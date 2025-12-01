"""API v1 router aggregation"""
from fastapi import APIRouter
from api.v1.endpoints import health, sessions, agents

api_router = APIRouter()

# Include all v1 endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(sessions.router, tags=["Sessions"])
api_router.include_router(agents.router, tags=["Agents"])
