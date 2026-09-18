# routes/comparison.py
from typing import Optional

from fastapi import APIRouter, Depends, Query

from schemas.comparison_schema import ComparisonRequest, ComparisonResponse
from services import comparison_service
from core.dependencies import get_current_user

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.post("/run", response_model=ComparisonResponse, status_code=201)
async def run_comparison(
    payload: ComparisonRequest,
    current_user=Depends(get_current_user),
):
    """
    Triggers a comparison across the given companies and returns the
    result. The saved record is tagged with workspace_id so it shows
    up when this workspace's history is listed. Persists a
    ComparisonResult document (status starts "running", ends
    "completed" or "failed") so it shows up in history regardless of
    outcome. See services/comparison_service.py.
    """
    return await comparison_service.run_comparison(
        payload.company_ids, payload.workspace_id, current_user
    )


@router.get("/", response_model=list[ComparisonResponse])
async def list_comparisons(
    workspace_id: Optional[str] = Query(
        None,
        description="Scope results to this workspace's comparisons only. "
        "Omit only for admin/debug use -- normal callers should always "
        "pass this to avoid paging through every workspace's history.",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user=Depends(get_current_user),
):
    return await comparison_service.list_comparisons(
        skip=skip, limit=limit, workspace_id=workspace_id
    )


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: str,
    current_user=Depends(get_current_user),
):
    return await comparison_service.get_comparison(comparison_id)