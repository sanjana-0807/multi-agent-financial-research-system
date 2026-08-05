from pydantic import BaseModel
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    id: str
    company_id: str
    file_name: str
    file_path: str
    status: str
    uploaded_at: datetime


class DocumentResponse(BaseModel):
    id: str
    company_id: str
    file_name: str
    file_path: str
    status: str
    uploaded_at: datetime