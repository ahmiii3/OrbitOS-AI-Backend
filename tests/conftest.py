import asyncio
import fnmatch
from typing import AsyncGenerator, Dict, List, Tuple, Any
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise
from app.dependencies.database import get_db
from app.dependencies.redis import get_redis_client
from app.main import app


class MockAsyncRedis:
    """Zero-dependency in-memory async Redis mock for testing token blacklisting, rotation, and rate limits."""

    def __init__(self) -> None:
        self.data: Dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    """Create in-memory SQLite database before each test and drop afterwards."""
    await Tortoise.close_connections()
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models.user"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture(scope="function")
async def mock_redis() -> MockAsyncRedis:
    """Provide a fresh instance of the MockAsyncRedis client per test."""
    return MockAsyncRedis()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[Any, None]:
    """Provide a dummy session fixture for compatibility."""
    yield None


@pytest_asyncio.fixture(scope="function")
async def client(db_session: Any, mock_redis: MockAsyncRedis) -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous HTTP test client with overridden database and Redis dependencies."""

    async def override_get_db() -> AsyncGenerator[Any, None]:
        yield db_session

    async def override_get_redis_client() -> AsyncGenerator[MockAsyncRedis, None]:
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
