# models/red_flag.py
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional


class RedFlag(BaseModel):
    """A single detected red flag."""
    category: str          # rising_debt | falling_margins | cash_flow_issues | financial_risk | auditor_remarks
    title: str
    severity: str           # LOW | MEDIUM | HIGH
    explanation: str
    evidence: str
    source_metric_id: Optional[str] = None   # links back to the ExtractionResponse.metric_id
    page_number: Optional[int] = None        # only populated by the auditor-remarks (LLM) layer


class RedFlagResult(Document):
    document_id: str
    company: str
    fiscal_year: int
    metric_id: str                            # the ExtractionResponse this analysis was run against

    flags: list[RedFlag] = Field(default_factory=list)
    overall_risk: Optional[str] = None         # LOW | MEDIUM | HIGH, derived from flags

    status: str = Field(default="pending")     # pending | running | completed | failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "red_flags"
        indexes = ["document_id", "company", "status"]

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "D09AE81D6",
                "company": "NVIDIA CORPORATION",
                "fiscal_year": 2025,
                "status": "completed",
            }
        }