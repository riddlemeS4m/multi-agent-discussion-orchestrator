from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.agent_manager import agent_manager
from api.v1.api import api_router
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("Initializing agents...")
    agent_manager.initialize_default_agent()
    print("Agents ready!")
    
    yield
    
    # Shutdown (if needed in the future)
    print("Shutting down...")


app = FastAPI(
    title="Multi-Agent Discussion Orchestrator API",
    description="A simple multi-agent system for discussing and orchestrating discussions",
    version="0.1.0",
    lifespan=lifespan
)

# Include API v1 router with prefix
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
