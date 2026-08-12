# routes/comparison.py
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
    Triggers a comparison across the given companies and returns the result.

    NOTE: until the Comparison Agent is built (Milestone 3), this returns
    a result computed from placeholder ratio data so the API contract is
    stable and testable now. See services/comparison_service.py.
    """
    return await comparison_service.run_comparison(payload.company_ids)


@router.get("/", response_model=list[ComparisonResponse])
async def list_comparisons(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user=Depends(get_current_user),
):
    return await comparison_service.list_comparisons(skip=skip, limit=limit)


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: str,
    current_user=Depends(get_current_user),
):
    return await comparison_service.get_comparison(comparison_id)