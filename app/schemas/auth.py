from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    """Payload for registering a new user."""
    name: str = Field(..., min_length=2, max_length=100, description="The user's full name.")
    email: EmailStr = Field(..., description="The user's email address.")
    password: str = Field(..., min_length=8, description="The user's password (min 8 chars).")

class LoginRequest(BaseModel):
    """Payload for user login."""
    email: EmailStr = Field(..., description="The user's email address.")
    password: str = Field(..., description="The user's password.")

class MessageResponse(BaseModel):
    """Generic message response payload."""
    message: str = Field(..., description="A human-readable message.")

class ChangePasswordRequest(BaseModel):
    """Payload for an authenticated user to change their password."""
    old_password: str = Field(..., description="The current password.")
    new_password: str = Field(..., min_length=8, description="The new password (min 8 chars).")
