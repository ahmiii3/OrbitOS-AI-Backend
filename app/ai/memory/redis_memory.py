import json
from typing import Dict, Any, List
from redis.asyncio import Redis
from app.ai.memory.base import BaseMemory

class RedisMemory(BaseMemory):
    """Simple Redis-backed memory for agent context and workflow state."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 60 * 60 * 24 * 7  # 7 days

    def _context_key(self, session_id: str) -> str:
        return f"orbitos:memory:context:{session_id}"
        
    def _history_key(self, session_id: str) -> str:
        return f"orbitos:memory:history:{session_id}"

    async def save_context(self, session_id: str, context: Dict[str, Any]):
        """Saves workflow state and shared agent context."""
        key = self._context_key(session_id)
        # Merge with existing context if it exists
        existing = await self.get_context(session_id)
        existing.update(context)
        
        await self.redis.set(key, json.dumps(existing), ex=self.ttl)

    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieves workflow state."""
        key = self._context_key(session_id)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return {}

    async def add_history(self, session_id: str, message: Dict[str, str]):
        """Adds a single message to the execution history."""
        key = self._history_key(session_id)
        await self.redis.rpush(key, json.dumps(message))
        await self.redis.expire(key, self.ttl)

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves full execution history."""
        key = self._history_key(session_id)
        raw_messages = await self.redis.lrange(key, 0, -1)
        return [json.loads(m) for m in raw_messages]
