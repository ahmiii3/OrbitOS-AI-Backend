from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.user import UserRead

class OrganizationBase(BaseModel):
    name: str
    slug: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
