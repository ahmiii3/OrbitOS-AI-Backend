import uuid
from tortoise import fields
from tortoise.models import Model

class Document(Model):
    """Knowledge base document uploaded by a user."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    filename = fields.CharField(max_length=255)
    organization = fields.ForeignKeyField("models.Organization", related_name="documents", on_delete=fields.CASCADE)
    workspace = fields.ForeignKeyField("models.Workspace", related_name="documents", on_delete=fields.CASCADE)
    uploaded_by = fields.ForeignKeyField("models.User", related_name="documents", on_delete=fields.CASCADE)
    status = fields.CharField(max_length=50, default="QUEUED")  # QUEUED, PROCESSING, INDEXING, COMPLETED, FAILED
    version = fields.IntField(default=1)
    is_latest = fields.BooleanField(default=True)
    checksum = fields.CharField(max_length=64, index=True)  # SHA256 checksum
    parent_document = fields.ForeignKeyField("models.Document", null=True, related_name="versions", on_delete=fields.SET_NULL)
    visibility = fields.CharField(max_length=50, default="team")  # public, team, private
    meta_attributes = fields.JSONField(null=True)  # Holds dynamic enrichments like author, tags, language
    upload_time = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "documents"

    def __str__(self):
        return f"{self.filename} (v{self.version})"


class DocumentChunk(Model):
    """Text chunk extracted from a document for RAG."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    document = fields.ForeignKeyField("models.Document", related_name="chunks", on_delete=fields.CASCADE)
    chunk_index = fields.IntField()
    content = fields.TextField()
    content_checksum = fields.CharField(max_length=64, index=True)  # SHA-256 chunk hash
    meta_attributes = fields.JSONField(null=True)  # Page numbers, headers, links

    class Meta:
        table = "document_chunks"

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.filename}"
