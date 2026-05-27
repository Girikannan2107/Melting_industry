from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

class DatabaseClient:
    client: AsyncIOMotorClient = None

    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)

    def disconnect(self):
        if self.client:
            self.client.close()

db_client = DatabaseClient()