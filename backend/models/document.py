from beanie import Document
from pydantic import Field
from datetime import datetime, timezone


class DocumentModel(Document):
    document_id: str
    filename: str
    file_path: str

    content_type: str
    file_size: int

    page_count: int = 0
    chunk_count: int = 0

    status: str = "uploaded"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "documents"