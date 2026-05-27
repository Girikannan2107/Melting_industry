import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "IDP Production Engine"
    API_V1_STR: str = "/api/v1"
    GEMINI_API_KEY: str = ""
    
    # Storage Settings
    UPLOAD_DIR: str = "uploads"
    
    # MongoDB Settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "idp_production")
    
    # Celery / Redis Settings
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://localhost:6379/0")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)