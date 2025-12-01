"""Orchestration endpoints for multi-agent conversations"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from services.agent_manager import agent_manager
from services.orchestrator_manager import orchestrator_manager
from models import StartOrchestrationRequest, OrchestrationResponse, OrchestrationHistoryResponse


router = APIRouter(tags=["Orchestration"])


@router.post("/start", response_model=OrchestrationResponse)
async def start_orchestration(request: StartOrchestrationRequest):
    """
    Start a multi-agent orchestrated discussion
    
    - **session_id**: Unique identifier for this orchestration session
    - **task**: The task/problem for agents to discuss
    - **agent_types**: List of agent types to include
    - **mode**: Orchestration mode (round_robin or sequential)
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
            detail="Need at least 2 agent types for orchestration"
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


@router.get("/history/{session_id}", response_model=OrchestrationHistoryResponse)
async def get_orchestration_history(session_id: str):
    """Get the full conversation history for an orchestration session"""
    orchestrator = orchestrator_manager.get_orchestrator(session_id)
    
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Orchestration session not found: {session_id}"
        )
    
    return OrchestrationHistoryResponse(
        session_id=session_id,
        history=orchestrator.get_conversation_history(),
        summary=orchestrator.get_summary()
    )


@router.post("/continue/{session_id}", response_model=OrchestrationResponse)
async def continue_orchestration(
    session_id: str,
    rounds: Optional[int] = 1
):
    """Continue an existing orchestration session for additional rounds"""
    orchestrator = orchestrator_manager.get_orchestrator(session_id)
    
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Orchestration session not found: {session_id}"
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
async def delete_orchestration(session_id: str):
    """Delete an orchestration session"""
    deleted = orchestrator_manager.delete_orchestrator(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Orchestration session not found: {session_id}"
        )
    
    return {
        "status": "success",
        "message": f"Orchestration session deleted: {session_id}"
    }


@router.get("/sessions")
async def get_all_orchestration_sessions():
    """Get all active orchestration sessions"""
    return {
        "sessions": orchestrator_manager.get_all_sessions()
    }
