from fastapi import Request
from fastapi.responses import JSONResponse

class IDPProcessingError(Exception):
    def __init__(self, message: str, task_id: str = None):
        self.message = message
        self.task_id = task_id

async def idp_exception_handler(request: Request, exc: IDPProcessingError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Processing Pipeline Failed", 
            "message": exc.message, 
            "task_id": exc.task_id
        },
    )