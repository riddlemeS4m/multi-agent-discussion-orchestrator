"""Session and chat management endpoints"""
from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse, HistoryResponse
from services.agent_manager import agent_manager

router = APIRouter(tags=["Sessions"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the agent and get a response
    
    - **message**: The message to send to the agent
    - **session_id**: Optional session identifier (default: "default")
    """
    session_id = request.session_id
    agent = agent_manager.get_agent(session_id)
    
    try:
        response = agent.chat(request.message)
        return ChatResponse(
            response=response,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str = "default"):
    """
    Get conversation history for a session
    
    - **session_id**: The session identifier
    """
    if not agent_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = agent_manager.get_agent(session_id)
    
    return HistoryResponse(
        history=agent.get_history(),
        session_id=session_id
    )


@router.post("/reset/{session_id}")
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


@router.delete("/session/{session_id}")
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


@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    """
    sessions = agent_manager.get_all_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions)
    }

