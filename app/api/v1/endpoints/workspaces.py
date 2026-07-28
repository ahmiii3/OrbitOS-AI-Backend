from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_active_user, verify_org_membership
from app.dependencies.services import get_workspace_service
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter()

@router.post(
    "/organizations/{org_id}/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workspace",
)
async def create_workspace(
    org_id: str,
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service)
) -> WorkspaceResponse:
    await verify_org_membership(org_id, current_user)
    workspace = await workspace_service.create_workspace(UUID(org_id), workspace_in)
    return WorkspaceResponse.model_validate(workspace)

@router.get(
    "/organizations/{org_id}/workspaces",
    summary="List Workspaces",
)
async def list_workspaces(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    await verify_org_membership(org_id, current_user)
    workspaces = await workspace_service.get_workspaces(UUID(org_id))
    return [WorkspaceResponse.model_validate(w) for w in workspaces]
