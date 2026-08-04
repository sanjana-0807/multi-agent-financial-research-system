from pydantic import BaseModel


class ExtractRequest(BaseModel):
    document_id: str


class RedFlagRequest(BaseModel):
    document_id: str