# services/comparison_service.py
"""
Bridge between the /comparison route and the Comparison Agent
(agents/comparison_agent/).

Flow for a real request:
    1. Resolve company_ids -> Company documents.
    2. For each company, find its latest linked+indexed document and
       run the Extraction Agent against it (data_fetcher.py). If any
       company has no linked/processed document, this is a hard 422 --
       we never fabricate numbers for a missing company.
    3. Compute ratio comparisons and rankings deterministically in
       Python (benchmarking.py) -- no LLM involved, fully reproducible.
    4. Ask the Comparison Agent's LLM step (crew.py) to narrate the
       already-computed table. The LLM never sees raw numbers it could
       get wrong -- only the finished table.
    5. Persist and return the ComparisonResult.

`extracted_data` can still be passed in directly (used by tests, or by
a future orchestration layer that already has extraction results in
hand) to skip step 2.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.company import Company
from models.comparison_result import ComparisonResult
from schemas.comparison_schema import ComparisonResponse
from models.user import User
from models.workspace import Workspace

from agents.comparison_agent.data_fetcher import get_extractions_for_companies
from agents.comparison_agent.benchmarking import (
    build_ratio_comparisons,
    build_rankings,
    format_comparison_context,
)
from agents.comparison_agent.crew import run_comparison_narrative


def _to_response(result: ComparisonResult) -> ComparisonResponse:
    data = result.model_dump()
    data["id"] = str(result.id)
    data["company_ids"] = [str(cid) for cid in result.company_ids]
    return ComparisonResponse.model_validate(data)


async def _resolve_companies(company_ids: list[str], workspace: Workspace) -> list[Company]:
    if len(company_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two companies are required for a comparison",
        )

    companies: list[Company] = []
    for cid in company_ids:
        try:
            obj_id = PydanticObjectId(cid)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid company id '{cid}'")

        company = await Company.get(obj_id)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{cid}' not found")
        if company.workspace_id != workspace.id:                      
            raise HTTPException(                                       
                status_code=403,                                       
                detail=f"Company '{cid}' does not belong to this workspace",  
            )  
        companies.append(company)

    return companies


async def run_comparison(
    company_ids: list[str],
    workspace_id: str,                    
    current_user: "User",
    extracted_data: Optional[dict] = None,
) -> ComparisonResponse:
    from services.workspace_service import get_workspace   
    workspace = await get_workspace(workspace_id, current_user)  

    companies = await _resolve_companies(company_ids, workspace)

    if extracted_data is None:
        extracted_data, missing = await get_extractions_for_companies(companies)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "No processed document is linked to: "
                    f"{', '.join(missing)}. Upload a document and link "
                    "it via PATCH /documents/{document_id}/link-company "
                    "for each company before running a comparison."
                ),
            )

    result = ComparisonResult(
        company_ids=[c.id for c in companies],
        tickers=[c.ticker for c in companies],
        status="running",
    )
    await result.insert()

    ratio_comparisons = build_ratio_comparisons(extracted_data)
    rankings = build_rankings(extracted_data, ratio_comparisons)

    companies_by_ticker = {c.ticker: c.name for c in companies}
    comparison_context = format_comparison_context(
        companies_by_ticker, ratio_comparisons, rankings
    )

    narrative = await run_comparison_narrative(comparison_context)

    result.ratio_comparisons = ratio_comparisons
    result.industry_rankings = rankings
    # Each ExtractionResponse today reflects a single fiscal year per
    # document (see agents/extraction_agent), so there is no year-over-
    # year series to plot yet. Populate this once a company can have
    # multiple linked documents across fiscal years.
    result.trend_analysis = []
    result.summary = narrative.get("summary") or (
        f"Comparison of {', '.join(c.ticker for c in companies)} "
        "completed. A narrative summary could not be generated, but "
        "the numeric comparison below is complete."
    )
    result.status = "completed"
    result.completed_at = datetime.now(timezone.utc)
    await result.save()

    return _to_response(result)


async def get_comparison(comparison_id: str) -> ComparisonResponse:
    try:
        obj_id = PydanticObjectId(comparison_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid comparison id")

    result = await ComparisonResult.get(obj_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison result not found")
    return _to_response(result)


async def list_comparisons(skip: int = 0, limit: int = 50) -> list[ComparisonResponse]:
    results = await ComparisonResult.find_all().skip(skip).limit(limit).to_list()
    return [_to_response(r) for r in results]