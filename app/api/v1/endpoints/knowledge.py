from typing import List, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Query
from app.dependencies.auth import get_current_active_user, verify_workspace_access
from app.dependencies.services import get_knowledge_service
from app.models.user import User
from app.schemas.document import DocumentResponse, SearchResult
from app.services.knowledge_service import KnowledgeService

router = APIRouter()

@router.post(
    "/workspaces/{workspace_id}/knowledge/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document to Knowledge Base",
)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> DocumentResponse:
    # Ensure user has access to this workspace
    await verify_workspace_access(workspace_id, current_user)
    
    # Process upload -> extract -> embed -> store
    document = await knowledge_service.process_upload(workspace_id, file, current_user)
    
    return DocumentResponse.model_validate(document)


@router.get(
    "/workspaces/{workspace_id}/knowledge/search",
    response_model=List[SearchResult],
    summary="Semantic Search in Knowledge Base",
)
async def search_knowledge(
    workspace_id: str,
    query: str = Query(..., description="The search query"),
    top_k: int = Query(5, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> List[SearchResult]:
    # Ensure user has access to this workspace
    await verify_workspace_access(workspace_id, current_user)
    
    # Perform semantic search
    results = await knowledge_service.semantic_search(workspace_id, query, top_k)
    
    formatted = []
    for r in results:
        formatted.append(SearchResult(
            chunk_id=r["metadata"].get("chunk_id", "00000000-0000-0000-0000-000000000000"),
            document_id=r["metadata"].get("document_id", "00000000-0000-0000-0000-000000000000"),
            filename=r["metadata"].get("filename", "unknown"),
            content=r["content"],
            score=r["score"],
            meta_attributes=r["metadata"]
        ))
        
    return formatted
