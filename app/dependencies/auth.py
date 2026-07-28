import uuid
from typing import Any
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from app.core import security
from app.core.config import settings
from app.core.exceptions import AccountDisabledError, EmailNotVerifiedError, InvalidTokenError
from app.dependencies.database import get_db
from app.dependencies.redis import get_redis_client
from app.models.user import User
from app.repositories.user import UserRepository

security_scheme = HTTPBearer(scheme_name="JWT Bearer Token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Any = Depends(get_db),
) -> User:
    """Validate access token and return current authenticated user model."""
    token = credentials.credentials
    try:
        payload = security.decode_token(token)
    except InvalidTokenError as exc:
        raise InvalidTokenError(message="Invalid or expired access token.") from exc

    if payload.get("type") != "access":
        raise InvalidTokenError(message="Invalid token type. Expected an access token.")

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

ROLE_HIERARCHY = {
    "viewer": 10,
    "member": 20,
    "manager": 50,
    "admin": 80,
    "owner": 100
}

async def verify_org_membership(
    org_id: str, 
    user: User, 
    required_role: str = None
):
    """
    Dependency helper to check if the current user owns the specified organization.
    """
    from fastapi import HTTPException, status
    from app.models.organization import Organization

    org = await Organization.filter(id=org_id, owner_id=user.id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not the owner of this organization"
        )
    return org


async def verify_workspace_access(workspace_id: str, user: User):
    from fastapi import HTTPException, status
    from app.models.workspace import Workspace

    workspace = await Workspace.filter(id=workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    await verify_org_membership(workspace.organization_id, user)
    return workspace
