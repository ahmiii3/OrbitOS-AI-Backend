import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user properties shared across schemas."""
    name: str = Field(..., min_length=1, max_length=255, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["john.doe@enterprise.com"])


class UserCreate(UserBase):
    """Properties required to create/register a new user."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long.",
        examples=["SecurePass!2026"],
    )


class UserUpdate(BaseModel):
    """Properties allowable for a user profile update."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, examples=["John Smith"])
    email: Optional[EmailStr] = Field(None, examples=["john.smith@enterprise.com"])


class UserRead(UserBase):
    """Properties returned to client when reading user profile (excludes password)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str = Field(..., examples=["user"])
    is_active: bool = Field(..., examples=[True])
    email_verified: bool = Field(..., examples=[False])
    created_at: datetime
    updated_at: datetime


class UserInDB(UserRead):
    """Internal schema representing full user data from DB including password hash."""
    hashed_password: str
