from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """Abstract base class for AI tools."""
    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool's functionality."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for OpenAI/Groq function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                }
            }
        }
