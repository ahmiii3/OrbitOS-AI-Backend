import os
from typing import List, Dict, Any
from app.ai.providers.base import BaseLLMProvider
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider for LLM inference."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment or settings.")
        
        self.model = model
        self.client = ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=0.7
        )

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Any]:
        lc_messages = []
        for m in messages:
            if m["role"] == "system":
                lc_messages.append(SystemMessage(content=m["content"]))
            elif m["role"] == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))
        return lc_messages

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using OpenAI."""
        lc_messages = self._convert_messages(messages)
        response = await self.client.ainvoke(lc_messages, **kwargs)
        return response.content
        
    async def generate_structured(self, messages: List[Dict[str, str]], schema: Any, **kwargs) -> Any:
        """Generate a structured response matching the Pydantic schema."""
        lc_messages = self._convert_messages(messages)
        structured_client = self.client.with_structured_output(schema)
        response = await structured_client.ainvoke(lc_messages, **kwargs)
        return response

    async def stream(self, messages: List[Dict[str, str]], **kwargs):
        """Stream response using OpenAI."""
        lc_messages = self._convert_messages(messages)
        async for chunk in self.client.astream(lc_messages, **kwargs):
            yield chunk.content
