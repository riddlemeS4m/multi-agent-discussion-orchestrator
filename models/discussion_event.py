from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class DiscussionEvent:
    """Represents a single event in a discussion"""
    event_type: str  # "agent_response", "round_start", "discussion_complete", "error"
    timestamp: str
    data: Dict
    
    def to_dict(self):
        return asdict(self)
