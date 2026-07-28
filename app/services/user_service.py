from app.core import security
from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import ChangePasswordRequest, MessageResponse
from app.schemas.user import UserRead, UserUpdate


class UserService:
    """Service layer for user profile management and account security operations."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_current_user_profile(self, user: User) -> UserRead:
        """Return the profile schema for the authenticated user."""
        return UserRead.model_validate(user)

    async def update_profile(self, user: User, payload: UserUpdate) -> UserRead:
        """Update user profile information."""
        if payload.email and payload.email.lower() != user.email:
            existing_user = await self.user_repo.get_by_email(payload.email)
            if existing_user and existing_user.id != user.id:
                raise UserAlreadyExistsError(message="This email address is already in use by another account.")

        updated_user = await self.user_repo.update_profile(
            user,
            name=payload.name,
            email=payload.email,
        )

        return UserRead.model_validate(updated_user)

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> MessageResponse:
        """Update authenticated user's password."""
        # Note: the schema defines old_password, but previous logic used current_password. We should match the schema: old_password
        if not security.verify_password(payload.old_password, user.hashed_password):
            raise InvalidCredentialsError(message="The current password provided is incorrect.")

        new_hashed = security.hash_password(payload.new_password)
        await self.user_repo.update_password(user, new_hashed_password=new_hashed)

        return MessageResponse(message="Your password has been changed successfully.")
