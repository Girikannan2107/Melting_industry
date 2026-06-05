from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from database.connection import db_client
from api.v1 import documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB at startup
    await db_client.connect()
    yield
    # Disconnect from MongoDB at shutdown
    db_client.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Allow React frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(
    documents.router, 
    prefix=settings.API_V1_STR, 
    tags=["Documents"]
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}