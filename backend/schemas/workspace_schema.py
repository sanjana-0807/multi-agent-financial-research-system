from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    objective: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    objective: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    description: Optional[str] = None
    objective: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    document_count: int = 0

    class Config:
        from_attributes = True