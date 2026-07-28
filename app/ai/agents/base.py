from abc import ABC, abstractmethod
from typing import Any, Dict
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.orchestrator.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent(ABC):
    """
    Abstract Base Class for all OrbitOS AI specialized agents.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        # Every agent gets its own instance of the LLM provider
        self.llm = OpenAIProvider()
        
    @abstractmethod
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the agent's logic based on the current state.
        Returns a dictionary that will be merged into the AgentState.
        """
        pass
        
    def _build_system_prompt(self, state: AgentState) -> str:
        """Helper to build a system prompt with the overarching business goal."""
        base_prompt = f"You are the {self.name} for OrbitOS AI. {self.description}\n"
        goal = state.get('business_goal', 'None provided.')
        return f"{base_prompt}\nYour current overarching business goal is: {goal}"
