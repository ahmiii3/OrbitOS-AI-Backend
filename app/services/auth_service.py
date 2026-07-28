import uuid
from typing import Optional
from app.core import security
from app.core.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.token import TokenResponse
from app.schemas.user import UserRead


class AuthService:
    """Service layer orchestrating simplified authentication workflows."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, payload: RegisterRequest) -> UserRead:
        """Register a new user account."""
        existing_user = await self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise UserAlreadyExistsError()

        hashed_pw = security.hash_password(payload.password)
        # We can just auto-verify email for simplicity since verification is removed
        user = await self.user_repo.create_user(
            name=payload.name,
            email=payload.email,
            hashed_password=hashed_pw,
        )
        
        # Auto-verify email to allow login immediately
        user = await self.user_repo.set_email_verified(user, verified=True)
        return UserRead.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Authenticate user credentials and issue an access token."""
        user = await self.user_repo.get_by_email(payload.email)
        if not user or not security.verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountDisabledError()

        access_token = security.create_access_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
