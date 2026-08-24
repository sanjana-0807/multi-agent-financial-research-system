from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional


class Workspace(Document):
    owner_id: PydanticObjectId
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    objective: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workspaces"
        indexes = ["owner_id"]