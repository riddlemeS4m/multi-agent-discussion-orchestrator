from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
from constants import DiscussionStatus
from models.discussion_event import DiscussionEvent


@dataclass
class DiscussionState:
    """Tracks the state of an orchestrated discussion"""
    discussion_id: str
    session_id: str
    task: str
    agent_types: List[str]
    mode: str
    status: DiscussionStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    events: List[DiscussionEvent] = field(default_factory=list)
    error: Optional[str] = None
    
    def add_event(self, event_type: str, data: Dict):
        """Add an event to the discussion"""
        event = DiscussionEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            data=data
        )
        self.events.append(event)
        return event
    
    def to_dict(self):
        return {
            **asdict(self),
            "events": [event.to_dict() for event in self.events]
        }
