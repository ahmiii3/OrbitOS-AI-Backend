import uuid
from tortoise import fields
from tortoise.models import Model

class Organization(Model):
    """Enterprise organization container representing a tenant."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=255)
    slug = fields.CharField(max_length=255, unique=True, index=True)
    
    # Directly link the organization to the single business owner
    owner = fields.ForeignKeyField("models.User", related_name="organizations", on_delete=fields.CASCADE)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organizations"

    def __str__(self):
        return self.name
