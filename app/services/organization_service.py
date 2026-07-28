from uuid import UUID
from fastapi import HTTPException, status
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.schemas.organization import OrganizationCreate

class OrganizationService:
    """Service for managing enterprise organizations."""
    def __init__(
        self,
        org_repo: OrganizationRepository,
        user_repo: UserRepository
    ):
        self.org_repo = org_repo
        self.user_repo = user_repo

    async def create_organization(self, org_in: OrganizationCreate, owner_id: UUID):
        # Verify slug uniqueness
        existing = await self.org_repo.get_by_slug(org_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this slug already exists"
            )
            
        owner = await self.user_repo.get(owner_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Owner user not found"
            )

        org = await self.org_repo.create({
            "name": org_in.name,
            "slug": org_in.slug,
            "owner_id": owner.id
        })
        return org

    async def get_user_organizations(self, user_id: UUID):
        return await self.org_repo.get_user_organizations(user_id)
