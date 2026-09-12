# schemas/report_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReportGenerateRequest(BaseModel):
    """Body for POST /report/generate."""
    workspace_id: str
    company_id: str
    comparison_ids: Optional[list[str]] = Field(
        default=None,
        description=(
            "Specific ComparisonResult ids to include in the report. "
            "If omitted, every completed comparison involving this "
            "company is auto-included (deduped by company set, "
            "keeping the latest run of each)."
        ),
    )


class ComparisonRefResponse(BaseModel):
    comparison_id: str
    tickers: list[str]


class ComparisonPreviewResponse(BaseModel):
    """One entry in the 'which comparisons could I include' preview
    list -- see GET /report/company/{company_id}/available-comparisons."""
    comparison_id: str
    tickers: list[str]
    status: str
    completed_at: Optional[datetime] = None


class ReportSectionStatusResponse(BaseModel):
    key_financials: bool
    red_flags: bool
    company_comparison: bool


class ReportResponse(BaseModel):
    id: str
    workspace_id: str
    company_id: str
    company_name: str
    ticker: str
    document_id: str
    fiscal_year: int

    comparisons_included: list[ComparisonRefResponse] = Field(default_factory=list)
    section_status: ReportSectionStatusResponse

    executive_summary: Optional[str] = None
    outlook: Optional[str] = None

    filename: str
    status: str
    error_message: Optional[str] = None

    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True