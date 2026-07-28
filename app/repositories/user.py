import uuid
from typing import Optional, Any
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for user data operations in PostgreSQL (Tortoise ORM)."""

    def __init__(self, session: Any = None):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by their email address (case-insensitive)."""
        return await User.filter(email__iexact=email).first()

    async def create_user(self, name: str, email: str, hashed_password: str, role: str = "user") -> User:
        """Create and store a new user in the database."""
        return await User.create(
            name=name,
            email=email.lower(),
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            email_verified=False,
        )

    async def set_email_verified(self, user: User, verified: bool = True) -> User:
        """Update user's email verification status."""
        user.email_verified = verified
        await user.save()
        return user

    async def update_password(self, user: User, new_hashed_password: str) -> User:
        """Update a user's hashed password."""
        user.hashed_password = new_hashed_password
        await user.save()
        return user

    async def update_profile(self, user: User, name: Optional[str] = None, email: Optional[str] = None) -> User:
        """Update a user's basic profile fields."""
        if name is not None:
            user.name = name
        if email is not None and email.lower() != user.email:
            user.email = email.lower()
            user.email_verified = False  # Require verification if email changes
        await user.save()
        return user
