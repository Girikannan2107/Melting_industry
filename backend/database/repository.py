from typing import Dict, Any, List
import json
import os
import aiofiles

class DocumentRepository:
    def __init__(self, db):
        self.collection = db.processed_documents if db is not None else None

    async def save_document(self, task_id: str, data: Dict[str, Any]):
        record = {
            "task_id": task_id, 
            "status": "COMPLETED", 
            "extracted_data": data
        }
        
        if self.collection is None:
            print("MongoDB not available, saving to local JSON fallback...")
            await self._save_to_local_fallback(record)
            return
            
        try:
            await self.collection.update_one(
                {"task_id": task_id}, 
                {"$set": record}, 
                upsert=True
            )
            print("Successfully saved processed document to MongoDB.")
        except Exception as e:
            print(f"MongoDB write failed: {e}. Falling back to local JSON...")
            await self._save_to_local_fallback(record)

    async def _save_to_local_fallback(self, record: Dict[str, Any]):
        fallback_path = os.path.join("uploads", "fallback_db.json")
        try:
            records = []
            if os.path.exists(fallback_path):
                async with aiofiles.open(fallback_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():
                        records = json.loads(content)
            
            # Remove existing record with same task_id if exists, then append
            records = [r for r in records if r.get("task_id") != record["task_id"]]
            records.append(record)
            
            async with aiofiles.open(fallback_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(records, indent=4))
            print(f"Successfully saved document to local fallback: {fallback_path}")
        except Exception as e:
            print(f"Local fallback write failed: {e}")
            raise e

    async def get_document(self, task_id: str) -> Dict[str, Any]:
        if self.collection is None:
            return await self._get_from_local_fallback(task_id)
            
        try:
            result = await self.collection.find_one({"task_id": task_id}, {"_id": 0})
            if result is None:
                return await self._get_from_local_fallback(task_id)
            return result
        except Exception as e:
            print(f"MongoDB fetch failed: {e}. Checking local fallback...")
            return await self._get_from_local_fallback(task_id)

    async def _get_from_local_fallback(self, task_id: str) -> Dict[str, Any]:
        fallback_path = os.path.join("uploads", "fallback_db.json")
        if not os.path.exists(fallback_path):
            return None
        try:
            async with aiofiles.open(fallback_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if content.strip():
                    records = json.loads(content)
                    for r in records:
                        if r.get("task_id") == task_id:
                            return r
        except Exception as e:
            print(f"Local fallback fetch failed: {e}")
        return None

    async def get_all_documents(self) -> List[Dict[str, Any]]:
        db_records = []
        if self.collection is not None:
            try:
                cursor = self.collection.find({}, {"_id": 0})
                db_records = await cursor.to_list(length=1000)
            except Exception as e:
                print(f"MongoDB fetch all failed: {e}")
        
        fallback_records = await self._get_all_from_local_fallback()
        
        # Merge records by task_id to avoid duplicates
        merged = {}
        for r in fallback_records:
            if "task_id" in r:
                merged[r["task_id"]] = r
        for r in db_records:
            if "task_id" in r:
                merged[r["task_id"]] = r
                
        return list(merged.values())

    async def _get_all_from_local_fallback(self) -> List[Dict[str, Any]]:
        fallback_path = os.path.join("uploads", "fallback_db.json")
        if not os.path.exists(fallback_path):
            return []
        try:
            async with aiofiles.open(fallback_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if content.strip():
                    return json.loads(content)
        except Exception as e:
            print(f"Local fallback fetch all failed: {e}")
        return []