from datetime import datetime
from typing import Any

from beanie import Document


class Report(Document):
    report_id: str
    company_name: str
    report_period: str
    executive_summary: str | None = None
    key_financials: dict[str, Any] = {}
    red_flags: list[Any] = []
    comparison: dict[str, Any] = {}
    outlook: str | None = None
    pdf_path: str | None = None
    status: str = "pending"
    error: str | None = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "reports"