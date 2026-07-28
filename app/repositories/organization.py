from typing import Optional, List, Any
from uuid import UUID
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    def __init__(self, session: Any = None):
        super().__init__(Organization, session)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        return await Organization.filter(slug=slug).first()

    async def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        memberships = await OrganizationMember.filter(user_id=user_id).prefetch_related("organization")
        return [m.organization for m in memberships]

    async def add_member(self, organization_id: UUID, user: User, role: str) -> OrganizationMember:
        member = await OrganizationMember.create(
            organization_id=organization_id,
            user=user,
            role=role
        )
        # Assign in memory to prevent lazy relation loading errors in Pydantic
        member.user = user
        return member

    async def get_member(self, organization_id: UUID, user_id: UUID) -> Optional[OrganizationMember]:
        return await OrganizationMember.filter(
            organization_id=organization_id,
            user_id=user_id
        ).first()

    async def remove_member(self, organization_id: UUID, user_id: UUID) -> bool:
        deleted = await OrganizationMember.filter(
            organization_id=organization_id,
            user_id=user_id
        ).delete()
        return deleted > 0

    async def get_members(self, organization_id: UUID) -> List[OrganizationMember]:
        return await OrganizationMember.filter(
            organization_id=organization_id
        ).prefetch_related("user")
