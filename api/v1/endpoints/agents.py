"""Agents management endpoints"""
from fastapi import APIRouter
from services.agent_manager import agent_manager

router = APIRouter(tags=["Agents"])

@router.get("/agents")
async def get_available_agents():
    """Get list of available agent types"""
    return {
        "agent_types": agent_manager.get_available_agent_types(),
        "configs": {
            agent_type: {
                "role": config["role"],
                "model": config["model"]
            }
            for agent_type, config in agent_manager.AGENT_CONFIGS.items()
        }
    }
