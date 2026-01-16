import logging
import asyncio
from typing import Any, Dict

from common.messaging import RabbitMQConsumer

from ..config import settings
from ..infrastructure.models import CachedCharacteristicORM

logger = logging.getLogger(__name__)

class CharacteristicConsumer:
    """
    Consumer for characteristic events to sync the local cache.
    """
    def __init__(self):
        self.consumer = RabbitMQConsumer(
            amqp_url=settings.RABBITMQ_URL,
            queue_name="specification-service.characteristic-sync.queue",
            exchange_name="catalog.events",
            routing_key="resource.characteristics.events"
        )

    async def run(self):
        """Starts the consumer."""
        await self.consumer.consume(self._handle_event)

    async def _handle_event(self, body: Dict[str, Any], headers: Dict[str, Any]):
        """Callback for handling incoming events."""
        event_type = body.get("event_type")
        payload = body.get("payload", {})
        
        logger.info(f"Received event {event_type} for characteristic {payload.get('id')}")
        
        # We use a synchronous session in a thread pool to avoid blocking the async consumer
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._process_event_sync, event_type, payload)

    def _process_event_sync(self, event_type: str, payload: Dict[str, Any]):
        from ..infrastructure.database import SessionLocal
        if SessionLocal is None:
            logger.error("SessionLocal is not initialized. Check DATABASE_URL.")
            return
        db = SessionLocal()
        try:
            char_id = payload.get("id")
            if not char_id:
                logger.error("Event payload missing 'id'")
                return

            if event_type in ["CharacteristicCreated", "CharacteristicUpdated"]:
                # Upsert
                existing = db.query(CachedCharacteristicORM).filter(
                    CachedCharacteristicORM.id == char_id
                ).first()
                
                if existing:
                    existing.name = payload.get("name")
                else:
                    db.add(CachedCharacteristicORM(
                        id=char_id,
                        name=payload.get("name")
                    ))
                
            elif event_type == "CharacteristicDeleted":
                db.query(CachedCharacteristicORM).filter(
                    CachedCharacteristicORM.id == char_id
                ).delete()
            
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return

            db.commit()
            logger.debug(f"Successfully processed {event_type} for {char_id}")
        except Exception as e:
            logger.error(f"Error syncing characteristic cache: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def stop(self):
        self.consumer.stop()
