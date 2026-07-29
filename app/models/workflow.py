from tortoise import fields
import uuid
from enum import Enum
from tortoise.models import Model
import uuid

class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class WorkflowExecution(Model):
    """Tracks the execution of long-running AI workflows."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    workspace = fields.ForeignKeyField("models.Workspace", related_name="workflows", on_delete=fields.CASCADE)
    status = fields.CharEnumField(WorkflowStatus, default=WorkflowStatus.PENDING)
    title = fields.CharField(max_length=255, null=True, default="New Workflow")
    messages = fields.JSONField(default=list)
    input_data = fields.JSONField(null=True)
    result_data = fields.JSONField(null=True)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "workflow_executions"
