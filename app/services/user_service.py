from redis.asyncio import Redis
from app.core import security
from app.core.config import settings
from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import ChangePasswordRequest, MessageResponse
from app.schemas.user import UserRead, UserUpdate
from app.services.email_service import EmailService


class UserService:
    """Service layer for user profile management and account security operations."""

    def __init__(self, user_repo: UserRepository, email_service: EmailService, redis_client: Redis):
        self.user_repo = user_repo
        self.email_service = email_service
        self.redis = redis_client

    async def get_current_user_profile(self, user: User) -> UserRead:
        """Return the profile schema for the authenticated user."""
        return UserRead.model_validate(user)

    async def update_profile(self, user: User, payload: UserUpdate) -> UserRead:
        """Update user profile information, triggering email verification if email address changes."""
        email_changed = False
        if payload.email and payload.email.lower() != user.email:
            existing_user = await self.user_repo.get_by_email(payload.email)
            if existing_user and existing_user.id != user.id:
                raise UserAlreadyExistsError(message="This email address is already in use by another account.")
            email_changed = True

        updated_user = await self.user_repo.update_profile(
            user,
            name=payload.name,
            email=payload.email,
        )

        if email_changed:
            token = security.generate_secure_token()
            redis_key = f"verify_email:{token}"
            ttl_seconds = settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS * 3600
            await self.redis.set(redis_key, str(updated_user.id), ex=ttl_seconds)

            await self.email_service.send_verification_email(
                to_email=updated_user.email,
                name=updated_user.name,
                token=token,
            )

        return UserRead.model_validate(updated_user)

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> MessageResponse:
        """Update authenticated user's password and revoke existing refresh tokens."""
        if not security.verify_password(payload.current_password, user.hashed_password):
            raise InvalidCredentialsError(message="The current password provided is incorrect.")

        new_hashed = security.hash_password(payload.new_password)
        await self.user_repo.update_password(user, new_hashed_password=new_hashed)

        # Revoke all active refresh tokens for this user upon password change
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=f"refresh_token:{user.id}:*", count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

        return MessageResponse(message="Your password has been changed successfully.")
