"""
RabbitMQ Messaging with OpenTelemetry Trace Context Propagation.

Provides async publisher and consumer with automatic B3 trace header injection/extraction.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import aio_pika
from opentelemetry import context, trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind

from .schemas import Event

logger = logging.getLogger(__name__)


class DictCarrier(dict):
    """
    Carrier for OpenTelemetry context propagation via message headers.
    """

    pass


def inject_trace_context(headers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject current trace context into message headers.

    Args:
        headers: Existing headers dict to inject into.

    Returns:
        Headers with B3 trace context added.
    """
    carrier = DictCarrier(headers)
    inject(carrier)
    return dict(carrier)


def extract_trace_context(headers: Dict[str, Any]) -> context.Context:
    """
    Extract trace context from message headers.

    Args:
        headers: Message headers containing B3 trace context.

    Returns:
        OpenTelemetry context for span continuation.
    """
    return extract(headers or {})


class RabbitMQPublisher:
    """
    Asynchronous RabbitMQ publisher with retry logic and trace propagation.
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

        Automatically injects B3 trace context into message headers.

        Args:
            topic: Routing key / topic for the event.
            event: Event object to publish.
            retries: Number of retry attempts on failure.
        """
        tracer = trace.get_tracer(__name__)

        # Create a PRODUCER span for the publish operation
        with tracer.start_as_current_span(
            f"PUBLISH {topic}",
            kind=SpanKind.PRODUCER,
            attributes={
                "messaging.system": "rabbitmq",
                "messaging.destination": topic,
                "messaging.destination_kind": "topic",
                "messaging.message_id": str(event.event_id),
            },
        ):
            # Build headers with correlation_id and trace context
            headers: Dict[str, Any] = {}
            if event.correlation_id:
                headers["correlation_id"] = event.correlation_id

            # Inject B3 trace context into headers
            headers = inject_trace_context(headers)

            message_body = event.model_dump_json().encode()
            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers=headers,
            )

            attempt = 0
            while attempt < retries:
                try:
                    await self.connect()

                    # Ensure exchange exists
                    exchange = await self.channel.declare_exchange(
                        "catalog.events", aio_pika.ExchangeType.TOPIC, durable=True
                    )

                    await exchange.publish(message, routing_key=topic)
                    logger.debug(f"Published event {event.event_id} to {topic}")
                    return
                except Exception as e:
                    attempt += 1
                    wait_time = 2**attempt
                    logger.warning(
                        f"Failed to publish event (attempt {attempt}/{retries}): {e!s}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)

            raise RuntimeError(f"Could not publish event after {retries} attempts")

    async def close(self):
        """Close connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection")


class RabbitMQConsumer:
    """
    Asynchronous RabbitMQ consumer with trace context extraction.
    """

    def __init__(
        self, amqp_url: str, queue_name: str, exchange_name: str, routing_key: str
    ):
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

    async def consume(
        self,
        callback: Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Any],
    ):
        """
        Starts consuming messages with automatic trace context extraction.

        'callback' should be an async function that takes (message_body, headers).
        A new span is created for each consumed message, linked to the producer span.

        Args:
            callback: Async function to process each message.
        """
        tracer = trace.get_tracer(__name__)

        while not self.stop_event.is_set():
            try:
                queue = await self.connect()

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        if self.stop_event.is_set():
                            break

                        async with message.process():
                            try:
                                # Extract trace context from message headers
                                headers = dict(message.headers) if message.headers else {}
                                ctx = extract_trace_context(headers)

                                # Create CONSUMER span linked to producer
                                with tracer.start_as_current_span(
                                    f"CONSUME {self.queue_name}",
                                    context=ctx,
                                    kind=SpanKind.CONSUMER,
                                    attributes={
                                        "messaging.system": "rabbitmq",
                                        "messaging.source": self.queue_name,
                                        "messaging.operation": "receive",
                                    },
                                ):
                                    body = json.loads(message.body.decode())
                                    await callback(body, headers)

                            except Exception as e:
                                logger.error(f"Error processing message: {e!s}")
                                # Log and continue to prevent poison pills

            except Exception as e:
                if not self.stop_event.is_set():
                    logger.error(f"Consumer error: {e!s}. Retrying in 5s...")
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
