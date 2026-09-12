# models/report.py
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional


class ReportSectionStatus(BaseModel):
    """
    Tracks whether each section actually had data available when the
    report was generated. Key Financials and Red Flags reflect
    whether the underlying agents produced usable data; Company
    Comparison is expected to be False whenever no comparison was run
    -- that's a normal, supported state, not a failure.
    """
    key_financials: bool = True
    red_flags: bool = True
    company_comparison: bool = True


class ReportComparisonRef(BaseModel):
    """
    Snapshot reference to a ComparisonResult that was included in this
    report at generation time. Stored (not just re-queried later) so
    that if comparisons are re-run afterward, older reports remain an
    accurate record of what they were built from.
    """
    comparison_id: str
    tickers: list[str]


class Report(Document):
    workspace_id: PydanticObjectId
    company_id: PydanticObjectId
    company_name: str
    ticker: str

    # The filing this report's Key Financials / Red Flags sections are
    # based on. Extraction itself is never persisted (see
    # agents/extraction_agent) -- this id is what lets you trace a
    # report back to the source document if extraction is re-run.
    document_id: str
    fiscal_year: int

    comparisons_included: list[ReportComparisonRef] = Field(default_factory=list)
    section_status: ReportSectionStatus = Field(default_factory=ReportSectionStatus)

    executive_summary: Optional[str] = None
    outlook: Optional[str] = None

    # Set once the PDF is rendered and stored in GridFS. Bucket used is
    # the default ("fs") in the same Atlas database referenced by
    # settings.DATABASE_NAME.
    gridfs_file_id: Optional[str] = None
    filename: str

    status: str = Field(default="pending")   # pending | generating | completed | failed
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "reports"
        indexes = ["company_id", "workspace_id", "status"]

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "NVIDIA Corporation",
                "ticker": "NVDA",
                "fiscal_year": 2025,
                "status": "completed",
            }
        }