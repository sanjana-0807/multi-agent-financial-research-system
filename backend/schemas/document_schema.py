from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    embedding_status: str
    vector_database: str
    metadata_database: str
    ocr_used: bool
    ocr_page_count: int
    status: str


class LinkCompanyRequest(BaseModel):
    company_id: str


class DocumentDetailResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    page_count: int
    chunk_count: int
    status: str
    company_id: Optional[str] = None
    created_at: str
    updated_at: str