import pytest
from httpx import AsyncClient
from tests.conftest import MockAsyncRedis

pytestmark = pytest.mark.asyncio


async def test_register_new_user(client: AsyncClient) -> None:
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alice Wonderland", "email": "alice@enterprise.com", "password": "StrongPassword123!"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Wonderland"
    assert data["email"] == "alice@enterprise.com"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test registration fails with an existing email address."""
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Bob", "email": "bob@enterprise.com", "password": "Password123!"}
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Bob Clone", "email": "bob@enterprise.com", "password": "Password123!"}
    )
    assert response.status_code == 409
    assert response.json()["error"] == "UserAlreadyExistsError"


async def test_login_success(client: AsyncClient) -> None:
    """Test successful authentication returning an access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Charlie", "email": "charlie@enterprise.com", "password": "Password123!"}
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@enterprise.com", "password": "Password123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Test authentication failure with incorrect password."""
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Dave", "email": "dave@enterprise.com", "password": "Password123!"}
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@enterprise.com", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "InvalidCredentialsError"
