from pydantic import BaseModel
from typing import Optional


class Ratios(BaseModel):
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    net_profit_margin: Optional[float] = None


class ExtractionResponse(BaseModel):
    metric_id: str
    document_id: str
    company: str
    fiscal_year: int
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    cash_flow: Optional[float] = None
    eps: Optional[float] = None
    ratios: Ratios

    class Config:
        from_attributes = True
