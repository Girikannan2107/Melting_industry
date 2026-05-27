from database.connection import db_client
from core.config import settings

async def get_db():
    """Dependency to yield the active MongoDB instance."""
    return db_client.client[settings.DB_NAME]