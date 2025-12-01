# multi-agent-discussion-orchestrator

A FastAPI-based multi-agent system using LangChain and OpenAI with integrated LangSmith tracing.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with required environment variables:
```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional: LangSmith Tracing (see LANGSMITH_SETUP.md)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=multi-agent-orchestrator
```

4. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 🔍 LangSmith Tracing (Optional)

This project includes integrated LangSmith tracing for monitoring and debugging multi-agent conversations.

**Benefits**:
- Visual traces of all agent interactions
- Performance metrics and token usage tracking
- Debugging tools for LLM inputs/outputs
- Dataset creation for evaluation

**Setup**: See [LANGSMITH_SETUP.md](LANGSMITH_SETUP.md) for detailed instructions.

**Quick Start**:
1. Create account at [smith.langchain.com](https://smith.langchain.com)
2. Get API key and create project
3. Add environment variables to `.env`
4. Restart server - tracing will auto-enable!

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Usage Example
```bash
# Send a message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a function to reverse a string in Python", "session_id": "test"}'
