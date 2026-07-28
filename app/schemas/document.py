from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    filename: str
    visibility: str = "team"
    meta_attributes: Optional[Dict[str, Any]] = None

class DocumentResponse(DocumentBase):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    uploaded_by_id: UUID
    status: str
    version: int
    is_latest: bool
    checksum: str
    upload_time: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    score: float
    meta_attributes: Optional[Dict[str, Any]] = None
