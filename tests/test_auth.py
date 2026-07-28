import pytest
from httpx import AsyncClient
from tests.conftest import MockAsyncRedis

pytestmark = pytest.mark.asyncio


async def test_register_user(client: AsyncClient) -> None:
    """Test user registration endpoint creates an unverified account."""
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@enterprise.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@enterprise.com"
    assert data["email_verified"] is False
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test registering with an existing email returns 409 Conflict."""
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@enterprise.com",
        "password": "SecurePassword123!",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["error"] == "UserAlreadyExistsError"


async def test_login_unverified_email(client: AsyncClient) -> None:
    """Test login fails with 403 when email is not verified."""
    payload = {
        "name": "Jane Doe",
        "email": "unverified@enterprise.com",
        "password": "SecurePassword123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    login_payload = {
        "email": "unverified@enterprise.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 403
    assert response.json()["error"] == "EmailNotVerifiedError"


async def test_verify_email_and_login(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test email verification flow with 6-digit code and subsequent successful login."""
    payload = {
        "name": "John Verified",
        "email": "john.verified@enterprise.com",
        "password": "SecurePassword123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    # Find 6-digit code in mock Redis
    code = None
    for key in mock_redis.data.keys():
        if key.startswith("verify_email:"):
            code = key.split("verify_email:")[1]
            break
    assert code is not None
    assert len(code) == 6  # Must be a 6-digit code

    # Verify email via POST with code
    response = await client.post("/api/v1/auth/verify-email", json={
        "email": "john.verified@enterprise.com",
        "code": code,
    })
    assert response.status_code == 200
    assert response.json()["email_verified"] is True

    # Login
    login_payload = {
        "email": "john.verified@enterprise.com",
        "password": "SecurePassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"


async def test_refresh_token_rotation(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test refresh token rotation and revocation of reused tokens."""
    # Register and verify
    await client.post("/api/v1/auth/register", json={"name": "Rotator", "email": "rotate@enterprise.com", "password": "Password123!"})
    code = [k.split("verify_email:")[1] for k in mock_redis.data.keys() if k.startswith("verify_email:")][0]
    await client.post("/api/v1/auth/verify-email", json={"email": "rotate@enterprise.com", "code": code})

    # Login
    login_res = await client.post("/api/v1/auth/login", json={"email": "rotate@enterprise.com", "password": "Password123!"})
    refresh_token = login_res.json()["refresh_token"]

    # Refresh tokens
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert new_tokens["access_token"] != login_res.json()["access_token"]
    assert new_tokens["refresh_token"] != refresh_token

    # Attempt reuse of old refresh token (must fail with 401)
    reuse_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_res.status_code == 401
    assert reuse_res.json()["error"] == "InvalidTokenError"


async def test_logout_blacklists_access_token(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test logout revokes tokens and blocks access to authenticated endpoints."""
    await client.post("/api/v1/auth/register", json={"name": "Logout User", "email": "logout@enterprise.com", "password": "Password123!"})
    code = [k.split("verify_email:")[1] for k in mock_redis.data.keys() if k.startswith("verify_email:")][0]
    await client.post("/api/v1/auth/verify-email", json={"email": "logout@enterprise.com", "code": code})

    login_res = await client.post("/api/v1/auth/login", json={"email": "logout@enterprise.com", "password": "Password123!"})
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200

    # Logout
    logout_res = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token}, headers=headers)
    assert logout_res.status_code == 200

    # Access endpoint after logout (must fail with 401)
    me_after_logout = await client.get("/api/v1/users/me", headers=headers)
    assert me_after_logout.status_code == 401
    assert "revoked" in me_after_logout.json()["message"].lower()


async def test_forgot_and_reset_password(client: AsyncClient, mock_redis: MockAsyncRedis) -> None:
    """Test forgot password request and resetting password with token."""
    await client.post("/api/v1/auth/register", json={"name": "Reset User", "email": "reset@enterprise.com", "password": "OldPassword123!"})
    code_verify = [k.split("verify_email:")[1] for k in mock_redis.data.keys() if k.startswith("verify_email:")][0]
    await client.post("/api/v1/auth/verify-email", json={"email": "reset@enterprise.com", "code": code_verify})

    # Forgot password
    forgot_res = await client.post("/api/v1/auth/forgot-password", json={"email": "reset@enterprise.com"})
    assert forgot_res.status_code == 200

    # Find reset token
    reset_token = [k.split("reset_password:")[1] for k in mock_redis.data.keys() if k.startswith("reset_password:")][0]

    # Reset password
    reset_res = await client.post("/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "NewPassword123!"})
    assert reset_res.status_code == 200

    # Login with old password (fails)
    old_login = await client.post("/api/v1/auth/login", json={"email": "reset@enterprise.com", "password": "OldPassword123!"})
    assert old_login.status_code == 401

    # Login with new password (succeeds)
    new_login = await client.post("/api/v1/auth/login", json={"email": "reset@enterprise.com", "password": "NewPassword123!"})
    assert new_login.status_code == 200
