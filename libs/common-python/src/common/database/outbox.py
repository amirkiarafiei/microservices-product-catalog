import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import asyncpg
from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from ..messaging import RabbitMQPublisher
from ..schemas import Event

logger = logging.getLogger(__name__)

OutboxBase = declarative_base()

class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class OutboxMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="PENDING", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

class OutboxListener:
    """
    Listens for Postgres NOTIFY and processes pending outbox messages.
    """
    def __init__(
        self,
        dsn: str,
        publisher: RabbitMQPublisher,
        outbox_model: Any, # The actual SQLAlchemy model class
        session_factory: Any # A callable that returns a new DB session
    ):
        self.dsn = dsn
        self.publisher = publisher
        self.outbox_model = outbox_model
        self.session_factory = session_factory
        self.stop_event = asyncio.Event()

    async def run(self):
        """Main loop for the listener."""
        while not self.stop_event.is_set():
            try:
                conn = await asyncpg.connect(self.dsn)
                await conn.add_listener('outbox_events', self._handle_notification)
                logger.info("Outbox listener started and waiting for notifications...")

                # Check for existing pending messages on startup
                await self._process_pending()

                while not self.stop_event.is_set():
                    # Keep the connection alive and poll occasionally
                    # as a fallback for missing notifications
                    await self._process_pending()
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Outbox listener error: {str(e)}. Retrying in 5s...")
                await asyncio.sleep(5)
            finally:
                if 'conn' in locals():
                    await conn.close()

    def _handle_notification(self, connection, pid, channel, payload):
        """Callback when a notification is received."""
        logger.debug(f"Received notification on {channel}: {payload}")
        # We don't necessarily need the ID from payload,
        # we can just trigger a process of all pending.
        asyncio.create_task(self._process_pending())

    async def _process_pending(self):
        """Fetches and processes all pending outbox records."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._process_pending_sync, loop)

    def _process_pending_sync(self, loop):
        session = self.session_factory()
        try:
            pending = session.query(self.outbox_model).filter(
                self.outbox_model.status == "PENDING"
            ).order_by(self.outbox_model.created_at.asc()).all()

            if pending:
                logger.info(f"Found {len(pending)} pending outbox records")

            for record in pending:
                try:
                    # Construct Event object from payload
                    payload_dict = record.payload
                    event = Event(**payload_dict)

                    # Publish to RabbitMQ (Wait for it)
                    # We use run_coroutine_threadsafe with the provided loop
                    future = asyncio.run_coroutine_threadsafe(
                        self.publisher.publish(record.topic, event),
                        loop
                    )
                    future.result() # Wait for completion

                    record.status = "SENT"
                    record.processed_at = datetime.now(timezone.utc)
                    logger.debug(f"Successfully processed outbox record {record.id}")
                except Exception as e:
                    logger.error(f"Failed to process outbox record {record.id}: {str(e)}")
                    record.status = "FAILED"
                    record.error_message = str(e)

                session.commit()
        except Exception as e:
            logger.error(f"Error in _process_pending_sync: {str(e)}")
        finally:
            session.close()

    def stop(self):
        self.stop_event.set()
