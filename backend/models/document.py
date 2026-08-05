from beanie import Document
from pydantic import Field
from datetime import datetime


class DocumentModel(Document):
    company_id: str
    file_name: str
    file_path: str
    status: str = "Uploaded"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "documents"