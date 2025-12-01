"""LangSmith configuration and tracing utilities"""

import os
from typing import Optional, Dict, Any
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LangSmithConfig:
    """Configuration for LangSmith tracing"""
    
    def __init__(self):
        self.enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project = os.getenv("LANGCHAIN_PROJECT", "multi-agent-orchestrator")
        self.endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled"""
        return self.enabled and bool(self.api_key)
    
    def get_status(self) -> Dict[str, Any]:
        """Get configuration status"""
        return {
            "enabled": self.enabled,
            "api_key_set": bool(self.api_key),
            "project": self.project,
            "endpoint": self.endpoint
        }


# Global configuration instance
langsmith_config = LangSmithConfig()


def get_langsmith_metadata(
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    agent_role: Optional[str] = None,
    orchestration_mode: Optional[str] = None,
    round_num: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate standardized metadata for LangSmith traces
    
    Args:
        session_id: The session/discussion ID
        agent_type: Type of agent (e.g., "product_manager")
        agent_role: Human-readable role (e.g., "Product Manager")
        orchestration_mode: Mode of orchestration (e.g., "round_robin", "adaptive")
        round_num: Round number in multi-round discussions
        **kwargs: Additional custom metadata
    
    Returns:
        Dictionary of metadata for LangSmith
    """
    metadata = {}
    
    if session_id:
        metadata["session_id"] = session_id
    if agent_type:
        metadata["agent_type"] = agent_type
    if agent_role:
        metadata["agent_role"] = agent_role
    if orchestration_mode:
        metadata["orchestration_mode"] = orchestration_mode
    if round_num is not None:
        metadata["round"] = round_num
    
    # Add any additional metadata
    metadata.update(kwargs)
    
    return metadata


def get_run_name(
    base_name: str,
    agent_role: Optional[str] = None,
    round_num: Optional[int] = None,
    **kwargs
) -> str:
    """
    Generate a descriptive run name for LangSmith traces
    
    Args:
        base_name: Base name for the run (e.g., "agent_chat", "orchestrator_decision")
        agent_role: Agent role to include in name
        round_num: Round number to include in name
        **kwargs: Additional identifiers
    
    Returns:
        Formatted run name
    """
    parts = [base_name]
    
    if agent_role:
        parts.append(f"[{agent_role}]")
    if round_num is not None:
        parts.append(f"Round-{round_num}")
    
    # Add any additional identifiers
    for key, value in kwargs.items():
        if value:
            parts.append(f"{key}:{value}")
    
    return " ".join(parts)

