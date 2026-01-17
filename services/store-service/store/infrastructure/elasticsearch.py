import logging

from elasticsearch import AsyncElasticsearch

from ..config import settings

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    def __init__(self):
        self.client = AsyncElasticsearch(settings.ELASTICSEARCH_URL)
        self.index = settings.ELASTICSEARCH_INDEX

    async def init_index(self):
        """
        Initializes the index with mapping if it doesn't exist.
        """
        exists = await self.client.indices.exists(index=self.index)
        if not exists:
            mapping = {
                "mappings": {
                    "properties": {
                        "name": {"type": "text"},
                        "description": {"type": "text"},
                        "lifecycle_status": {"type": "keyword"},
                        "published_at": {"type": "date"},
                        "sales_channels": {"type": "keyword"},
                        "specifications": {
                            "type": "nested",
                            "properties": {
                                "id": {"type": "keyword"},
                                "name": {"type": "text"},
                                "characteristics": {
                                    "type": "nested",
                                    "properties": {
                                        "name": {"type": "keyword"},
                                        "value": {"type": "keyword"},
                                        "unit_of_measure": {"type": "keyword"}
                                    }
                                }
                            }
                        },
                        "pricing": {
                            "type": "nested",
                            "properties": {
                                "id": {"type": "keyword"},
                                "name": {"type": "text"},
                                "value": {"type": "double"},
                                "currency": {"type": "keyword"},
                                "unit": {"type": "keyword"}
                            }
                        }
                    }
                }
            }
            await self.client.indices.create(index=self.index, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index}")

    async def index_offering(self, offering_id: str, document: dict):
        await self.client.index(index=self.index, id=offering_id, body=document, refresh=True)

    async def delete_offering(self, offering_id: str):
        await self.client.delete(index=self.index, id=offering_id, ignore=[404], refresh=True)

    async def search_offerings(self, query_body: dict, from_: int = 0, size: int = 10):
        return await self.client.search(
            index=self.index,
            body=query_body,
            from_=from_,
            size=size
        )

    async def close(self):
        await self.client.close()

es_client = ElasticsearchClient()

def get_elasticsearch():
    return es_client
