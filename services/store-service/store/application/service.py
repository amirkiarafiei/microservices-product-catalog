import logging
from typing import Any, Dict, List

import httpx

from ..config import settings
from ..infrastructure.elasticsearch import ElasticsearchClient
from ..infrastructure.mongodb import MongoDBClient

logger = logging.getLogger(__name__)

class StoreService:
    def __init__(self, mongodb: MongoDBClient, es: ElasticsearchClient):
        self.mongodb = mongodb
        self.es = es

    async def is_event_processed(self, event_id: str) -> bool:
        doc = await self.mongodb.events.find_one({"event_id": event_id})
        return doc is not None

    async def mark_event_processed(self, event_id: str):
        await self.mongodb.events.insert_one({"event_id": event_id})

    async def fetch_offering_details(self, offering_id: str) -> Dict[str, Any]:
        """
        Data Composition: Fetch full details from Specification, Pricing, and Characteristic services.
        """
        async with httpx.AsyncClient() as client:
            # 1. Fetch Offering from Offering Service
            offering_resp = await client.get(f"{settings.OFFERING_SERVICE_URL}/api/v1/offerings/{offering_id}")
            if offering_resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch offering {offering_id}")
            offering = offering_resp.json()

            # 2. Fetch Specifications
            specs = []
            for spec_id in offering.get("specification_ids", []):
                spec_resp = await client.get(f"{settings.SPECIFICATION_SERVICE_URL}/api/v1/specifications/{spec_id}")
                if spec_resp.status_code == 200:
                    spec_data = spec_resp.json()

                    # Fetch Characteristics for each spec
                    # Note: specification-service returns IDs, we need values.
                    # Actually, spec-service might return expanded chars if implemented that way,
                    # but characteristic-service has the latest.
                    # For this phase, we fetch expanded specs or fetch chars manually.
                    # Looking at specifications-service/src/main.py (if I could),
                    # but let's assume we need to fetch char details.

                    chars = []
                    for char_id in spec_data.get("characteristic_ids", []):
                        char_resp = await client.get(f"{settings.CHARACTERISTIC_SERVICE_URL}/api/v1/characteristics/{char_id}")
                        if char_resp.status_code == 200:
                            chars.append(char_resp.json())

                    spec_data["characteristics"] = chars
                    specs.append(spec_data)

            # 3. Fetch Prices
            prices = []
            for price_id in offering.get("pricing_ids", []):
                price_resp = await client.get(f"{settings.PRICING_SERVICE_URL}/api/v1/prices/{price_id}")
                if price_resp.status_code == 200:
                    prices.append(price_resp.json())

            # Compose full document
            full_doc = {
                "id": str(offering["id"]),
                "name": offering["name"],
                "description": offering.get("description"),
                "lifecycle_status": offering["lifecycle_status"],
                "published_at": offering.get("published_at"),
                "sales_channels": offering.get("sales_channels", []),
                "specifications": specs,
                "pricing": prices
            }
            return full_doc

    async def sync_offering(self, offering_id: str):
        """
        Syncs a single offering to MongoDB and Elasticsearch.
        """
        try:
            full_doc = await self.fetch_offering_details(offering_id)

            # Upsert in MongoDB
            await self.mongodb.offerings.replace_one(
                {"id": offering_id}, full_doc, upsert=True
            )

            # Index in Elasticsearch
            # Convert decimal values to float for ES if necessary
            es_doc = full_doc.copy()
            for p in es_doc.get("pricing", []):
                if "value" in p:
                    p["value"] = float(p["value"])

            await self.es.index_offering(offering_id, es_doc)
            logger.info(f"Synced offering {offering_id}")
        except Exception as e:
            logger.error(f"Failed to sync offering {offering_id}: {str(e)}")

    async def retire_offering(self, offering_id: str):
        """
        Removes an offering from MongoDB and Elasticsearch.
        """
        await self.mongodb.offerings.delete_one({"id": offering_id})
        await self.es.delete_offering(offering_id)
        logger.info(f"Retired offering {offering_id}")

    async def find_affected_offerings(self, entity_type: str, entity_id: str) -> List[str]:
        """
        Finds offerings affected by an update to a characteristic, spec, or price.
        """
        if entity_type == "characteristic":
            # Find specs containing this char
            # This is complex because specs are nested.
            # In MongoDB, we can query nested arrays.
            cursor = self.mongodb.offerings.find(
                {"specifications.characteristics.id": entity_id},
                {"id": 1}
            )
        elif entity_type == "specification":
            cursor = self.mongodb.offerings.find(
                {"specifications.id": entity_id},
                {"id": 1}
            )
        elif entity_type == "price":
            cursor = self.mongodb.offerings.find(
                {"pricing.id": entity_id},
                {"id": 1}
            )
        else:
            return []

        offering_ids = []
        async for doc in cursor:
            offering_ids.append(doc["id"])
        return offering_ids
