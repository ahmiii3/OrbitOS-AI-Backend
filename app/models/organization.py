import uuid
from tortoise import fields
from tortoise.models import Model

# Constants for roles
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_MEMBER = "member"

class Organization(Model):
    """Enterprise organization container representing a tenant."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=255)
    slug = fields.CharField(max_length=255, unique=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organizations"

    def __str__(self):
        return self.name


class OrganizationMember(Model):
    """Mapping of a user to an organization with a specific role."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    organization = fields.ForeignKeyField("models.Organization", related_name="memberships", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="memberships", on_delete=fields.CASCADE)
    role = fields.CharField(max_length=50, default=ROLE_MEMBER) # owner, admin, member
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organization_members"
        unique_together = (("organization", "user"),)

    def __str__(self):
        return f"{self.user_id} in {self.organization_id} as {self.role}"


class OrganizationInvitation(Model):
    """Pending invitation for a user to join an organization."""
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    organization = fields.ForeignKeyField("models.Organization", related_name="invitations", on_delete=fields.CASCADE)
    email = fields.CharField(max_length=255, index=True)
    role = fields.CharField(max_length=50, default=ROLE_MEMBER)
    token = fields.CharField(max_length=255, unique=True, index=True)
    invited_by = fields.ForeignKeyField("models.User", related_name="sent_invitations", on_delete=fields.CASCADE)
    status = fields.CharField(max_length=50, default="pending") # pending, accepted, expired, revoked
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "organization_invitations"

    def __str__(self):
        return f"Invite for {self.email} to {self.organization_id} ({self.role})"
