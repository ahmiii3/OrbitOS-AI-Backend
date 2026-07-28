import uuid
from typing import Any
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from app.core import security
from app.core.config import settings
from app.core.exceptions import AccountDisabledError, EmailNotVerifiedError, InvalidTokenError
from app.dependencies.database import get_db
from app.dependencies.redis import get_redis_client
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scheme_name="JWT Bearer Authentication",
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Any = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> User:
    """Validate access token, check blacklist, and return current authenticated user model."""
    try:
        payload = security.decode_token(token)
    except InvalidTokenError as exc:
        raise InvalidTokenError(message="Invalid or expired access token.") from exc

    if payload.get("type") != "access":
        raise InvalidTokenError(message="Invalid token type. Expected an access token.")

    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis.get(f"blacklist_token:{jti}")
        if is_blacklisted:
            raise InvalidTokenError(message="This access token has been revoked or logged out.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise InvalidTokenError(message="Token subject missing.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise InvalidTokenError(message="Malformed token subject ID.") from exc

    user_repo = UserRepository(db)
    user = await user_repo.get(user_uuid)
    if not user:
        raise InvalidTokenError(message="User associated with this token no longer exists.")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user account is active."""
    if not current_user.is_active:
        raise AccountDisabledError()
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure the authenticated user has verified their email address."""
    if not current_user.email_verified:
        raise EmailNotVerifiedError()
    return current_user
