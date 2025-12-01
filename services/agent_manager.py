"""Agent management service for handling agent instances and sessions"""
from typing import Dict, Optional
from agent import Agent
from constants import AGENT_CONFIGS


class AgentManager:
    """Manages agent instances across different sessions and roles"""
    
    
    
    def __init__(self):
        # Sessions are now keyed by "session_id:agent_type"
        self.agents: Dict[str, Agent] = {}
    
    def initialize_default_agents(self):
        """Initialize default agents for each type"""
        for agent_type in AGENT_CONFIGS.keys():
            session_key = f"default:{agent_type}"
            config = AGENT_CONFIGS[agent_type]
            self.agents[session_key] = Agent(
                role=config["role"],
                prompt_file=config["prompt_file"],
                model=config["model"]
            )
    
    def get_agent(
        self, 
        session_id: str, 
        agent_type: str = "junior_engineer"
    ) -> Agent:
        """Get an agent for a session and type, creating if necessary"""
        if agent_type not in AGENT_CONFIGS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        session_key = f"{session_id}:{agent_type}"
        
        if session_key not in self.agents:
            config = AGENT_CONFIGS[agent_type]
            self.agents[session_key] = Agent(
                role=config["role"],
                prompt_file=config["prompt_file"],
                model=config["model"]
            )
        
        return self.agents[session_key]
    
    def session_exists(self, session_id: str, agent_type: Optional[str] = None) -> bool:
        """Check if a session exists for a specific agent type or any type"""
        if agent_type:
            session_key = f"{session_id}:{agent_type}"
            return session_key in self.agents
        
        # Check if session exists for any agent type
        return any(
            key.startswith(f"{session_id}:") 
            for key in self.agents.keys()
        )
    
    def delete_session(
        self, 
        session_id: str, 
        agent_type: Optional[str] = None
    ) -> int:
        """
        Delete a session. If agent_type is specified, delete only that agent.
        Otherwise, delete all agents for the session.
        Returns the number of agents deleted.
        """
        deleted_count = 0
        
        if agent_type:
            # Delete specific agent type
            session_key = f"{session_id}:{agent_type}"
            if session_key in self.agents:
                del self.agents[session_key]
                deleted_count = 1
        else:
            # Delete all agents for this session
            keys_to_delete = [
                key for key in self.agents.keys() 
                if key.startswith(f"{session_id}:")
            ]
            for key in keys_to_delete:
                del self.agents[key]
                deleted_count += 1
        
        return deleted_count
    
    def get_all_sessions(self) -> Dict[str, list]:
        """Get all active sessions grouped by session_id"""
        sessions = {}
        for key in self.agents.keys():
            session_id, agent_type = key.split(":", 1)
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(agent_type)
        return sessions
    
    def get_available_agent_types(self) -> list:
        """Get list of available agent types"""
        return list(AGENT_CONFIGS.keys())


# Global instance
agent_manager = AgentManager()
