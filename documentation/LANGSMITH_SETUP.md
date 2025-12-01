# LangSmith Integration Setup Guide

This guide walks you through setting up LangSmith tracing for your Multi-Agent Discussion Orchestrator.

## 🎯 What You'll Get

LangSmith provides:
- **Visual traces** of all multi-agent conversations
- **Performance metrics** (latency, token usage)
- **Debugging tools** to inspect LLM inputs/outputs
- **Dataset creation** from production conversations
- **Cost tracking** and optimization insights

## 📋 Prerequisites

- A LangSmith account (free tier available)
- The project dependencies installed (`pip install -r requirements.txt`)

---

## Step 1: Create a LangSmith Account

1. **Go to LangSmith**: Navigate to [https://smith.langchain.com](https://smith.langchain.com)

2. **Sign up**: Click "Sign Up" and create an account using:
   - Email/password, or
   - GitHub OAuth, or
   - Google OAuth

3. **Verify your email** (if using email/password signup)

---

## Step 2: Create a Project

1. **After logging in**, you'll see the LangSmith dashboard

2. **Create a new project**:
   - Click the **"New Project"** button (or "Create Project")
   - Name it: `multi-agent-orchestrator` (or any name you prefer)
   - Add an optional description: "Tracing for multi-agent discussion system"
   - Click **"Create"**

3. **Note your project name** - you'll need it for the environment variables

---

## Step 3: Get Your API Key

1. **Click on your profile/avatar** in the top-right corner

2. **Select "Settings"** or "API Keys" from the dropdown

3. **Create a new API key**:
   - Click **"Create API Key"**
   - Give it a name like "multi-agent-orchestrator-dev"
   - Optionally set permissions (full access is fine for development)
   - Click **"Create"**

4. **Copy the API key immediately** - it will only be shown once!
   - It will look like: `lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **Important**: Store this key securely. Don't commit it to version control!

---

## Step 4: Configure Environment Variables

Add these variables to your `.env` file:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Your API key
LANGCHAIN_PROJECT=multi-agent-orchestrator  # Your project name
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com  # Default endpoint
```

### Environment Variable Details:

| Variable | Required | Description |
|----------|----------|-------------|
| `LANGCHAIN_TRACING_V2` | Yes | Set to `true` to enable tracing |
| `LANGCHAIN_API_KEY` | Yes | Your LangSmith API key |
| `LANGCHAIN_PROJECT` | No | Project name (defaults to "multi-agent-orchestrator") |
| `LANGCHAIN_ENDPOINT` | No | API endpoint (defaults to https://api.smith.langchain.com) |

---

## Step 5: Install Dependencies

If you haven't already, install the updated dependencies:

```bash
# Activate your virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install/upgrade dependencies
pip install -r requirements.txt
```

---

## Step 6: Test the Integration

1. **Start your server**:
   ```bash
   python main.py
   ```

2. **Check the startup logs** - you should see:
   ```
   🔍 LangSmith Tracing Status:
     ✅ Enabled
     📊 Project: multi-agent-orchestrator
     🔗 Endpoint: https://api.smith.langchain.com
   ```

3. **Make a test request**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/discussions" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "test-session",
       "task": "Design a simple todo app API",
       "agent_types": ["product_manager", "junior_engineer"],
       "mode": "sequential",
       "rounds": 1
     }'
   ```

4. **View traces in LangSmith**:
   - Go to [https://smith.langchain.com](https://smith.langchain.com)
   - Select your project from the dropdown
   - You should see traces appearing in real-time!

---

## 🔍 Understanding Your Traces

### Trace Organization

Each discussion creates a **trace tree** that shows:

1. **Top-level run**: The orchestrator's discussion execution
2. **Nested runs**: Individual agent responses
3. **Sub-runs**: LLM calls within each agent

### Trace Metadata

Each trace includes useful metadata:
- `session_id`: Discussion/session identifier
- `agent_type`: Agent type (e.g., "product_manager")
- `agent_role`: Human-readable role (e.g., "Product Manager")
- `orchestration_mode`: Mode used (round_robin, sequential, adaptive)
- `round`: Round number (for multi-round discussions)
- `operation`: Type of operation (e.g., "prompt_generation", "should_continue_decision")

### Trace Tags

Traces are tagged for easy filtering:
- Agent type tags: `product_manager`, `junior_engineer`, `project_manager`
- Mode tags: `round_robin`, `sequential`, `adaptive`
- Operation tags: `orchestrator`, `decision_making`, `prompt_generation`

---

## 🎨 Using LangSmith Dashboard

### View Traces

1. **Projects page**: See all traces for your project
2. **Click a trace**: Drill down into the full execution tree
3. **Inspect I/O**: View exact inputs and outputs for each LLM call
4. **Performance metrics**: See latency and token usage

### Filter Traces

Use the filter bar to find specific traces:
```
tag:adaptive                    # All adaptive mode discussions
metadata.agent_role:"Product Manager"   # All PM responses
metadata.round:2                # All round 2 interactions
```

### Compare Runs

1. Select multiple traces using checkboxes
2. Click **"Compare"**
3. View side-by-side outputs, latencies, and costs

### Create Datasets

1. Find a good example trace
2. Click **"Add to Dataset"**
3. Create evaluation datasets for testing improvements

---

## 🐛 Troubleshooting

### Traces Not Appearing

**Problem**: Server starts but no traces show up in LangSmith.

**Solutions**:
1. Check your API key is correct in `.env`
2. Verify `LANGCHAIN_TRACING_V2=true` (not "True" or "TRUE")
3. Restart the server after updating `.env`
4. Check network connectivity to api.smith.langchain.com
5. Look for errors in server logs

### "API Key Invalid" Error

**Problem**: Server logs show authentication errors.

**Solutions**:
1. Verify you copied the entire API key (including `lsv2_pt_` prefix)
2. Check for extra spaces in the `.env` file
3. Generate a new API key from LangSmith settings
4. Ensure the key hasn't been revoked

### Project Not Found

**Problem**: Traces appear in wrong project or "Default Project".

**Solutions**:
1. Verify `LANGCHAIN_PROJECT` matches your project name exactly
2. Check for typos in the project name
3. If project doesn't exist, LangSmith creates it automatically

### Slow Performance

**Problem**: Application feels slower with tracing enabled.

**Note**: LangSmith adds minimal overhead (<100ms per trace), but:
1. Check your internet connection
2. Tracing is asynchronous and shouldn't block requests
3. Consider disabling in production if needed

---

## 🔧 Advanced Configuration

### Sampling (Production Use)

To reduce costs in production, sample traces:

```python
import os
import random

# In config/langsmith_config.py, add:
def should_trace():
    """Sample 10% of traces in production"""
    if os.getenv("ENVIRONMENT") == "production":
        return random.random() < 0.1
    return True

# Use in your code:
if should_trace():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
```

### Custom Run Names

The integration already provides descriptive run names like:
- `agent_response [Product Manager] Round-2`
- `orchestrator_decision [Project Manager]`
- `orchestrator_prompt_generation [Junior Engineer] Round-1`

### Environment-Specific Projects

Use different projects per environment:

```bash
# .env.development
LANGCHAIN_PROJECT=multi-agent-orchestrator-dev

# .env.production
LANGCHAIN_PROJECT=multi-agent-orchestrator-prod
```

---

## 💡 Best Practices

1. **Use descriptive session IDs**: Help identify traces later
   ```python
   session_id = f"user-{user_id}-{timestamp}"
   ```

2. **Tag important discussions**: Add custom metadata for key interactions

3. **Review traces regularly**: Identify slow agents or poor prompts

4. **Create datasets**: Save good examples for future evaluation

5. **Monitor costs**: Track token usage in LangSmith dashboard

6. **Disable in local testing**: Set `LANGCHAIN_TRACING_V2=false` when not needed

---

## 📊 Example Use Cases

### Debug Agent Behavior

**Scenario**: Product Manager agent gives irrelevant responses.

**Solution**:
1. Find a problematic trace in LangSmith
2. Inspect the agent's input (prompt + history)
3. Check if the system prompt is clear
4. Verify conversation history is correct
5. Adjust prompts and re-test

### Optimize Performance

**Scenario**: Discussions are too slow.

**Solution**:
1. View latency breakdown by agent
2. Identify the slowest agent/operation
3. Check if that agent's prompt is too long
4. Consider using a faster model for that agent
5. Compare latencies across different modes

### Compare Orchestration Modes

**Scenario**: Unsure which mode produces better results.

**Solution**:
1. Run same task with different modes
2. Tag each with mode name
3. Use LangSmith's compare feature
4. Analyze quality, latency, and cost differences

---

## 🔗 Useful Links

- **LangSmith Docs**: https://docs.smith.langchain.com
- **LangSmith Platform**: https://smith.langchain.com
- **LangChain Docs**: https://python.langchain.com/docs/langsmith
- **API Reference**: https://api.smith.langchain.com/docs

---

## ✅ Quick Start Checklist

- [ ] Created LangSmith account
- [ ] Created project in LangSmith
- [ ] Generated API key
- [ ] Added environment variables to `.env`
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Started server and verified tracing is enabled
- [ ] Made test request
- [ ] Viewed traces in LangSmith dashboard

---

## 🎉 You're All Set!

Your multi-agent orchestrator now has enterprise-grade tracing. Every agent interaction, orchestrator decision, and LLM call is visible in LangSmith.

**Next Steps**:
1. Run some discussions and explore the traces
2. Experiment with filters and comparisons
3. Create datasets from good examples
4. Optimize based on insights from traces

Happy tracing! 🚀

