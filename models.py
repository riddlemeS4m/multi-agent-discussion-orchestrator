from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    agent_type: Optional[str] = Field(
        default="junior_engineer",
        description="Type of agent to chat with"
    )


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_type: str


class HistoryResponse(BaseModel):
    history: List[Dict[str, str]]
    session_id: str
