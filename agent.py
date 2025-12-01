from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from typing import List, Dict
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Agent:
    """A simple LangChain-powered agent with a system prompt"""
    
    def __init__(self, role: str, prompt_file: str, model: str = "gpt-4o-mini"):
        self.role = role
        self.model = model
        
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
    
    def chat(self, message: str) -> str:
        """Send a message and get a response"""
        response = self.chain.invoke({
            "history": self.conversation_history,
            "input": message
        })
        
        # Update conversation history
        self.conversation_history.append(HumanMessage(content=message))
        self.conversation_history.append(AIMessage(content=response.content))
        
        return response.content
    
    def chat_with_history(self, message: str, history: List) -> str:
        """
        Send a message with external conversation history
        Useful for orchestrated conversations where history is shared
        """
        response = self.chain.invoke({
            "history": history,
            "input": message
        })
        
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
