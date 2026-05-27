from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ExtractedText(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[List[int]]] = None

class StructuredDocument(BaseModel):
    document_info: Dict[str, Any]
    pouring_details: Dict[str, Any]
    tables: List[Any]
    raw_notes: List[Dict[str, Any]]