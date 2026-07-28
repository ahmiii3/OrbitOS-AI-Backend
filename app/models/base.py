import uuid
from tortoise.models import Model
from tortoise import fields


class BaseModel(Model):
    """Abstract base model with standard UUID primary key and audit timestamps."""
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True
