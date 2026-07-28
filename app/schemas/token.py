from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Token authentication response containing access token."""
    access_token: str = Field(..., description="JWT access token for bearer authentication.")
    token_type: str = Field(default="bearer", description="Token scheme type.")


class TokenPayload(BaseModel):
    """Parsed claims payload from a validated JWT token."""
    sub: str = Field(..., description="Subject (user UUID or identifier).")
    exp: int = Field(..., description="Expiration timestamp (Unix EPOCH).")
    iat: int = Field(..., description="Issued at timestamp (Unix EPOCH).")
    type: str = Field(..., description="Token type ('access' or 'refresh').")
    jti: str = Field(..., description="Unique JWT ID for token revocation tracking.")
