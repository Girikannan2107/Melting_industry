from celery import Celery
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings
from ml_pipeline.engine import process_document

# Initialize Celery connected to Redis
celery_app = Celery(
    "idp_worker",
    broker=settings.REDIS_URI,
    backend=settings.REDIS_URI
)

async def save_results_to_db(task_id: str, data: dict):
    """Async helper to save JSON output to MongoDB."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    document_record = {
        "task_id": task_id,
        "status": "COMPLETED",
        "extracted_data": data
    }
    await db.processed_documents.insert_one(document_record)
    client.close()

@celery_app.task(bind=True, name="process_document")
def process_document_task(self, file_path: str):
    """
    The background task that runs the OCR pipeline.
    """
    try:
        # 1. Run the heavy ML Pipeline using the updated standalone function
        # We pass the GEMINI_API_KEY from settings directly to the function
        extracted_results = process_document(file_path, settings.GEMINI_API_KEY)
        
        # If the engine returned an error, raise it so Celery knows the task failed
        if extracted_results.get("status") == "error":
            raise Exception(extracted_results.get("message"))
            
        data_payload = extracted_results.get("data", {})
        
        # 2. Save to Database (running async Mongo in a sync Celery thread)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(save_results_to_db(self.request.id, data_payload))
        
        return {"status": "success", "data": data_payload}
        
    except Exception as e:
        # Log the error and fail the task gracefully
        return {"status": "error", "message": str(e)}