import logging

from motor.motor_asyncio import AsyncIOMotorClient

from ..config import settings

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.offerings = self.db["published_offerings"]
        self.events = self.db["processed_events"]

    async def close(self):
        self.client.close()

mongodb_client = MongoDBClient()

def get_mongodb():
    return mongodb_client
