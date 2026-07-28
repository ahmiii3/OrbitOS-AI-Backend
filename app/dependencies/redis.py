from typing import AsyncGenerator
from redis.asyncio import Redis
from app.core.redis import get_redis


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Dependency generator providing an async Redis connection from the pool."""
    client = await get_redis()
    try:
        yield client
    finally:
        await client.aclose()
