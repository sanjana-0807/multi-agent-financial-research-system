# schemas/comparison_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ComparisonRequest(BaseModel):
    """Body for POST /comparison/run."""
    company_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Mongo _id strings of the companies to compare (2-10).",
    )

class ComparisonRequest(BaseModel):
    """Body for POST /comparison/run."""
    workspace_id: str = Field(..., description="Mongo _id of the Workspace these companies belong to")
    company_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Mongo _id strings of the companies to compare (2-10).",
    )
    
class RatioComparisonResponse(BaseModel):
    ratio_name: str
    values: dict[str, float]
    industry_average: Optional[float] = None
    best_performer: Optional[str] = None


class IndustryRankingResponse(BaseModel):
    ticker: str
    rank: int
    score: Optional[float] = None


class TrendPointResponse(BaseModel):
    period: str
    ticker: str
    value: float


class ComparisonResponse(BaseModel):
    id: str
    company_ids: list[str]
    tickers: list[str]

    ratio_comparisons: list[RatioComparisonResponse] = Field(default_factory=list)
    industry_rankings: list[IndustryRankingResponse] = Field(default_factory=list)
    trend_analysis: list[TrendPointResponse] = Field(default_factory=list)

    summary: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True