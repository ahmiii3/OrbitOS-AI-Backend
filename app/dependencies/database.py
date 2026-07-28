from typing import AsyncGenerator, Any


async def get_db() -> AsyncGenerator[Any, None]:
    """Dependency generator (no-op in Tortoise ORM Active Record pattern)."""
    yield None
