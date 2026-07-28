from typing import List, Any
from uuid import UUID
from app.models.workspace import Workspace
from app.repositories.base import BaseRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

class WorkspaceRepository(BaseRepository[Workspace, WorkspaceCreate, WorkspaceUpdate]):
    def __init__(self, session: Any = None):
        super().__init__(Workspace, session)

    async def get_by_organization(self, organization_id: UUID) -> List[Workspace]:
        return await Workspace.filter(organization_id=organization_id).all()
