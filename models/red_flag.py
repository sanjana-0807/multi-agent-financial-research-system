from typing import List

from beanie import Document
from pydantic import Field


class RedFlag(Document):

    flag_id: str = Field(..., description="Unique red flag ID")
    document_id: str = Field(..., description="Source document ID")

    company: str | None = None

    risk_level: str = "Low"

    red_flags: List[str] = []

    class Settings:
        name = "red_flags"