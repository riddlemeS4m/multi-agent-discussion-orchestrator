from pydantic import BaseModel
from typing import List, Dict, Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


class HistoryResponse(BaseModel):
    history: List[Dict[str, str]]
    session_id: str
