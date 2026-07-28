from typing import Any
from fastapi import Depends
from redis.asyncio import Redis
from app.dependencies.database import get_db
from app.dependencies.redis import get_redis_client
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.user_service import UserService


def get_user_repository(db: Any = Depends(get_db)) -> UserRepository:
    """Provide a UserRepository instance."""
    return UserRepository(db)


def get_email_service() -> EmailService:
    """Provide an EmailService instance."""
    return EmailService()


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
    redis_client: Redis = Depends(get_redis_client),
) -> AuthService:
    """Provide an AuthService instance with injected dependencies."""
    return AuthService(user_repo=user_repo, email_service=email_service, redis_client=redis_client)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
    redis_client: Redis = Depends(get_redis_client),
) -> UserService:
    """Provide a UserService instance with injected dependencies."""
    return UserService(user_repo=user_repo, email_service=email_service, redis_client=redis_client)
