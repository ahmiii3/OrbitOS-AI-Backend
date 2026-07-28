import uuid
import hashlib
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from app.models.document import Document, DocumentChunk
from app.models.workspace import Workspace
from app.models.user import User
from app.services.storage_service import StorageService
from app.services.document_parser import DocumentParser
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.repositories.workspace import WorkspaceRepository

class KnowledgeService:
    """Orchestrates document upload, extraction, chunking, and embedding."""
    
    def __init__(
        self,
        storage_service: StorageService,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
        workspace_repo: WorkspaceRepository,
    ):
        self.storage_service = storage_service
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.workspace_repo = workspace_repo

    async def process_upload(
        self, 
        workspace_id: str, 
        file: UploadFile, 
        user: User
    ) -> Document:
        workspace = await self.workspace_repo.get(uuid.UUID(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        # 1. Read file to memory
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 2. Upload to Supabase Storage
        file_ext = file.filename.split(".")[-1]
        storage_path = f"{workspace.organization_id}/{workspace_id}/{uuid.uuid4()}.{file_ext}"
        
        # Reset file pointer for Storage Service
        await file.seek(0)
        public_url = await self.storage_service.upload_file(file, storage_path)

        # 3. Create Document Record
        document = await Document.create(
            filename=file.filename,
            organization_id=workspace.organization_id,
            workspace_id=workspace.id,
            uploaded_by=user,
            status="PROCESSING",
            checksum=file_hash,
            meta_attributes={"storage_url": public_url, "size": len(content)}
        )

        try:
            # 4. Extract Text
            text = await DocumentParser.extract_text(file, content)
            
            # 5. Chunk Text
            metadata = {
                "document_id": str(document.id),
                "workspace_id": str(workspace.id),
                "organization_id": str(workspace.organization_id),
                "filename": file.filename
            }
            chunks = self.embedding_service.chunk_text(text, metadata=metadata)
            
            # 6. Save Chunk Records to Relational DB
            for chunk_data in chunks:
                chunk_hash = hashlib.sha256(chunk_data["content"].encode('utf-8')).hexdigest()
                await DocumentChunk.create(
                    document=document,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    content_checksum=chunk_hash,
                    meta_attributes=chunk_data["metadata"]
                )

            # 7. Store Vectors in PGVector
            # This is synchronous in Langchain right now, but it's fast enough for a background/async wrapper
            self.vector_store.add_chunks(chunks)

            # 8. Mark Completed
            document.status = "COMPLETED"
            await document.save()

        except Exception as e:
            # If processing fails, mark it
            document.status = "FAILED"
            document.meta_attributes["error"] = str(e)
            await document.save()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {str(e)}"
            )

        return document

    async def semantic_search(
        self, 
        workspace_id: str, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search across vectors scoped by workspace."""
        filter_dict = {"workspace_id": workspace_id}
        return self.vector_store.search(query=query, top_k=top_k, filter_dict=filter_dict)
