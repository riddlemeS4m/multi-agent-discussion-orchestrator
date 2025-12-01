from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from typing import List, Dict, Optional
from pathlib import Path
import os
from dotenv import load_dotenv
from config import get_langsmith_metadata, get_run_name

# Load environment variables
load_dotenv()


class Agent:
    """A simple LangChain-powered agent with a system prompt"""
    
    def __init__(
        self, 
        role: str, 
        prompt_file: str, 
        model: str = "gpt-4o-mini",
        agent_type: Optional[str] = None
    ):
        self.role = role
        self.model = model
        self.agent_type = agent_type or role.lower().replace(" ", "_")
        
        # Load system prompt from file
        self.system_prompt = self._load_prompt(prompt_file)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Create chain
        self.chain = self.prompt | self.llm
        
        # Conversation history
        self.conversation_history: List = []
    
    def _load_prompt(self, prompt_file: str) -> str:
        """Load system prompt from a markdown file"""
        prompt_path = Path(__file__).parent / "prompts" / prompt_file
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r') as f:
            return f.read()
    
    def chat(self, message: str, session_id: Optional[str] = None) -> str:
        """
        Send a message and get a response using the agent's own conversation history.
        This is stateful - it updates the agent's internal history.
        
        Args:
            message: The input message
            session_id: Optional session ID for LangSmith tracing
        """
        # Prepare LangSmith configuration
        config = {
            "run_name": get_run_name("agent_chat", agent_role=self.role),
            "metadata": get_langsmith_metadata(
                session_id=session_id,
                agent_type=self.agent_type,
                agent_role=self.role,
                interaction_type="stateful_chat"
            ),
            "tags": [self.agent_type, "stateful_chat"]
        }
        
        response = self.chain.invoke(
            {
                "history": self.conversation_history,
                "input": message
            },
            config=config
        )
        
        # Update conversation history
        self.conversation_history.append(HumanMessage(content=message))
        self.conversation_history.append(AIMessage(content=response.content))
        
        return response.content
    
    def chat_with_shared_history(
        self, 
        message: str, 
        history: List,
        session_id: Optional[str] = None,
        round_num: Optional[int] = None,
        orchestration_mode: Optional[str] = None
    ) -> str:
        """
        Generate a response using external/shared conversation history.
        This is stateless - it does NOT modify the agent's internal history.
        Useful for orchestrated conversations where history is shared across agents.
        
        Args:
            message: The input message/prompt
            history: Shared conversation history
            session_id: Optional session ID for LangSmith tracing
            round_num: Optional round number for multi-round discussions
            orchestration_mode: Optional orchestration mode (e.g., "round_robin")
        """
        # Prepare LangSmith configuration
        config = {
            "run_name": get_run_name(
                "agent_response",
                agent_role=self.role,
                round_num=round_num
            ),
            "metadata": get_langsmith_metadata(
                session_id=session_id,
                agent_type=self.agent_type,
                agent_role=self.role,
                orchestration_mode=orchestration_mode,
                round_num=round_num,
                interaction_type="orchestrated_chat"
            ),
            "tags": [
                self.agent_type,
                "orchestrated_chat",
                orchestration_mode if orchestration_mode else "unknown_mode"
            ]
        }
        
        response = self.chain.invoke(
            {
                "history": history,
                "input": message
            },
            config=config
        )
        
        return response.content
    
    def reset_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history in a serializable format"""
        history = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history
