from typing import Optional, List, Any
from uuid import UUID
from app.models.organization import Organization
from app.repositories.base import BaseRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    def __init__(self, session: Any = None):
        super().__init__(Organization, session)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        return await Organization.filter(slug=slug).first()

    async def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        return await Organization.filter(owner_id=user_id).all()
