from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas.research_schema import (
    ResearchRequest,
    ResearchResponse,
)

from services.research_service import (
    ResearchService,
)

from agents.research_agent.orchestrator import (
    build_integrated_research,
)


router = APIRouter(
    prefix="/research",
    tags=["Research"],
)


class IntegratedResearchRequest(BaseModel):
    question: str
    document_id: str
    comparison_context: Optional[str] = None


@router.post(
    "/ask",
    response_model=ResearchResponse,
)
def ask_research_question(
    request: ResearchRequest,
):
    """
    Basic PDF-grounded research endpoint.
    """

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Research question cannot be empty.",
        )

    if not request.document_id.strip():

        raise HTTPException(
            status_code=400,
            detail="Document ID cannot be empty.",
        )

    try:

        return ResearchService.ask_question(
            question=request.question,
            document_id=request.document_id,
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/integrated",
)
async def integrated_research(
    request: IntegratedResearchRequest,
):
    """
    Full multi-agent financial research pipeline.
    """

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Research question cannot be empty.",
        )

    if not request.document_id.strip():

        raise HTTPException(
            status_code=400,
            detail="Document ID cannot be empty.",
        )

    try:

        result = await build_integrated_research(
            question=request.question,
            document_id=request.document_id,
            comparison_context=request.comparison_context,
        )

        return result

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )