"""Orchestration service for multi-agent conversations"""
from typing import List, Dict, Optional, Callable, Awaitable
from orchestrator import Orchestrator
from constants import OrchestrationMode

class OrchestratorManager:
    """Manages orchestrator instances across sessions"""
    
    def __init__(self):
        self.orchestrators: Dict[str, Orchestrator] = {}
    
    def create_orchestrator(
        self,
        session_id: str,
        agent_types: List[str],
        mode: OrchestrationMode = OrchestrationMode.ROUND_ROBIN,
        event_callback: Optional[Callable[[str, Dict], Awaitable[None]]] = None
    ) -> Orchestrator:
        """Create a new orchestrator"""
        orchestrator = Orchestrator(
            session_id=session_id,
            agent_types=agent_types,
            mode=mode,
            event_callback=event_callback
        )
        self.orchestrators[session_id] = orchestrator
        return orchestrator
    
    def get_orchestrator(self, session_id: str) -> Optional[Orchestrator]:
        """Get an existing orchestrator"""
        return self.orchestrators.get(session_id)
    
    def delete_orchestrator(self, session_id: str) -> bool:
        """Delete an orchestrator session"""
        if session_id in self.orchestrators:
            del self.orchestrators[session_id]
            return True
        return False
    
    def get_all_sessions(self) -> List[str]:
        """Get all orchestrator session IDs"""
        return list(self.orchestrators.keys())


# Global instance
orchestrator_manager = OrchestratorManager()
