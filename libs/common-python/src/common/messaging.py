import asyncio
import logging

import aio_pika

from .schemas import Event

logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    """
    Asynchronous RabbitMQ publisher with retry logic.
    """
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection = None
        self.channel = None

    async def connect(self):
        """Establish connection to RabbitMQ."""
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ")

    async def publish(self, topic: str, event: Event, retries: int = 3):
        """
        Publishes an event to a specific topic exchange.
        """
        await self.connect()

        # Ensure exchange exists
        exchange = await self.channel.declare_exchange(
            "catalog.events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        message_body = event.model_dump_json().encode()
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={"correlation_id": event.correlation_id} if event.correlation_id else {}
        )

        attempt = 0
        while attempt < retries:
            try:
                await exchange.publish(message, routing_key=topic)
                logger.debug(f"Published event {event.event_id} to {topic}")
                return
            except Exception as e:
                attempt += 1
                wait_time = 2 ** attempt
                logger.warning(f"Failed to publish event (attempt {attempt}/{retries}): {str(e)}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        raise RuntimeError(f"Could not publish event after {retries} attempts")

    async def close(self):
        """Close connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection")
