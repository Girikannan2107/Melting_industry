import os
from pydantic_settings import BaseSettings

# Calculate the path to the root .env file (three levels up from backend/core/config.py)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(ROOT_DIR, ".env")

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "IDP Production Engine"
    API_V1_STR: str = "/api/v1"
    GEMINI_API_KEY: str = ""
    
    # Storage Settings
    UPLOAD_DIR: str = "uploads"
    
    # MongoDB Settings
    MONGO_URI: str = "mongodb+srv://madhurithika:Madhu222@cluster0.9ienqct.mongodb.net/?retryWrites=true&w=majority"
    DB_NAME: str = os.getenv("DB_NAME", "idp_production")
    
    # Celery / Redis Settings
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://localhost:6379/0")
    
    class Config:
        env_file = ENV_PATH
        case_sensitive = True

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)