"""Multi-agent discussion endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from services.agent_manager import agent_manager
from services.orchestrator_manager import orchestrator_manager
from models import StartOrchestrationRequest, OrchestrationResponse, OrchestrationHistoryResponse


router = APIRouter(tags=["Discussions"])


@router.post("/", response_model=OrchestrationResponse)
async def start_discussion(request: StartOrchestrationRequest):
    """
    Start a multi-agent discussion
    
    - **session_id**: Unique identifier for this discussion session
    - **task**: The task/problem for agents to discuss
    - **agent_types**: List of agent types to include
    - **mode**: Discussion mode (round_robin or sequential)
    - **rounds**: Number of rounds for round_robin mode
    """
    # Validate agent types
    available_agents = agent_manager.get_available_agent_types()
    for agent_type in request.agent_types:
        if agent_type not in available_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {agent_type}"
            )
    
    if len(request.agent_types) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 agent types for a discussion"
        )
    
    try:
        # Create orchestrator
        orchestrator = orchestrator_manager.create_orchestrator(
            session_id=request.session_id,
            agent_types=request.agent_types,
            mode=request.mode
        )
        
        # Add initial task
        orchestrator.add_initial_task(request.task)
        
        # Run discussion
        responses = orchestrator.run_discussion(rounds=request.rounds)
        
        return OrchestrationResponse(
            session_id=request.session_id,
            responses=responses,
            summary=orchestrator.get_summary()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history", response_model=OrchestrationHistoryResponse)
async def get_discussion_history(session_id: str):
    """Get the full conversation history for a discussion session"""
    orchestrator = orchestrator_manager.get_orchestrator(session_id)
    
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion session not found: {session_id}"
        )
    
    return OrchestrationHistoryResponse(
        session_id=session_id,
        history=orchestrator.get_conversation_history(),
        summary=orchestrator.get_summary()
    )


@router.post("/{session_id}/continue", response_model=OrchestrationResponse)
async def continue_discussion(
    session_id: str,
    rounds: Optional[int] = 1
):
    """Continue an existing discussion session for additional rounds"""
    orchestrator = orchestrator_manager.get_orchestrator(session_id)
    
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion session not found: {session_id}"
        )
    
    try:
        responses = orchestrator.run_discussion(rounds=rounds)
        
        return OrchestrationResponse(
            session_id=session_id,
            responses=responses,
            summary=orchestrator.get_summary()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_discussion(session_id: str):
    """Delete a discussion session"""
    deleted = orchestrator_manager.delete_orchestrator(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion session not found: {session_id}"
        )
    
    return {
        "status": "success",
        "message": f"Discussion session deleted: {session_id}"
    }


@router.get("/")
async def get_all_discussions():
    """Get all active discussion sessions"""
    return {
        "sessions": orchestrator_manager.get_all_sessions()
    }

