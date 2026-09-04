from fastapi import APIRouter, Depends

from core.dependencies import get_current_user
from models.user import User
from services.research_chat_service import (
    start_research_chat,
    select_workspace,
    select_mode,
    select_companies,
    ask_research_question,
)

router = APIRouter(
    prefix="/research-chat",
    tags=["Research Chat"],
)


@router.post("/start")
async def start(
    current_user: User = Depends(get_current_user),
):
    return await start_research_chat(
        current_user=current_user,
    )


@router.post("/workspace")
async def workspace(
    session_id: str,
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    return await select_workspace(
        session_id=session_id,
        workspace_id=workspace_id,
        current_user=current_user,
    )


@router.post("/mode")
async def mode(
    session_id: str,
    compare: bool,
):
    return await select_mode(
        session_id=session_id,
        compare=compare,
    )


@router.post("/companies")
async def companies(
    session_id: str,
    company_ids: list[str],
):
    return await select_companies(
        session_id=session_id,
        company_ids=company_ids,
    )


@router.post("/ask")
async def ask(
    session_id: str,
    question: str,
    current_user: User = Depends(get_current_user),
):
    return await ask_research_question(
        session_id=session_id,
        question=question,
        current_user=current_user,
    )
