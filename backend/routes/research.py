from fastapi import APIRouter

from schemas.research_schema import (
    ExtractRequest,
    RedFlagRequest,
)

from services.research_service import ResearchService

router = APIRouter(
    prefix="/research",
    tags=["Research"]
)


@router.post("/extract")
def extract(request: ExtractRequest):
    """
    Placeholder extraction endpoint.
    """
    return ResearchService.extract(request.document_id)


@router.post("/redflag")
def redflag(request: RedFlagRequest):
    """
    Placeholder red flag endpoint.
    """
    return ResearchService.red_flags(request.document_id)