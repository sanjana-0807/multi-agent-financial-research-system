# schemas/red_flag_schema.py
from pydantic import BaseModel
from typing import Optional


class RedFlagItem(BaseModel):
    category: str
    title: str
    severity: str
    explanation: str
    evidence: str
    source_metric_id: Optional[str] = None
    page_number: Optional[int] = None


class RedFlagResponse(BaseModel):
    id: str
    document_id: str
    company: str
    fiscal_year: int
    metric_id: str
    flags: list[RedFlagItem]
    overall_risk: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class RedFlagRequest(BaseModel):
    document_id: str