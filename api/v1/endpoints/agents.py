"""Agents management endpoints"""
from fastapi import APIRouter
from services.agent_manager import agent_manager
from constants import AGENT_CONFIGS

router = APIRouter(tags=["Agents"])

@router.get("/")
async def get_available_agents():
    """Get list of available agent types"""
    return {
        "agent_types": agent_manager.get_available_agent_types(),
        "configs": {
            agent_type: {
                "role": config["role"],
                "model": config["model"]
            }
            for agent_type, config in AGENT_CONFIGS.items()
        }
    }
