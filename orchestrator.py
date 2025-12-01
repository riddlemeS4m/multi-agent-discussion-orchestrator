from typing import List, Dict, Optional, Callable, Awaitable
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from agent import Agent
from services.agent_manager import agent_manager
from constants import OrchestrationMode
import asyncio


class Orchestrator(Agent):
    """
    Intelligent orchestrator that manages multi-agent conversations.
    Inherits from Agent to leverage LLM capabilities for guiding discussions.
    """
    
    def __init__(
        self,
        session_id: str,
        agent_types: List[str],
        mode: OrchestrationMode = OrchestrationMode.ROUND_ROBIN,
        model: str = "gpt-4o-mini",
        event_callback: Optional[Callable[[str, Dict], Awaitable[None]]] = None
    ):
        # Initialize as an Agent with the project manager role
        super().__init__(
            role="Project Manager",
            prompt_file="project_manager.md",
            model=model
        )
        
        # Orchestration-specific attributes
        self.session_id = session_id
        self.agent_types = agent_types
        self.mode = mode
        self.event_callback = event_callback
        
        # Shared conversation history across all agents
        # Note: This is different from self.conversation_history inherited from Agent
        # which is used for the orchestrator's own LLM interactions
        self.shared_history: List = []
        
        # Get agent instances
        self.agents: Dict[str, Agent] = {
            agent_type: agent_manager.get_agent(session_id, agent_type)
            for agent_type in agent_types
        }
        
        # Track current turn for round-robin
        self.current_turn = 0
    
    async def _emit_event(self, event_type: str, data: Dict):
        """Emit an event if callback is provided"""
        if self.event_callback:
            await self.event_callback(event_type, data)
    
    def add_initial_task(self, task: str):
        """Add the initial task to shared conversation history"""
        self.shared_history.append(
            HumanMessage(content=f"[TASK] {task}")
        )
    
    def _generate_agent_prompt(self, agent_type: str, round_num: int = None, context: str = "") -> str:
        """
        Use the orchestrator's intelligence to generate a contextual prompt for an agent.
        
        Args:
            agent_type: The type of agent being prompted
            round_num: Current round number (if applicable)
            context: Additional context about what to focus on
        """
        agent = self.agents[agent_type]
        
        # Build request for orchestrator LLM
        if round_num is not None:
            request = f"""Generate a prompt for the {agent.role} agent (round {round_num}).

Agent role: {agent.role}

Based on the conversation so far, what should this agent focus on? Create a clear, specific prompt that:
1. References relevant points from previous discussion
2. Asks the agent to apply their unique expertise
3. Advances the discussion toward a solution

Keep the prompt concise (2-3 sentences max)."""
        else:
            request = f"""Generate a prompt for the {agent.role} agent.

Agent role: {agent.role}

Based on the conversation so far, what should this agent focus on? Create a clear, specific prompt that:
1. Asks the agent to analyze the task from their perspective
2. Encourages them to provide their unique expertise
3. Helps move toward a solution

Keep the prompt concise (2-3 sentences max)."""
        
        if context:
            request += f"\n\nAdditional context: {context}"
        
        # Use orchestrator's inherited LLM to generate intelligent prompt
        # Use shared_history so the orchestrator sees the full discussion context
        response = self.chain.invoke({
            "history": self.shared_history,
            "input": request
        })
        
        return response.content
    
    def _should_continue_discussion(self) -> tuple[bool, str]:
        """
        Use orchestrator's intelligence to determine if more discussion would be valuable.
        
        Returns:
            tuple: (should_continue, reason)
        """
        request = """Analyze the discussion so far. Has the task been sufficiently addressed?

Consider:
1. Have all key perspectives been shared?
2. Are there unresolved questions or gaps?
3. Would another round add significant value?

Respond with ONLY 'CONTINUE' or 'COMPLETE' followed by a brief reason (one sentence)."""
        
        response = self.chain.invoke({
            "history": self.shared_history,
            "input": request
        })
        
        decision = response.content.strip()
        should_continue = decision.startswith('CONTINUE')
        
        return should_continue, decision
    
    def run_round_robin(self, rounds: int = 2, use_intelligent_prompts: bool = False) -> List[Dict[str, str]]:
        """
        Run a round-robin discussion where each agent speaks in order
        
        Args:
            rounds: Number of rounds to run
            use_intelligent_prompts: If True, orchestrator uses its LLM to craft contextual prompts
        
        Returns list of responses with metadata
        """
        responses = []
        
        for round_num in range(rounds):
            for agent_type in self.agent_types:
                agent = self.agents[agent_type]
                
                # Generate prompt for agent
                if use_intelligent_prompts:
                    prompt = self._generate_agent_prompt(agent_type, round_num=round_num + 1)
                else:
                    prompt = f"Round {round_num + 1}: Share your perspective on this task."
                
                # Agent responds based on full shared history
                response = agent.chat_with_shared_history(
                    message=prompt,
                    history=self.shared_history
                )
                
                # Add to shared history with role label
                message = AIMessage(content=f"[{agent.role}]: {response}")
                self.shared_history.append(message)
                
                # Track response
                response_dict = {
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": str(round_num + 1),
                    "response": response
                }
                # Only include prompt_used if intelligent prompts are enabled
                if use_intelligent_prompts:
                    response_dict["prompt_used"] = prompt
                
                responses.append(response_dict)
        
        return responses
    
    def run_sequential(self, use_intelligent_prompts: bool = False) -> List[Dict[str, str]]:
        """
        Run a sequential discussion where each agent speaks once in order
        Each agent sees all previous responses
        
        Args:
            use_intelligent_prompts: If True, orchestrator uses its LLM to craft contextual prompts
        """
        responses = []
        
        for agent_type in self.agent_types:
            agent = self.agents[agent_type]
            
            # Generate prompt for agent
            if use_intelligent_prompts:
                prompt = self._generate_agent_prompt(agent_type)
            else:
                prompt = "Share your perspective on this task."
            
            # Agent responds based on everything said so far in shared history
            response = agent.chat_with_shared_history(
                message=prompt,
                history=self.shared_history
            )
            
            # Add to shared history
            message = AIMessage(content=f"[{agent.role}]: {response}")
            self.shared_history.append(message)
            
            response_dict = {
                "agent_type": agent_type,
                "role": agent.role,
                "response": response
            }
            # Only include prompt_used if intelligent prompts are enabled
            if use_intelligent_prompts:
                response_dict["prompt_used"] = prompt
            
            responses.append(response_dict)
        
        return responses
    
    def run_discussion(self, rounds: int = 2, use_intelligent_prompts: bool = False):
        """
        Run a discussion based on the orchestration mode
        
        Args:
            rounds: Number of rounds (for round-robin mode) or max rounds (for adaptive mode)
            use_intelligent_prompts: If True, orchestrator uses its LLM to craft contextual prompts
        
        Returns:
            For ROUND_ROBIN/SEQUENTIAL: List[Dict[str, str]]
            For ADAPTIVE: Dict with responses, rounds_completed, completion_reason, etc.
        """
        if self.mode == OrchestrationMode.ROUND_ROBIN:
            return self.run_round_robin(rounds, use_intelligent_prompts)
        elif self.mode == OrchestrationMode.SEQUENTIAL:
            return self.run_sequential(use_intelligent_prompts)
        elif self.mode == OrchestrationMode.ADAPTIVE:
            return self.run_adaptive_discussion(max_rounds=rounds)
        else:
            raise ValueError(f"Unknown orchestration mode: {self.mode}")
    
    def run_adaptive_discussion(self, max_rounds: int = 5) -> Dict:
        """
        Run an intelligent discussion where the orchestrator decides when to stop.
        Uses the orchestrator's LLM to guide the conversation and determine completion.
        
        Args:
            max_rounds: Maximum number of rounds before stopping
            
        Returns:
            Dict with responses and orchestrator's analysis
        """
        responses = []
        round_num = 0
        
        while round_num < max_rounds:
            round_num += 1
            
            # Run one round with intelligent prompts
            for agent_type in self.agent_types:
                agent = self.agents[agent_type]
                
                # Orchestrator generates contextual prompt
                prompt = self._generate_agent_prompt(agent_type, round_num=round_num)
                
                # Agent responds
                response = agent.chat_with_shared_history(
                    message=prompt,
                    history=self.shared_history
                )
                
                # Add to shared history
                message = AIMessage(content=f"[{agent.role}]: {response}")
                self.shared_history.append(message)
                
                # Track response
                responses.append({
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": str(round_num),
                    "response": response,
                    "prompt_used": prompt
                })
            
            # After each round, orchestrator decides if discussion is complete
            should_continue, reason = self._should_continue_discussion()
            
            if not should_continue:
                return {
                    "responses": responses,
                    "rounds_completed": round_num,
                    "completion_reason": reason,
                    "max_rounds_reached": False
                }
        
        return {
            "responses": responses,
            "rounds_completed": round_num,
            "completion_reason": "Maximum rounds reached",
            "max_rounds_reached": True
        }
    
    async def run_round_robin_async(self, rounds: int = 2, use_intelligent_prompts: bool = False) -> List[Dict[str, str]]:
        """
        Async version of run_round_robin with event streaming
        
        Args:
            rounds: Number of rounds to run
            use_intelligent_prompts: If True, orchestrator uses its LLM to craft contextual prompts
        
        Returns list of responses with metadata
        """
        responses = []
        
        for round_num in range(rounds):
            await self._emit_event("round_start", {
                "round": round_num + 1,
                "total_rounds": rounds
            })
            
            for agent_type in self.agent_types:
                agent = self.agents[agent_type]
                
                await self._emit_event("agent_thinking", {
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": round_num + 1
                })
                
                # Generate prompt for agent
                if use_intelligent_prompts:
                    prompt = self._generate_agent_prompt(agent_type, round_num=round_num + 1)
                else:
                    prompt = f"Round {round_num + 1}: Share your perspective on this task."
                
                # Agent responds based on full shared history (run in thread pool since it's sync)
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    agent.chat_with_shared_history,
                    prompt,
                    self.shared_history
                )
                
                # Add to shared history with role label
                message = AIMessage(content=f"[{agent.role}]: {response}")
                self.shared_history.append(message)
                
                # Track response
                response_dict = {
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": str(round_num + 1),
                    "response": response
                }
                # Only include prompt_used if intelligent prompts are enabled
                if use_intelligent_prompts:
                    response_dict["prompt_used"] = prompt
                
                responses.append(response_dict)
                
                # Emit agent response event
                await self._emit_event("agent_response", response_dict)
        
        return responses
    
    async def run_sequential_async(self, use_intelligent_prompts: bool = False) -> List[Dict[str, str]]:
        """
        Async version of run_sequential with event streaming
        
        Args:
            use_intelligent_prompts: If True, orchestrator uses its LLM to craft contextual prompts
        """
        responses = []
        
        await self._emit_event("discussion_start", {
            "mode": "sequential",
            "agent_count": len(self.agent_types)
        })
        
        for idx, agent_type in enumerate(self.agent_types):
            agent = self.agents[agent_type]
            
            await self._emit_event("agent_thinking", {
                "agent_type": agent_type,
                "role": agent.role,
                "position": idx + 1,
                "total": len(self.agent_types)
            })
            
            # Generate prompt for agent
            if use_intelligent_prompts:
                prompt = self._generate_agent_prompt(agent_type)
            else:
                prompt = "Share your perspective on this task."
            
            # Agent responds based on everything said so far in shared history
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                agent.chat_with_shared_history,
                prompt,
                self.shared_history
            )
            
            # Add to shared history
            message = AIMessage(content=f"[{agent.role}]: {response}")
            self.shared_history.append(message)
            
            response_dict = {
                "agent_type": agent_type,
                "role": agent.role,
                "response": response
            }
            # Only include prompt_used if intelligent prompts are enabled
            if use_intelligent_prompts:
                response_dict["prompt_used"] = prompt
            
            responses.append(response_dict)
            
            # Emit agent response event
            await self._emit_event("agent_response", response_dict)
        
        return responses
    
    async def run_adaptive_discussion_async(self, max_rounds: int = 5) -> Dict:
        """
        Async version of run_adaptive_discussion with event streaming
        
        Args:
            max_rounds: Maximum number of rounds before stopping
            
        Returns:
            Dict with responses and orchestrator's analysis
        """
        responses = []
        round_num = 0
        
        await self._emit_event("discussion_start", {
            "mode": "adaptive",
            "max_rounds": max_rounds
        })
        
        while round_num < max_rounds:
            round_num += 1
            
            await self._emit_event("round_start", {
                "round": round_num,
                "max_rounds": max_rounds
            })
            
            # Run one round with intelligent prompts
            for agent_type in self.agent_types:
                agent = self.agents[agent_type]
                
                await self._emit_event("agent_thinking", {
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": round_num
                })
                
                # Orchestrator generates contextual prompt
                prompt = self._generate_agent_prompt(agent_type, round_num=round_num)
                
                # Agent responds
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    agent.chat_with_shared_history,
                    prompt,
                    self.shared_history
                )
                
                # Add to shared history
                message = AIMessage(content=f"[{agent.role}]: {response}")
                self.shared_history.append(message)
                
                # Track response
                response_dict = {
                    "agent_type": agent_type,
                    "role": agent.role,
                    "round": str(round_num),
                    "response": response,
                    "prompt_used": prompt
                }
                responses.append(response_dict)
                
                # Emit agent response event
                await self._emit_event("agent_response", response_dict)
            
            # After each round, orchestrator decides if discussion is complete
            should_continue, reason = self._should_continue_discussion()
            
            await self._emit_event("round_complete", {
                "round": round_num,
                "should_continue": should_continue,
                "reason": reason
            })
            
            if not should_continue:
                return {
                    "responses": responses,
                    "rounds_completed": round_num,
                    "completion_reason": reason,
                    "max_rounds_reached": False
                }
        
        return {
            "responses": responses,
            "rounds_completed": round_num,
            "completion_reason": "Maximum rounds reached",
            "max_rounds_reached": True
        }
    
    async def run_discussion_async(self, rounds: int = 2, use_intelligent_prompts: bool = False):
        """
        Async version of run_discussion with event streaming
        
        Args:
            rounds: Number of rounds (for round-robin mode) or max rounds (for adaptive mode)
            use_intelligent_prompts: If True, orchestrator uses its LLM to craft contextual prompts
        
        Returns:
            For ROUND_ROBIN/SEQUENTIAL: List[Dict[str, str]]
            For ADAPTIVE: Dict with responses, rounds_completed, completion_reason, etc.
        """
        if self.mode == OrchestrationMode.ROUND_ROBIN:
            return await self.run_round_robin_async(rounds, use_intelligent_prompts)
        elif self.mode == OrchestrationMode.SEQUENTIAL:
            return await self.run_sequential_async(use_intelligent_prompts)
        elif self.mode == OrchestrationMode.ADAPTIVE:
            return await self.run_adaptive_discussion_async(max_rounds=rounds)
        else:
            raise ValueError(f"Unknown orchestration mode: {self.mode}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full shared conversation history in a serializable format"""
        history = []
        for msg in self.shared_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                history.append({"role": "system", "content": msg.content})
        return history
    
    def get_summary(self) -> Dict:
        """Get a summary of the orchestration session"""
        return {
            "session_id": self.session_id,
            "agent_types": self.agent_types,
            "mode": self.mode,
            "total_messages": len(self.shared_history),
            "agents": [
                {"type": agent_type, "role": agent.role}
                for agent_type, agent in self.agents.items()
            ]
        }
