from enum import Enum

AGENT_CONFIGS = {
    "junior_engineer": {
        "role": "Junior Engineer",
        "prompt_file": "junior_engineer.md",
        "model": "gpt-4o-mini"
    },
    "product_manager": {
        "role": "Product Manager",
        "prompt_file": "product_manager.md",
        "model": "gpt-4o-mini"
    }
}

class OrchestrationMode(str, Enum):
    """Available orchestration modes"""
    ROUND_ROBIN = "round_robin"
    SEQUENTIAL = "sequential"
    # We can add DYNAMIC later

class AgentType(str, Enum):
    """Available agent types"""
    JUNIOR_ENGINEER = "junior_engineer"
    PRODUCT_MANAGER = "product_manager"
