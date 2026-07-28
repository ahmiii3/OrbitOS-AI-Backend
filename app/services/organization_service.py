from uuid import UUID
from fastapi import HTTPException, status
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.schemas.organization import OrganizationCreate, AddMemberRequest

class OrganizationService:
    """Service for managing enterprise organizations and their members."""
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

        org = await self.org_repo.create(
            name=org_in.name,
            slug=org_in.slug
        )
        
        # Add owner member using the full User object
        await self.org_repo.add_member(
            organization_id=org.id,
            user=owner,
            role="owner"
        )
        return org

    async def get_user_organizations(self, user_id: UUID):
        return await self.org_repo.get_user_organizations(user_id)

    async def add_member(self, organization_id: UUID, member_req: AddMemberRequest):
        # Look up user
        user = await self.user_repo.get_by_email(member_req.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {member_req.email} not found"
            )
            
        # Check if already a member
        existing = await self.org_repo.get_member(organization_id, user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )
            
        return await self.org_repo.add_member(
            organization_id=organization_id,
            user=user,
            role=member_req.role
        )

    async def get_members(self, organization_id: UUID):
        return await self.org_repo.get_members(organization_id)
