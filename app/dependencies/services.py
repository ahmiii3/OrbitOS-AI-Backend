from typing import Any
from fastapi import Depends
from app.dependencies.database import get_db
from app.repositories.user import UserRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.user_service import UserService
from app.services.organization_service import OrganizationService
from app.services.workspace_service import WorkspaceService


def get_user_repository(db: Any = Depends(get_db)) -> UserRepository:
    """Provide a UserRepository instance."""
    return UserRepository(db)

def get_organization_repository(db: Any = Depends(get_db)) -> OrganizationRepository:
    """Provide an OrganizationRepository instance."""
    return OrganizationRepository(db)

def get_workspace_repository(db: Any = Depends(get_db)) -> WorkspaceRepository:
    """Provide a WorkspaceRepository instance."""
    return WorkspaceRepository(db)


def get_email_service() -> EmailService:
    """Provide an EmailService instance."""
    return EmailService()


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Provide an AuthService instance with injected dependencies."""
    return AuthService(user_repo=user_repo)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Provide a UserService instance with injected dependencies."""
    return UserService(user_repo=user_repo)


def get_organization_service(
    org_repo: OrganizationRepository = Depends(get_organization_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> OrganizationService:
    """Provide an OrganizationService instance."""
    return OrganizationService(org_repo=org_repo, user_repo=user_repo)


def get_workspace_service(
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository)
) -> WorkspaceService:
    """Provide a WorkspaceService instance."""
    return WorkspaceService(workspace_repo=workspace_repo)

from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.knowledge_service import KnowledgeService

def get_storage_service() -> StorageService:
    return StorageService()

def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

def get_vector_store(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> VectorStoreService:
    return VectorStoreService(embedding_service=embedding_service)

def get_knowledge_service(
    storage_service: StorageService = Depends(get_storage_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStoreService = Depends(get_vector_store),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository)
) -> KnowledgeService:
    return KnowledgeService(
        storage_service=storage_service,
        embedding_service=embedding_service,
        vector_store=vector_store,
        workspace_repo=workspace_repo
    )
