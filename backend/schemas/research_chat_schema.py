from typing import List, Optional

from pydantic import BaseModel


class ResearchWorkspaceRequest(BaseModel):
    session_id: str
    workspace_id: str


class ResearchModeRequest(BaseModel):
    session_id: str
    comparison: bool


class ResearchCompanySelectionRequest(BaseModel):
    session_id: str
    company_ids: List[str]


class ResearchQuestionRequest(BaseModel):
    session_id: str
    question: str