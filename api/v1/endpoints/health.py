"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Multi-Agent Discussion Orchestrator API is running",
    }

