"""Multi-agent discussion endpoints with async WebSocket support"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
import uuid
import asyncio
from services.agent_manager import agent_manager
from services.orchestrator_manager import orchestrator_manager
from services.discussion_manager import discussion_manager
from constants import DiscussionStatus
from schemas import (
    StartAsyncDiscussionRequest,
    StartAsyncDiscussionResponse,
    DiscussionStatusResponse
)


router = APIRouter(tags=["Discussions"])


async def run_orchestration_background(
    discussion_id: str,
    session_id: str,
    task: str,
    agent_types: list[str],
    mode: str,
    rounds: int,
    use_intelligent_prompts: bool
):
    """Run orchestration in the background with event streaming"""
    
    try:
        # Update status to running
        discussion_manager.update_status(discussion_id, DiscussionStatus.RUNNING)
        
        # Get the discussion state
        discussion = discussion_manager.get_discussion(discussion_id)
        
        # Event callback that adds events to state and broadcasts
        async def emit_event(event_type: str, data: dict):
            event = discussion.add_event(event_type, data)
            await discussion_manager.broadcast_event(discussion_id, event)
        
        # Create orchestrator with event callback
        orchestrator = orchestrator_manager.create_orchestrator(
            session_id=session_id,
            agent_types=agent_types,
            mode=mode,
            event_callback=emit_event
        )
        
        # Add initial task
        orchestrator.add_initial_task(task)
        
        # Emit start event
        await emit_event("discussion_start", {
            "discussion_id": discussion_id,
            "task": task,
            "agent_types": agent_types,
            "mode": mode
        })
        
        # Run the discussion
        result = await orchestrator.run_discussion_async(
            rounds=rounds,
            use_intelligent_prompts=use_intelligent_prompts
        )
        
        # Emit completion event
        await emit_event("discussion_complete", {
            "total_responses": len(result) if isinstance(result, list) else len(result.get("responses", [])),
            "conversation_history": orchestrator.get_conversation_history(),
            "result": result if isinstance(result, dict) else {"responses": result}
        })
        
        # Update status to completed
        discussion_manager.update_status(discussion_id, DiscussionStatus.COMPLETED)
        
    except Exception as e:
        # Update status to failed
        discussion_manager.update_status(
            discussion_id, 
            DiscussionStatus.FAILED,
            error=str(e)
        )
        
        # Emit error event
        discussion = discussion_manager.get_discussion(discussion_id)
        if discussion:
            event = discussion.add_event("error", {"error": str(e)})
            await discussion_manager.broadcast_event(discussion_id, event)


@router.post("/", response_model=StartAsyncDiscussionResponse)
async def start_async_discussion(
    request: StartAsyncDiscussionRequest,
    background_tasks: BackgroundTasks
):
    """
    Start an orchestrated discussion asynchronously (returns immediately)
    
    The discussion runs in the background. Connect to the WebSocket
    to receive real-time updates.
    """
    # Validate agent types
    available_agents = agent_manager.get_available_agent_types()
    for agent_type in request.agent_types:
        if agent_type not in available_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {agent_type}. Available: {available_agents}"
            )
    
    if len(request.agent_types) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 agent types for a discussion"
        )
    
    # Generate unique IDs
    discussion_id = str(uuid.uuid4())
    session_id = f"orchestration-{discussion_id}"
    
    # Create discussion state
    discussion_manager.create_discussion(
        discussion_id=discussion_id,
        session_id=session_id,
        task=request.task,
        agent_types=request.agent_types,
        mode=request.mode
    )
    
    # Start orchestration in background
    background_tasks.add_task(
        run_orchestration_background,
        discussion_id=discussion_id,
        session_id=session_id,
        task=request.task,
        agent_types=request.agent_types,
        mode=request.mode,
        rounds=request.rounds,
        use_intelligent_prompts=request.enable_project_manager
    )
    
    return StartAsyncDiscussionResponse(
        discussion_id=discussion_id,
        session_id=session_id,
        status="started",
        message="Discussion started in background. Connect to WebSocket for real-time updates.",
        websocket_url=f"/api/v1/discussions/{discussion_id}/stream"
    )


@router.websocket("/{discussion_id}/stream")
async def stream_discussion(websocket: WebSocket, discussion_id: str):
    """
    WebSocket endpoint to stream discussion events in real-time
    
    Connect to this endpoint to receive live updates about the discussion progress.
    """
    await websocket.accept()
    
    discussion = discussion_manager.get_discussion(discussion_id)
    if not discussion:
        await websocket.send_json({
            "error": f"Discussion not found: {discussion_id}"
        })
        await websocket.close()
        return
    
    # Subscribe to discussion events
    queue = discussion_manager.subscribe(discussion_id)
    
    try:
        # Send any existing events first
        for event in discussion.events:
            await websocket.send_json(event.to_dict())
        
        # Stream new events as they arrive
        while True:
            # Wait for new event or check if discussion is complete
            try:
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json(event.to_dict())
                
                # Close connection after completion or error
                if event.event_type in ["discussion_complete", "error"]:
                    await websocket.close()
                    break
                    
            except asyncio.TimeoutError:
                # Check if discussion completed while we were waiting
                current_discussion = discussion_manager.get_discussion(discussion_id)
                if current_discussion and current_discussion.status in [DiscussionStatus.COMPLETED, DiscussionStatus.FAILED]:
                    await websocket.close()
                    break
                continue
                
    except WebSocketDisconnect:
        pass
    finally:
        discussion_manager.unsubscribe(discussion_id, queue)


@router.get("/{discussion_id}/status", response_model=DiscussionStatusResponse)
async def get_discussion_status(discussion_id: str):
    """Get the current status of a discussion (polling fallback if WebSocket not available)"""
    discussion = discussion_manager.get_discussion(discussion_id)
    
    if not discussion:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion not found: {discussion_id}"
        )
    
    return DiscussionStatusResponse(
        discussion_id=discussion_id,
        status=discussion.status,
        progress={
            "created_at": discussion.created_at,
            "started_at": discussion.started_at,
            "completed_at": discussion.completed_at,
            "agent_types": discussion.agent_types,
            "mode": discussion.mode,
            "error": discussion.error
        },
        events_count=len(discussion.events)
    )


@router.get("/{discussion_id}/history")
async def get_discussion_history(discussion_id: str):
    """Get the full event history for a discussion"""
    discussion = discussion_manager.get_discussion(discussion_id)
    
    if not discussion:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion not found: {discussion_id}"
        )
    
    return discussion.to_dict()


@router.get("/")
async def list_all_discussions():
    """Get all discussions"""
    return {
        "discussions": discussion_manager.get_all_discussions()
    }


@router.delete("/{discussion_id}")
async def delete_discussion(discussion_id: str):
    """Delete a discussion and its state"""
    discussion = discussion_manager.get_discussion(discussion_id)
    
    if not discussion:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion not found: {discussion_id}"
        )
    
    # Delete the discussion from the manager
    del discussion_manager.discussions[discussion_id]
    
    # Clean up any orphaned subscribers
    if discussion_id in discussion_manager.subscribers:
        del discussion_manager.subscribers[discussion_id]
    
    # Also delete the orchestrator session if it exists
    session_id = discussion.session_id
    orchestrator_manager.delete_orchestrator(session_id)
    
    return {
        "status": "success",
        "message": f"Discussion deleted: {discussion_id}"
    }


@router.delete("/{discussion_id}/history")
async def clear_discussion_history(discussion_id: str):
    """Clear the event history for a discussion"""
    discussion = discussion_manager.get_discussion(discussion_id)
    
    if not discussion:
        raise HTTPException(
            status_code=404,
            detail=f"Discussion not found: {discussion_id}"
        )
    
    # Clear the events
    events_cleared = len(discussion.events)
    discussion.events = []
    
    return {
        "status": "success",
        "message": f"Cleared {events_cleared} events from discussion {discussion_id}",
        "events_cleared": events_cleared
    }
