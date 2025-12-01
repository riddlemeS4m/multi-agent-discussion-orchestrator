from fastapi import FastAPI
from services.agent_manager import agent_manager
from routers import health, sessions
import uvicorn

app = FastAPI(
    title="Multi-Agent Discussion Orchestrator API",
    description="A simple multi-agent system for discussing and orchestrating discussions",
    version="0.1.0"
)

# Include routers
app.include_router(health.router)
app.include_router(sessions.router)


@app.on_event("startup")
async def startup_event():
    """Initialize default agent on startup"""
    print("Initializing agents...")
    agent_manager.initialize_default_agent()
    print("Agents ready!")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
