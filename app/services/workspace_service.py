from uuid import UUID
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate

class WorkspaceService:
    """Service for managing operational workspaces within organizations."""
    def __init__(
        self,
        workspace_repo: WorkspaceRepository
    ):
        self.workspace_repo = workspace_repo

    async def create_workspace(self, org_id: UUID, workspace_in: WorkspaceCreate):
        return await self.workspace_repo.create({
            "organization_id": org_id,
            "name": workspace_in.name,
            "description": workspace_in.description
        })

    async def get_workspaces(self, org_id: UUID):
        return await self.workspace_repo.get_by_organization(org_id)
