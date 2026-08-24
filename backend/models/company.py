from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional


class Company(Document):
    workspace_id: PydanticObjectId
    name: str = Field(..., min_length=1, max_length=200)
    ticker: str = Field(..., min_length=1, max_length=10)      # e.g. "AAPL"
    industry: Optional[str] = None                              # e.g. "Technology"
    sector: Optional[str] = None                                 # e.g. "Consumer Electronics"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "companies"                # MongoDB collection name
        indexes = ["ticker"]              # fast lookup by ticker

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "industry": "Technology",
                "sector": "Consumer Electronics",
            }
        }