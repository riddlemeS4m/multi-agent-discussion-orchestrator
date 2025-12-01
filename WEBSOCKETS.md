# WebSocket Discussion API Usage Guide

## Overview

The discussion API uses a pub/sub pattern with WebSockets for real-time streaming. Start a discussion with a POST request, then connect via WebSocket to receive live events as agents respond.

## Quick Start

### Step 1: Start a Discussion

Use a regular HTTP POST request to start a discussion:

```bash
curl -X POST http://localhost:8000/api/v1/discussions \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a scalable authentication system",
    "agent_types": ["junior_engineer", "product_manager"],
    "mode": "round_robin",
    "rounds": 1,
    "enable_project_manager": true
  }'
```

Response:
```json
{
  "discussion_id": "abc-123-def-456",
  "session_id": "orchestration-abc-123-def-456",
  "status": "started",
  "message": "Discussion started in background. Connect to WebSocket for real-time updates.",
  "websocket_url": "/api/v1/discussions/abc-123-def-456/stream"
}
```

### Step 2: Connect to WebSocket Stream

Establish a WebSocket connection to receive real-time events.

#### Python Client (Recommended)

```python
import asyncio
import websockets
import json

async def stream_discussion(discussion_id):
    uri = f"ws://localhost:8000/api/v1/discussions/{discussion_id}/stream"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"Event: {event['event_type']}")
            print(json.dumps(event, indent=2))
            
            if event['event_type'] in ['discussion_complete', 'error']:
                break

asyncio.run(stream_discussion("your-discussion-id"))
```

#### JavaScript/Browser

Use in browser console or client application:

```javascript
const discussionId = "your-discussion-id"; // Replace with actual ID
const ws = new WebSocket(`ws://localhost:8000/api/v1/discussions/${discussionId}/stream`);

ws.onopen = () => {
  console.log('Connected to discussion stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Event: ${data.event_type}`, data);
};

ws.onclose = () => {
  console.log('Stream closed');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

#### CLI Tools

**websocat** (install: `brew install websocat`):
```bash
websocat ws://localhost:8000/api/v1/discussions/your-discussion-id/stream
```

**wscat** (install: `npm install -g wscat`):
```bash
wscat -c ws://localhost:8000/api/v1/discussions/your-discussion-id/stream
```

### Step 3: Alternative - Status Polling

For environments without WebSocket support, use HTTP polling:

```bash
# Get current status
curl http://localhost:8000/api/v1/discussions/{discussion_id}/status

# Get full history (after completion)
curl http://localhost:8000/api/v1/discussions/{discussion_id}/history
```

## Event Types You'll Receive

When connected to the WebSocket, you'll receive these event types:

1. **discussion_start** - Discussion has begun
   ```json
   {
     "event_type": "discussion_start",
     "timestamp": "2025-12-01T04:50:36.593916",
     "data": {
       "discussion_id": "...",
       "task": "...",
       "agent_types": [...],
       "mode": "round_robin"
     }
   }
   ```

2. **round_start** - New round beginning
   ```json
   {
     "event_type": "round_start",
     "timestamp": "...",
     "data": {
       "round": 1,
       "total_rounds": 2
     }
   }
   ```

3. **agent_thinking** - Agent is processing
   ```json
   {
     "event_type": "agent_thinking",
     "timestamp": "...",
     "data": {
       "agent_type": "junior_engineer",
       "role": "Junior Engineer",
       "round": 1
     }
   }
   ```

4. **agent_response** - Agent has responded
   ```json
   {
     "event_type": "agent_response",
     "timestamp": "...",
     "data": {
       "agent_type": "junior_engineer",
       "role": "Junior Engineer",
       "round": "1",
       "response": "...",
       "prompt_used": "..." // Only if enable_project_manager=true
     }
   }
   ```

5. **discussion_complete** - Discussion finished
   ```json
   {
     "event_type": "discussion_complete",
     "timestamp": "...",
     "data": {
       "total_responses": 2,
       "conversation_history": [...],
       "result": {...}
     }
   }
   ```

6. **error** - An error occurred
   ```json
   {
     "event_type": "error",
     "timestamp": "...",
     "data": {
       "error": "Error message here"
     }
   }
   ```

## Complete Python Example

See `test_websocket_client.py` for a complete working example that demonstrates:
- Starting a discussion
- Connecting to WebSocket stream
- Receiving and processing events in real-time
- Polling fallback for when WebSocket isn't available

Run it with:
```bash
python test_websocket_client.py
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/discussions` | Start async discussion (returns immediately) |
| GET | `/api/v1/discussions` | List all discussions |
| WebSocket | `/api/v1/discussions/{discussion_id}/stream` | Stream real-time events |
| GET | `/api/v1/discussions/{discussion_id}/status` | Get current status (polling) |
| GET | `/api/v1/discussions/{discussion_id}/history` | Get complete event history |
| DELETE | `/api/v1/discussions/{discussion_id}` | Delete a discussion |
| DELETE | `/api/v1/discussions/{discussion_id}/history` | Clear discussion event history |

## WebSocket Benefits

- **Real-time updates** - Events streamed as they occur
- **Efficient** - Single persistent connection
- **Low latency** - No polling overhead
- **Live progress** - Show discussion progress to users in real-time

## Notes

- WebSocket connections require a WebSocket client (not HTTP GET requests)
- Connections automatically close after `discussion_complete` or `error` events
- Historical events are sent immediately upon connection, followed by live events
- The `/status` and `/history` endpoints provide HTTP alternatives for polling-based clients

