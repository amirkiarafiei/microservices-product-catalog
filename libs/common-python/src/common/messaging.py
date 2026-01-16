import asyncio
import json
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


class RabbitMQConsumer:
    """
    Asynchronous RabbitMQ consumer for handling incoming events.
    """
    def __init__(self, amqp_url: str, queue_name: str, exchange_name: str, routing_key: str):
        self.amqp_url = amqp_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.connection = None
        self.channel = None
        self.stop_event = asyncio.Event()

    async def connect(self):
        """Establish connection and setup topology."""
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
            
            # Declare queue
            queue = await self.channel.declare_queue(self.queue_name, durable=True)
            
            # Bind queue to exchange
            await queue.bind(exchange, routing_key=self.routing_key)
            
            logger.info(f"Consumer connected and bound to {self.routing_key}")
            return queue

    async def consume(self, callback):
        """
        Starts consuming messages. 
        'callback' should be an async function that takes (message_body, headers).
        """
        while not self.stop_event.is_set():
            try:
                queue = await self.connect()
                
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        if self.stop_event.is_set():
                            break
                            
                        async with message.process():
                            try:
                                body = json.loads(message.body.decode())
                                headers = message.headers
                                await callback(body, headers)
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                                # message.process() handles nack if exception is raised, 
                                # but we caught it. If we want requeue, we should raise or 
                                # use custom ack/nack logic. For now, we log and move on
                                # to prevent poison pills from blocking the queue.
                
            except Exception as e:
                if not self.stop_event.is_set():
                    logger.error(f"Consumer error: {str(e)}. Retrying in 5s...")
                    await asyncio.sleep(5)

    def stop(self):
        """Stop the consumer loop."""
        self.stop_event.set()

    async def close(self):
        """Close connection."""
        self.stop()
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ consumer connection")
