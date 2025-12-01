"""Single-agent chat endpoints"""
from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse, HistoryResponse
from services.agent_manager import agent_manager

router = APIRouter(tags=["Chats"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to an agent and get a response
    
    - **message**: The message to send to the agent
    - **session_id**: Optional session identifier (default: "default")
    - **agent_type**: Type of agent (junior_engineer or product_manager)
    """
    try:
        agent = agent_manager.get_agent(
            session_id=request.session_id,
            agent_type=request.agent_type
        )
        
        response = agent.chat(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            agent_type=request.agent_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history", response_model=HistoryResponse)
async def get_history(
    session_id: str = "default",
    agent_type: str = "junior_engineer"
):
    """
    Get conversation history for a session and agent type
    """
    if not agent_manager.session_exists(session_id, agent_type):
        raise HTTPException(
            status_code=404, 
            detail=f"Session '{session_id}' with agent '{agent_type}' not found"
        )
    
    agent = agent_manager.get_agent(session_id, agent_type)
    
    return HistoryResponse(
        history=agent.get_history(),
        session_id=session_id,
        agent_type=agent_type
    )


@router.delete("/{session_id}/history")
async def reset_conversation(session_id: str = "default"):
    """
    Reset conversation history for a session
    
    - **session_id**: The session identifier
    """
    if not agent_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = agent_manager.get_agent(session_id)
    agent.reset_history()
    
    return {
        "status": "success",
        "message": f"Conversation history reset for session: {session_id}"
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session entirely
    
    - **session_id**: The session identifier
    """
    if session_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default session")
    
    if not agent_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent_manager.delete_session(session_id)
    
    return {
        "status": "success",
        "message": f"Session deleted: {session_id}"
    }


@router.get("/")
async def list_sessions():
    """
    List all active chat sessions
    """
    sessions = agent_manager.get_all_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions)
    }

