from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.agent_manager import agent_manager
from api.v1.api import api_router
from config import langsmith_config
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("=" * 60)
    print("🚀 Multi-Agent Discussion Orchestrator Starting...")
    print("=" * 60)
    
    # Initialize agents
    print("📝 Initializing agents...")
    agent_manager.initialize_default_agents()
    print("✅ Agents ready!")
    
    # Check LangSmith status
    print("\n🔍 LangSmith Tracing Status:")
    status = langsmith_config.get_status()
    if langsmith_config.is_enabled():
        print(f"  ✅ Enabled")
        print(f"  📊 Project: {status['project']}")
        print(f"  🔗 Endpoint: {status['endpoint']}")
    else:
        print(f"  ⚠️  Disabled")
        if not status['api_key_set']:
            print("  ℹ️  Set LANGCHAIN_API_KEY to enable tracing")
        else:
            print("  ℹ️  Set LANGCHAIN_TRACING_V2=true to enable tracing")
    
    print("=" * 60)
    print("🎉 Server ready!\n")
    
    yield
    
    # Shutdown (if needed in the future)
    print("\n👋 Shutting down...")


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
