from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM based on messages."""
        pass

    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], **kwargs):
        """Stream a response from the LLM."""
        pass
