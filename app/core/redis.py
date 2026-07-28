import fnmatch
import logging
from typing import Optional, Dict, List, Tuple, Any
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_pool: Optional[ConnectionPool] = None
_in_memory_store: Dict[str, str] = {}
_use_in_memory: bool = False


class InMemoryRedisClient:
    """Zero-dependency in-memory async Redis fallback for local development without Redis server."""

    def __init__(self) -> None:
        global _in_memory_store
        self.data = _in_memory_store

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        self.data[key] = str(value)
        return True

    async def incr(self, key: str) -> int:
        val = int(self.data.get(key, 0)) + 1
        self.data[key] = str(val)
        return val

    async def expire(self, key: str, time: int) -> bool:
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self.data:
                del self.data[k]
                count += 1
        return count

    async def scan(self, cursor: int = 0, match: str = "*", count: int = 10) -> Tuple[int, List[str]]:
        matching_keys = [k for k in self.data.keys() if fnmatch.fnmatch(k, match)]
        return 0, matching_keys

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        pass

    async def aclose(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass


class ResilientRedisClient:
    """Wrapper around async Redis client that automatically falls back to in-memory store if Redis is unreachable."""

    def __init__(self, real_client: Redis, fallback_client: InMemoryRedisClient):
        self.real_client = real_client
        self.fallback_client = fallback_client

    async def _execute_with_fallback(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        global _use_in_memory
        if _use_in_memory:
            return await getattr(self.fallback_client, method_name)(*args, **kwargs)
        try:
            return await getattr(self.real_client, method_name)(*args, **kwargs)
        except (RedisConnectionError, RedisTimeoutError, OSError) as exc:
            logger.warning(f"Redis connection failed ({exc}). Falling back to in-memory store for local development.")
            _use_in_memory = True
            return await getattr(self.fallback_client, method_name)(*args, **kwargs)

    async def get(self, key: str) -> Any:
        return await self._execute_with_fallback("get", key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> Any:
        return await self._execute_with_fallback("set", key, value, ex=ex)

    async def incr(self, key: str) -> Any:
        return await self._execute_with_fallback("incr", key)

    async def expire(self, key: str, time: int) -> Any:
        return await self._execute_with_fallback("expire", key, time)

    async def delete(self, *keys: str) -> Any:
        return await self._execute_with_fallback("delete", *keys)

    async def scan(self, cursor: int = 0, match: str = "*", count: int = 10) -> Any:
        return await self._execute_with_fallback("scan", cursor, match, count=count)

    async def ping(self) -> Any:
        return await self._execute_with_fallback("ping")

    async def close(self) -> None:
        if not _use_in_memory:
            try:
                await self.real_client.close()
            except Exception:
                pass

    async def aclose(self) -> None:
        if not _use_in_memory:
            try:
                await self.real_client.aclose()
            except Exception:
                pass


def get_redis_pool() -> ConnectionPool:
    """Get or initialize the async Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URI,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def get_redis() -> Any:
    """Get an async Redis client instance (resilient with in-memory fallback)."""
    pool = get_redis_pool()
    real_client = Redis(connection_pool=pool)
    fallback_client = InMemoryRedisClient()
    return ResilientRedisClient(real_client, fallback_client)


async def close_redis_pool() -> None:
    """Close all connections in the Redis pool (call during app shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        try:
            await _redis_pool.disconnect()
        except Exception:
            pass
        _redis_pool = None
