from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

class DatabaseClient:
    client: AsyncIOMotorClient = None

    async def connect(self):
        # Completely disconnected MongoDB for Stateless Deployment / Offline local JSON mode
        print("Stateless Deployment: MongoDB is disconnected. Using local JSON database fallback.")
        self.client = None

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

db_client = DatabaseClient()