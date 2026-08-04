from pydantic import BaseModel


class FinancialRatios(BaseModel):
    current_ratio: float
    debt_to_equity: float
    net_profit_margin: float


class ExtractionResponse(BaseModel):
    metric_id: str
    document_id: str
    company: str
    fiscal_year: int

    revenue: float
    net_profit: float
    assets: float
    liabilities: float
    cash_flow: float
    eps: float

    ratios: FinancialRatios