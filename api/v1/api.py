"""API v1 router aggregation"""
from fastapi import APIRouter
from api.v1.endpoints import health, chats, agents, discussions

api_router = APIRouter()

# Include all v1 endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(chats.router, prefix="/chats", tags=["Chats"])
api_router.include_router(discussions.router, prefix="/discussions", tags=["Discussions"])
