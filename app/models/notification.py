from tortoise import fields
from tortoise.models import Model
import uuid

class Notification(Model):
    """System and workflow notifications for users."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="notifications", on_delete=fields.CASCADE)
    title = fields.CharField(max_length=255)
    message = fields.TextField()
    is_read = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"

    def __str__(self):
        return f"{self.title} ({'Read' if self.is_read else 'Unread'})"
