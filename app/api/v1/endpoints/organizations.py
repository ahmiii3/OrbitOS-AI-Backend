from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_active_user, verify_org_membership
from app.dependencies.services import get_organization_service
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse, AddMemberRequest, OrganizationMemberResponse
from app.services.organization_service import OrganizationService

router = APIRouter()

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
)
async def create_organization(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
) -> OrganizationResponse:
    org = await org_service.create_organization(org_in, current_user.id)
    return OrganizationResponse.model_validate(org)

@router.get(
    "",
    summary="List Organizations",
)
async def list_organizations(
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    orgs = await org_service.get_user_organizations(current_user.id)
    return [OrganizationResponse.model_validate(o) for o in orgs]

@router.post(
    "/{org_id}/members",
    response_model=OrganizationMemberResponse,
    summary="Add Member",
    include_in_schema=False,
)
async def add_member(
    org_id: str,
    member_req: AddMemberRequest,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    await verify_org_membership(org_id, current_user, required_role="admin")
    new_member = await org_service.add_member(UUID(org_id), member_req)
    return OrganizationMemberResponse.model_validate(new_member)

@router.get(
    "/{org_id}/members",
    summary="List Members",
    include_in_schema=False,
)
async def list_members(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
):
    await verify_org_membership(org_id, current_user)
    members = await org_service.get_members(UUID(org_id))
    return [OrganizationMemberResponse.model_validate(m) for m in members]
