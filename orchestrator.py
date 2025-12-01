from typing import List, Dict
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from agent import Agent
from services.agent_manager import agent_manager
from constants import OrchestrationMode


class Orchestrator:
    """Manages multi-agent conversations"""
    
    def __init__(
        self,
        session_id: str,
        agent_types: List[str],
        mode: OrchestrationMode = OrchestrationMode.ROUND_ROBIN
    ):
        self.session_id = session_id
        self.agent_types = agent_types
        self.mode = mode
        
        # Shared conversation history across all agents
        self.conversation_history: List = []
        
        # Get agent instances
        self.agents: Dict[str, Agent] = {
            agent_type: agent_manager.get_agent(session_id, agent_type)
            for agent_type in agent_types
        }
        
        # Track current turn for round-robin
        self.current_turn = 0
    
    def add_initial_task(self, task: str):
        """Add the initial task/prompt to conversation history"""
        self.conversation_history.append(
            HumanMessage(content=f"[TASK] {task}")
        )
    
    def run_round_robin(self, rounds: int = 2) -> List[Dict[str, str]]:
        """
        Run a round-robin discussion where each agent speaks in order
        
        Returns list of responses with metadata
        """
        responses = []
        
        for round_num in range(rounds):
            for agent_type in self.agent_types:
                agent = self.agents[agent_type]
                
                # Agent responds based on full conversation history
                response = agent.chat_with_history(
                    message=f"Round {round_num + 1}: Share your perspective on this task.",
                    history=self.conversation_history
                )
                
                # Add to shared history with role label
                message = AIMessage(content=f"[{agent.role}]: {response}")
                self.conversation_history.append(message)
                
                # Track response
                responses.append({
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": str(round_num + 1),
                    "response": response
                })
        
        return responses
    
    def run_sequential(self) -> List[Dict[str, str]]:
        """
        Run a sequential discussion where each agent speaks once in order
        Each agent sees all previous responses
        """
        responses = []
        
        for agent_type in self.agent_types:
            agent = self.agents[agent_type]
            
            # Agent responds based on everything said so far
            response = agent.chat_with_history(
                message="Share your perspective on this task.",
                history=self.conversation_history
            )
            
            # Add to shared history
            message = AIMessage(content=f"[{agent.role}]: {response}")
            self.conversation_history.append(message)
            
            responses.append({
                "agent_type": agent_type,
                "role": agent.role,
                "response": response
            })
        
        return responses
    
    def run_discussion(self, rounds: int = 2) -> List[Dict[str, str]]:
        """
        Run a discussion based on the orchestration mode
        """
        if self.mode == OrchestrationMode.ROUND_ROBIN:
            return self.run_round_robin(rounds)
        elif self.mode == OrchestrationMode.SEQUENTIAL:
            return self.run_sequential()
        else:
            raise ValueError(f"Unknown orchestration mode: {self.mode}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history in a serializable format"""
        history = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                history.append({"role": "system", "content": msg.content})
        return history
    
    def get_summary(self) -> Dict:
        """Get a summary of the orchestration session"""
        return {
            "session_id": self.session_id,
            "agent_types": self.agent_types,
            "mode": self.mode,
            "total_messages": len(self.conversation_history),
            "agents": [
                {"type": agent_type, "role": agent.role}
                for agent_type, agent in self.agents.items()
            ]
        }
