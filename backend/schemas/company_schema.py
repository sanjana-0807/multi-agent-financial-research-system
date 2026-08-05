from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    ticker: str = Field(..., min_length=1, max_length=10)
    industry: Optional[str] = None
    sector: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    ticker: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True