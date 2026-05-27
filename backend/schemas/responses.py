from pydantic import BaseModel
from typing import Optional, Any
from .document import StructuredDocument

class TaskResponse(BaseModel):
    message: str
    task_id: str
    filename: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[StructuredDocument] = None
    error: Optional[str] = None