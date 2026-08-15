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