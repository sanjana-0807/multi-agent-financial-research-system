from typing import Optional
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

    ocr_used: bool = False
    ocr_page_count: int = 0

    # Links this document to a Company (models/company.py) so the
    # Comparison Agent can find the right document to extract metrics
    # from for a given company. Optional because documents can be
    # uploaded before a Company record exists, or never linked at all
    # (e.g. seed/demo documents).
    company_id: Optional[str] = None
    
    status: str = "uploaded"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "documents"
        indexes = ["company_id", "status"]