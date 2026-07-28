from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserCreate


class RegisterRequest(UserCreate):
    """Payload for new user registration."""
    pass


class VerifyEmailRequest(BaseModel):
    """Payload for verifying email with 6-digit confirmation code."""
    email: EmailStr = Field(..., description="The email address to verify.", examples=["john.doe@enterprise.com"])
    code: str = Field(..., min_length=6, max_length=6, description="The 6-digit verification code received via email.", examples=["482901"])


class LoginRequest(BaseModel):
    """Payload for email/password authentication."""
    email: EmailStr = Field(..., examples=["john.doe@enterprise.com"])
    password: str = Field(..., examples=["SecurePass!2026"])


class RefreshTokenRequest(BaseModel):
    """Payload for rotating access and refresh tokens."""
    refresh_token: str = Field(..., description="The current active refresh token.")


class ForgotPasswordRequest(BaseModel):
    """Payload for requesting a password reset email."""
    email: EmailStr = Field(..., examples=["john.doe@enterprise.com"])


class ResetPasswordRequest(BaseModel):
    """Payload for completing password reset with token."""
    token: str = Field(..., description="The secure reset token sent via email.")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The new password (at least 8 characters).",
        examples=["NewSecurePass!2026"],
    )


class ChangePasswordRequest(BaseModel):
    """Payload for changing password while authenticated."""
    current_password: str = Field(..., description="The user's current password.")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The new password (at least 8 characters).",
        examples=["NewSecurePass!2026"],
    )


class MessageResponse(BaseModel):
    """Generic status message response."""
    message: str = Field(..., examples=["Operation completed successfully."])
