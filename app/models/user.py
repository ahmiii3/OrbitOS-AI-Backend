from tortoise import fields
from app.models.base import BaseModel


class User(BaseModel):
    """User entity model in PostgreSQL (Tortoise ORM)."""
    name = fields.CharField(max_length=255, null=False)
    email = fields.CharField(max_length=255, unique=True, db_index=True, null=False)
    hashed_password = fields.CharField(max_length=255, null=False)
    role = fields.CharField(max_length=50, default="user", null=False)
    is_active = fields.BooleanField(default=True, null=False)
    email_verified = fields.BooleanField(default=False, null=False)

    class Meta:
        table = "users"
        