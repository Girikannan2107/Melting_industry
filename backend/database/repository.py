from typing import Dict, Any

class DocumentRepository:
    def __init__(self, db):
        self.collection = db.processed_documents

    async def save_document(self, task_id: str, data: Dict[str, Any]):
        record = {
            "task_id": task_id, 
            "status": "COMPLETED", 
            "extracted_data": data
        }
        await self.collection.update_one(
            {"task_id": task_id}, 
            {"$set": record}, 
            upsert=True
        )

    async def get_document(self, task_id: str):
        return await self.collection.find_one({"task_id": task_id}, {"_id": 0})