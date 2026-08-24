# routes/red_flag.py
from fastapi import APIRouter, Depends

from backend.schemas.red_flag_schema import RedFlagResponse, RedFlagRequest
from backend.services import red_flag_service
from core.dependencies import get_current_user

router = APIRouter(prefix="/red-flags", tags=["Red Flags"])


@router.post("/run", response_model=RedFlagResponse, status_code=201)
async def run_red_flags(
    payload: RedFlagRequest,
    current_user=Depends(get_current_user),
):
    return await red_flag_service.run_red_flag_analysis(payload.document_id)


@router.get("/document/{document_id}", response_model=list[RedFlagResponse])
async def get_red_flags_for_document(
    document_id: str,
    current_user=Depends(get_current_user),
):
    return await red_flag_service.list_red_flags_for_document(document_id)


@router.get("/{red_flag_id}", response_model=RedFlagResponse)
async def get_red_flag(
    red_flag_id: str,
    current_user=Depends(get_current_user),
):
    return await red_flag_service.get_red_flag_result(red_flag_id)