# services/comparison_service.py
"""
Bridge between the /comparison route and the Comparison Agent
(agents/comparison_agent/), matching the shared signature agreed with Prem
for wiring into agents/crew.py in Milestone 3:

    run_comparison(company_ids, extracted_data) -> ComparisonResult

Until the Comparison Agent exists, `run_comparison` computes deterministic
placeholder ratios/rankings itself so the API is fully functional and
testable in Milestone 2. Once the Extraction Agent and Comparison Agent are
ready, `extracted_data` (ticker -> ExtractionResponse-shaped dict) will be
passed in by the orchestration layer and used instead of the placeholder.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from beanie import PydanticObjectId

from models.company import Company
from models.comparison_result import (
    ComparisonResult,
    RatioComparison,
    IndustryRanking,
)
from schemas.comparison_schema import ComparisonResponse

# Ratios benchmarked until the real Comparison Agent supplies its own
# selection based on the Extraction Agent's output (Milestone 3).
_PLACEHOLDER_RATIOS = ["current_ratio", "debt_to_equity", "net_profit_margin"]


def _to_response(result: ComparisonResult) -> ComparisonResponse:
    data = result.model_dump()
    data["id"] = str(result.id)
    data["company_ids"] = [str(cid) for cid in result.company_ids]
    return ComparisonResponse.model_validate(data)


async def _resolve_companies(company_ids: list[str]) -> list[Company]:
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
        companies.append(company)

    return companies


def _build_placeholder_ratios(
    companies: list[Company],
    extracted_data: Optional[dict],
) -> list[RatioComparison]:
    ratios: list[RatioComparison] = []

    for ratio_name in _PLACEHOLDER_RATIOS:
        values: dict[str, float] = {}
        for company in companies:
            if extracted_data and company.ticker in extracted_data:
                raw = extracted_data[company.ticker].get("ratios", {}).get(ratio_name)
                values[company.ticker] = float(raw) if raw is not None else 0.0
            else:
                # Deterministic placeholder (not random) so results and
                # tests are stable until the Extraction Agent exists.
                seed = sum(ord(c) for c in company.ticker + ratio_name)
                values[company.ticker] = round((seed % 100) / 10, 2)

        best_ticker = max(values, key=values.get) if values else None
        industry_avg = round(sum(values.values()) / len(values), 2) if values else None

        ratios.append(
            RatioComparison(
                ratio_name=ratio_name,
                values=values,
                industry_average=industry_avg,
                best_performer=best_ticker,
            )
        )

    return ratios


def _build_placeholder_rankings(
    ratios: list[RatioComparison],
    companies: list[Company],
) -> list[IndustryRanking]:
    scores: dict[str, float] = {c.ticker: 0.0 for c in companies}
    for ratio in ratios:
        for ticker, value in ratio.values.items():
            scores[ticker] = scores.get(ticker, 0.0) + value

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [
        IndustryRanking(ticker=ticker, rank=idx + 1, score=round(score, 2))
        for idx, (ticker, score) in enumerate(ranked)
    ]


async def run_comparison(
    company_ids: list[str],
    extracted_data: Optional[dict] = None,
) -> ComparisonResponse:
    companies = await _resolve_companies(company_ids)

    result = ComparisonResult(
        company_ids=[c.id for c in companies],
        tickers=[c.ticker for c in companies],
        status="running",
    )
    await result.insert()

    ratios = _build_placeholder_ratios(companies, extracted_data)
    rankings = _build_placeholder_rankings(ratios, companies)

    result.ratio_comparisons = ratios
    result.industry_rankings = rankings
    result.trend_analysis = []  # populated once the Comparison Agent adds historical data (M3)
    result.summary = (
        f"Placeholder comparison of {', '.join(c.ticker for c in companies)} "
        "based on mock ratio data. Will be replaced by the Comparison Agent's "
        "generated summary in Milestone 3."
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