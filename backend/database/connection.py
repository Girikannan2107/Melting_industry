from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

class DatabaseClient:
    client: AsyncIOMotorClient = None

    def connect(self):
        try:
            # Increased timeout to 5000ms (5 seconds) to accommodate cloud clusters like MongoDB Atlas
            self.client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            
            # Send a ping to confirm a successful connection
            self.client.admin.command('ping')
            print(f"MongoDB client initialized successfully. Connected to cluster: {settings.DB_NAME}")
        except Exception as e:
            print(f"MongoDB initialization error: {e}")
            self.client = None

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

db_client = DatabaseClient()