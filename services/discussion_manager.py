"""Manage orchestration discussion state and events"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import asyncio
from collections import defaultdict
from constants import DiscussionStatus
from models.discussion_state import DiscussionState
from models.discussion_event import DiscussionEvent


class DiscussionManager:
    """Manages discussion states and event broadcasting"""
    
    def __init__(self):
        self.discussions: Dict[str, DiscussionState] = {}
        # WebSocket connections per discussion_id
        self.subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
    
    def create_discussion(
        self,
        discussion_id: str,
        session_id: str,
        task: str,
        agent_types: List[str],
        mode: str
    ) -> DiscussionState:
        """Create a new discussion state"""
        state = DiscussionState(
            discussion_id=discussion_id,
            session_id=session_id,
            task=task,
            agent_types=agent_types,
            mode=mode,
            status=DiscussionStatus.PENDING,
            created_at=datetime.utcnow().isoformat()
        )
        self.discussions[discussion_id] = state
        return state
    
    def get_discussion(self, discussion_id: str) -> Optional[DiscussionState]:
        """Get a discussion by ID"""
        return self.discussions.get(discussion_id)
    
    def update_status(
        self,
        discussion_id: str,
        status: DiscussionStatus,
        error: Optional[str] = None
    ):
        """Update discussion status"""
        discussion = self.discussions.get(discussion_id)
        if discussion:
            discussion.status = status
            if status == DiscussionStatus.RUNNING and not discussion.started_at:
                discussion.started_at = datetime.utcnow().isoformat()
            elif status in [DiscussionStatus.COMPLETED, DiscussionStatus.FAILED]:
                discussion.completed_at = datetime.utcnow().isoformat()
            if error:
                discussion.error = error
    
    async def broadcast_event(self, discussion_id: str, event: DiscussionEvent):
        """Broadcast an event to all subscribers of a discussion"""
        if discussion_id in self.subscribers:
            # Send to all connected clients
            for queue in self.subscribers[discussion_id]:
                await queue.put(event)
    
    def subscribe(self, discussion_id: str) -> asyncio.Queue:
        """Subscribe to a discussion's events"""
        queue = asyncio.Queue()
        self.subscribers[discussion_id].append(queue)
        return queue
    
    def unsubscribe(self, discussion_id: str, queue: asyncio.Queue):
        """Unsubscribe from a discussion"""
        if discussion_id in self.subscribers:
            try:
                self.subscribers[discussion_id].remove(queue)
            except ValueError:
                pass
            
            # Clean up empty subscriber lists
            if not self.subscribers[discussion_id]:
                del self.subscribers[discussion_id]
    
    def get_all_discussions(self) -> List[Dict]:
        """Get all discussions"""
        return [d.to_dict() for d in self.discussions.values()]


# Global instance
discussion_manager = DiscussionManager()
