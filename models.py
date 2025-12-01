from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from constants import OrchestrationMode


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


class StartOrchestrationRequest(BaseModel):
    session_id: str
    task: str
    agent_types: List[str] = Field(
        default=["junior_engineer", "product_manager"],
        description="List of agent types to include in the discussion"
    )
    mode: OrchestrationMode = Field(
        default=OrchestrationMode.ROUND_ROBIN,
        description="Orchestration mode (round_robin, sequential, or adaptive)"
    )
    rounds: Optional[int] = Field(
        default=2,
        description="Number of rounds (for round_robin mode) or max rounds (for adaptive mode)"
    )
    enable_project_manager: Optional[bool] = Field(
        default=False,
        description="If True, the Project Manager agent will use its LLM to craft contextual prompts for each agent"
    )


class OrchestrationResponse(BaseModel):
    session_id: str
    responses: List[Dict[str, str]]
    summary: Dict


class OrchestrationHistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, str]]
    summary: Dict
