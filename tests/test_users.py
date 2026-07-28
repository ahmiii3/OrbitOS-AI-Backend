import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _register_and_login(client: AsyncClient, email: str = "user@enterprise.com", password: str = "Password123!") -> str:
    """Helper to register and login a test user, returning the access token."""
    await client.post("/api/v1/auth/register", json={"name": "Test User", "email": email, "password": password})
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login_res.json()["access_token"]


async def test_get_current_user_profile(client: AsyncClient) -> None:
    """Test retrieving authenticated user profile via /users/me."""
    access_token = await _register_and_login(client, "profile@enterprise.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@enterprise.com"
    assert data["name"] == "Test User"


async def test_get_profile_unauthorized(client: AsyncClient) -> None:
    """Test accessing /users/me without an access token returns 401 Unauthorized."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_update_user_profile_name(client: AsyncClient) -> None:
    """Test updating user profile name."""
    access_token = await _register_and_login(client, "updatename@enterprise.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Updated Name"}
    response = await client.put("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["email"] == "updatename@enterprise.com"


async def test_update_user_email(client: AsyncClient) -> None:
    """Test updating user profile email."""
    access_token = await _register_and_login(client, "oldemail@enterprise.com")
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {"email": "newemail@enterprise.com"}
    response = await client.put("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "newemail@enterprise.com"
