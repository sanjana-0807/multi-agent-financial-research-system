from typing import Optional, Dict

from beanie import Document
from pydantic import Field


class ExtractedMetric(Document):

    metric_id: str = Field(..., description="Unique metric ID")
    document_id: str = Field(..., description="Source document ID")

    company: Optional[str] = None
    fiscal_year: Optional[int] = None

    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    cash_flow: Optional[float] = None
    eps: Optional[float] = None

    ratios: Dict[str, float] = Field(default_factory=dict)

    class Settings:
        name = "extracted_metrices"