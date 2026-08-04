from decimal import Decimal
from pydantic import BaseModel
class Config:
    from_attributes = True
class Ratios(BaseModel):
    current_ratio: Decimal
    debt_to_equity: Decimal
    net_profit_margin: Decimal
class ExtractionResponse(BaseModel):
    metric_id: str
    document_id: str
    company: str
    fiscal_year: int
    revenue: Decimal
    net_profit: Decimal
    assets: Decimal
    liabilities: Decimal
    cash_flow: Decimal
    eps: Decimal
    ratios: Ratios
