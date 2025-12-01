"""API v1 router aggregation"""
from fastapi import APIRouter
from api.v1.endpoints import health, sessions, agents, orchestration

api_router = APIRouter()

# Include all v1 endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(orchestration.router, prefix="/orchestration", tags=["Orchestration"])
