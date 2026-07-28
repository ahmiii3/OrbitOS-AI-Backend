import pytest
from httpx import AsyncClient
from tests.conftest import MockAsyncRedis

pytestmark = pytest.mark.asyncio


async def _register_verify_login(client: AsyncClient, mock_redis: MockAsyncRedis, email: str = "user@enterprise.com", password: str = "Password123!") -> str:
    """Helper to register, verify, and login a test user, returning the access token."""
    await client.post("/api/v1/auth/register", json={"name": "Test User", "email": email, "password": password})
    tokens = [k.split("verify_email:")[1] for k in mock_redis.data.keys() if k.startswith("verify_email:")]
    await client.get(f"/api/v1/auth/verify-email?token={tokens[0]}")
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login_res.json()["access_token"]


async def test_get_current_user_profile(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test retrieving authenticated user profile via /users/me."""
    access_token = await _register_verify_login(client, mock_redis, "profile@enterprise.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@enterprise.com"
    assert data["name"] == "Test User"
    assert data["email_verified"] is True


async def test_get_profile_unauthorized(client: AsyncClient) -> None:
    """Test accessing /users/me without an access token returns 401 Unauthorized."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_update_user_profile_name(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test updating user profile name."""
    access_token = await _register_verify_login(client, mock_redis, "updatename@enterprise.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Updated Name"}
    response = await client.put("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["email"] == "updatename@enterprise.com"
    assert response.json()["email_verified"] is True


async def test_update_user_email_triggers_verification(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test updating email address resets email_verified status to False."""
    access_token = await _register_verify_login(client, mock_redis, "oldemail@enterprise.com")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Clear existing verify keys
    verify_keys = [k for k in mock_redis.data.keys() if k.startswith("verify_email:")]
    await mock_redis.delete(*verify_keys)

    payload = {"email": "newemail@enterprise.com"}
    response = await client.put("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "newemail@enterprise.com"
    assert response.json()["email_verified"] is False

    # Check that a new verification token was generated in Redis
    new_verify_keys = [k for k in mock_redis.data.keys() if k.startswith("verify_email:")]
    assert len(new_verify_keys) == 1


async def test_change_password_endpoint(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test changing password while authenticated."""
    access_token = await _register_verify_login(client, mock_redis, "changepw@enterprise.com", "OldPassword123!")
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {
        "current_password": "OldPassword123!",
        "new_password": "NewSecurePassword123!",
    }
    response = await client.post("/api/v1/auth/change-password", json=payload, headers=headers)
    assert response.status_code == 200

    # Test login with old password fails
    old_login = await client.post("/api/v1/auth/login", json={"email": "changepw@enterprise.com", "password": "OldPassword123!"})
    assert old_login.status_code == 401

    # Test login with new password succeeds
    new_login = await client.post("/api/v1/auth/login", json={"email": "changepw@enterprise.com", "password": "NewSecurePassword123!"})
    assert new_login.status_code == 200
