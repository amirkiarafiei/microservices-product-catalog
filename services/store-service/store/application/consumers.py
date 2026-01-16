import asyncio
import logging
from typing import Any, Dict

from common.messaging import RabbitMQConsumer

from ..config import settings
from ..infrastructure.elasticsearch import es_client
from ..infrastructure.mongodb import mongodb_client
from .service import StoreService

logger = logging.getLogger(__name__)

class EventConsumerService:
    def __init__(self):
        self.store_service = StoreService(mongodb_client, es_client)
        self.consumers = []

    async def _handle_event(self, body: Dict[str, Any], headers: Dict[str, Any]):
        event_id = body.get("event_id")
        event_type = body.get("event_type")
        payload = body.get("payload", {})

        if not event_id or not event_type:
            logger.warning(f"Received malformed event: {body}")
            return

        # Idempotency check
        if await self.store_service.is_event_processed(event_id):
            logger.debug(f"Event {event_id} already processed, skipping.")
            return

        logger.info(f"Processing event {event_id} of type {event_type}")

        try:
            if event_type == "OfferingPublished":
                offering_id = payload.get("id")
                if offering_id:
                    await self.store_service.sync_offering(offering_id)

            elif event_type == "OfferingRetired":
                offering_id = payload.get("id")
                if offering_id:
                    await self.store_service.retire_offering(offering_id)

            elif event_type in ["CharacteristicUpdated", "CharacteristicDeleted"]:
                char_id = payload.get("id")
                if char_id:
                    affected = await self.store_service.find_affected_offerings("characteristic", char_id)
                    for off_id in affected:
                        await self.store_service.sync_offering(off_id)

            elif event_type in ["SpecificationUpdated", "SpecificationDeleted"]:
                spec_id = payload.get("id")
                if spec_id:
                    affected = await self.store_service.find_affected_offerings("specification", spec_id)
                    for off_id in affected:
                        await self.store_service.sync_offering(off_id)

            elif event_type in ["PriceUpdated", "PriceDeleted"]:
                price_id = payload.get("id")
                if price_id:
                    affected = await self.store_service.find_affected_offerings("price", price_id)
                    for off_id in affected:
                        await self.store_service.sync_offering(off_id)

            # Mark processed
            await self.store_service.mark_event_processed(event_id)

        except Exception as e:
            logger.error(f"Error handling event {event_id}: {str(e)}")

    async def start(self):
        # Topics to subscribe to
        topics = [
            "resource.characteristics.events",
            "resource.specifications.events",
            "commercial.pricing.events",
            "product.offering.events"
        ]

        for topic in topics:
            consumer = RabbitMQConsumer(
                amqp_url=settings.RABBITMQ_URL,
                queue_name=f"store-service.{topic}.queue",
                exchange_name="catalog.events",
                routing_key=topic
            )
            self.consumers.append(consumer)
            # Each consumer runs in its own task
            asyncio.create_task(consumer.consume(self._handle_event))
            logger.info(f"Started consumer for topic: {topic}")

    async def stop(self):
        for consumer in self.consumers:
            consumer.stop()
            await consumer.close()
