from fastapi import APIRouter

from schemas.research_schema import (
    ExtractRequest,
    RedFlagRequest,
    ResearchAskRequest,
    ResearchAskResponse,
)

from services.research_service import ResearchService


router = APIRouter(
    prefix="/research",
    tags=["Research"],
)


@router.post(
    "/ask",
    response_model=ResearchAskResponse,
)
async def ask_research(
    request: ResearchAskRequest,
):
    return await ResearchService.ask(
        document_id=request.document_id,
        question=request.question,
        conversation_id=request.conversation_id,
        chat_history=[
            message.model_dump()
            for message in request.chat_history
        ],
    )


@router.post("/extract")
def extract(
    request: ExtractRequest,
):
    return ResearchService.extract(
        request.document_id
    )


@router.post("/redflag")
def redflag(
    request: RedFlagRequest,
):
    return ResearchService.red_flags(
        request.document_id
    )