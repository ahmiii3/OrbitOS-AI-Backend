from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_active_user
from app.dependencies.services import get_organization_service
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse
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
