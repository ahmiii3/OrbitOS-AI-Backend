import random
import uuid
from typing import Optional
from redis.asyncio import Redis
from app.core import security
from app.core.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.repositories.user import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.schemas.token import TokenResponse
from app.schemas.user import UserRead
from app.services.email_service import EmailService


class AuthService:
    """Service layer orchestrating authentication workflows, token management, and email notifications."""

    def __init__(self, user_repo: UserRepository, email_service: EmailService, redis_client: Redis):
        self.user_repo = user_repo
        self.email_service = email_service
        self.redis = redis_client

    async def register(self, payload: RegisterRequest) -> UserRead:
        """Register a new user account and dispatch a verification email."""
        existing_user = await self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise UserAlreadyExistsError()

        hashed_pw = security.hash_password(payload.password)
        user = await self.user_repo.create_user(
            name=payload.name,
            email=payload.email,
            hashed_password=hashed_pw,
        )

        # Generate 6-digit verification code stored in Redis
        code = f"{random.randint(100000, 999999)}"
        redis_key = f"verify_email:{code}"
        ttl_seconds = settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS * 3600
        await self.redis.set(redis_key, str(user.id), ex=ttl_seconds)

        # Send verification code via email
        await self.email_service.send_verification_email(
            to_email=user.email,
            name=user.name,
            code=code,
        )

        return UserRead.model_validate(user)

    async def verify_email(self, code: str) -> UserRead:
        """Validate a 6-digit email verification code and activate verified status."""
        redis_key = f"verify_email:{code}"
        user_id_str = await self.redis.get(redis_key)
        if not user_id_str:
            raise InvalidTokenError(message="Invalid or expired verification code.")

        user = await self.user_repo.get(uuid.UUID(user_id_str))
        if not user:
            raise UserNotFoundError()

        if not user.email_verified:
            user = await self.user_repo.set_email_verified(user, verified=True)

        await self.redis.delete(redis_key)
        return UserRead.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Authenticate user credentials and issue rotated access/refresh JWTs."""
        user = await self.user_repo.get_by_email(payload.email)
        if not user or not security.verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountDisabledError()
        if not user.email_verified:
            raise EmailNotVerifiedError()

        access_token = security.create_access_token(subject=user.id)
        refresh_token = security.create_refresh_token(subject=user.id)

        # Decode refresh token to get JTI and store in Redis whitelist
        refresh_payload = security.decode_token(refresh_token)
        jti = refresh_payload["jti"]
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        redis_key = f"refresh_token:{user.id}:{jti}"
        await self.redis.set(redis_key, "active", ex=ttl_seconds)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Rotate JWT refresh token and issue a fresh access token."""
        try:
            payload = security.decode_token(refresh_token)
        except InvalidTokenError as exc:
            raise InvalidTokenError(message="Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise InvalidTokenError(message="Invalid token type. Expected a refresh token.")

        user_id_str = payload["sub"]
        jti = payload["jti"]
        redis_key = f"refresh_token:{user_id_str}:{jti}"

        is_valid = await self.redis.get(redis_key)
        if not is_valid:
            raise InvalidTokenError(message="Refresh token has been revoked or already used.")

        user = await self.user_repo.get(uuid.UUID(user_id_str))
        if not user or not user.is_active:
            raise AccountDisabledError()
        if not user.email_verified:
            raise EmailNotVerifiedError()

        # Invalidate old refresh token (Token Rotation)
        await self.redis.delete(redis_key)

        new_access_token = security.create_access_token(subject=user.id)
        new_refresh_token = security.create_refresh_token(subject=user.id)

        new_payload = security.decode_token(new_refresh_token)
        new_jti = new_payload["jti"]
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.set(f"refresh_token:{user.id}:{new_jti}", "active", ex=ttl_seconds)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def logout(self, refresh_token: str, access_token: Optional[str] = None) -> MessageResponse:
        """Invalidate the refresh token and optionally blacklist the access token."""
        try:
            payload = security.decode_token(refresh_token)
            if payload.get("type") == "refresh":
                user_id_str = payload["sub"]
                jti = payload["jti"]
                await self.redis.delete(f"refresh_token:{user_id_str}:{jti}")
        except Exception:
            pass  # Even if token is already expired or malformed, proceed to blacklist access token

        if access_token:
            try:
                access_payload = security.decode_token(access_token)
                access_jti = access_payload.get("jti")
                if access_jti:
                    # Blacklist access token for 15 minutes (or its remaining TTL)
                    await self.redis.set(f"blacklist_token:{access_jti}", "revoked", ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
            except Exception:
                pass

        return MessageResponse(message="Successfully logged out.")

    async def forgot_password(self, payload: ForgotPasswordRequest) -> MessageResponse:
        """Initiate password reset workflow by explicitly checking user existence."""
        user = await self.user_repo.get_by_email(payload.email)
        if not user:
            raise UserNotFoundError(message="We could not find an account associated with this email address.")
        if not user.is_active:
            raise AccountDisabledError(message="This account has been disabled and cannot request a password reset.")

        token = security.generate_secure_token()
        redis_key = f"reset_password:{token}"
        ttl_seconds = settings.EMAIL_RESET_TOKEN_EXPIRE_MINUTES * 60
        await self.redis.set(redis_key, str(user.id), ex=ttl_seconds)

        await self.email_service.send_password_reset_email(
            to_email=user.email,
            name=user.name,
            token=token,
        )

        return MessageResponse(
            message="Password reset instructions have been successfully sent to your email address."
        )

    async def reset_password(self, payload: ResetPasswordRequest) -> MessageResponse:
        """Complete password reset with a valid token and revoke active sessions."""
        redis_key = f"reset_password:{payload.token}"
        user_id_str = await self.redis.get(redis_key)
        if not user_id_str:
            raise InvalidTokenError(message="Invalid or expired password reset token.")

        user = await self.user_repo.get(uuid.UUID(user_id_str))
        if not user:
            raise UserNotFoundError()

        hashed_pw = security.hash_password(payload.new_password)
        await self.user_repo.update_password(user, new_hashed_password=hashed_pw)

        # Invalidate reset token
        await self.redis.delete(redis_key)

        # Revoke all active refresh tokens for this user for security
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=f"refresh_token:{user.id}:*", count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

        return MessageResponse(message="Your password has been reset successfully. Please log in with your new password.")
