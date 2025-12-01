"""Agent management service for handling agent instances and sessions"""
from typing import Dict
from agent import Agent


class AgentManager:
    """Manages agent instances across different sessions"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    def initialize_default_agent(self):
        """Initialize the default agent"""
        self.agents["default"] = Agent(
            role="Junior Engineer",
            prompt_file="junior_engineer.md",
            model="gpt-4o-mini"
        )
    
    def get_agent(self, session_id: str) -> Agent:
        """Get an agent for a session, creating if necessary"""
        if session_id not in self.agents:
            self.agents[session_id] = Agent(
                role="Junior Engineer",
                prompt_file="junior_engineer.md",
                model="gpt-4o-mini"
            )
        return self.agents[session_id]
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        return session_id in self.agents
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session, returns True if deleted, False if not found"""
        if session_id in self.agents:
            del self.agents[session_id]
            return True
        return False
    
    def get_all_sessions(self) -> list:
        """Get list of all active session IDs"""
        return list(self.agents.keys())


# Global instance
agent_manager = AgentManager()
