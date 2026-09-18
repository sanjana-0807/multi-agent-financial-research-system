# models/comparison_result.py
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional


class RatioComparison(BaseModel):
    """A single financial ratio compared across companies."""
    ratio_name: str                          # e.g. "P/E Ratio", "Debt-to-Equity"
    values: dict[str, float]                 # {"AAPL": 28.5, "MSFT": 32.1}
    industry_average: Optional[float] = None
    best_performer: Optional[str] = None      # ticker of the best value for this ratio


class IndustryRanking(BaseModel):
    """Where each company stands relative to its peers."""
    ticker: str
    rank: int                                 # 1 = best
    score: Optional[float] = None             # composite score used to rank, if applicable


class TrendPoint(BaseModel):
    """A single point in a trend analysis (e.g. revenue growth over time)."""
    period: str                               # e.g. "Q1 2025", "FY2024"
    ticker: str
    value: float


class ComparisonResult(Document):
    # Optional (not required) so existing documents inserted before this
    # field existed continue to load without a validation error. Any
    # record with workspace_id=None predates workspace-scoped history
    # and will simply never match a workspace-filtered query -- which is
    # correct, since there is no reliable way to retroactively attribute
    # it to a workspace.
    workspace_id: Optional[PydanticObjectId] = None

    company_ids: list[PydanticObjectId]       # companies included in this comparison
    tickers: list[str]                        # denormalized for quick display, e.g. ["AAPL", "MSFT"]

    ratio_comparisons: list[RatioComparison] = Field(default_factory=list)
    industry_rankings: list[IndustryRanking] = Field(default_factory=list)
    trend_analysis: list[TrendPoint] = Field(default_factory=list)

    summary: Optional[str] = None             # short natural-language summary, filled in by the agent later

    status: str = Field(default="pending")    # pending | running | completed | failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "comparison_results"
        indexes = ["workspace_id", "tickers", "status"]

    class Config:
        json_schema_extra = {
            "example": {
                "workspace_id": "665f1a2b3c4d5e6f7a8b9c0e",
                "company_ids": ["665f1a2b3c4d5e6f7a8b9c0d"],
                "tickers": ["AAPL", "MSFT"],
                "status": "pending",
            }
        }