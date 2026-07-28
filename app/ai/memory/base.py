from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseMemory(ABC):
    """Abstract base class for Agent shared memory."""

    @abstractmethod
    async def save_context(self, session_id: str, context: Dict[str, Any]):
        pass

    @abstractmethod
    async def get_context(self, session_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        pass
