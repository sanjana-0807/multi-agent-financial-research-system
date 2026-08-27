from pydantic import BaseModel


class ResearchRequest(BaseModel):
    question: str
    document_id: str


class ResearchCitation(BaseModel):
    document_id: str
    page: int | None = None
    source: str | None = None
    filename: str | None = None


class ResearchResponse(BaseModel):
    question: str
    answer: str
    evidence: str | None = None
    citations: list[ResearchCitation]