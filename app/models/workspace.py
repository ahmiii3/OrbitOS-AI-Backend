import uuid
from tortoise import fields
from tortoise.models import Model

class Workspace(Model):
    """Operational workspace within an organization for distinct teams or projects."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    organization = fields.ForeignKeyField("models.Organization", related_name="workspaces", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "workspaces"

    def __str__(self):
        return self.name
