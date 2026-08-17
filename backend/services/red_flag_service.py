# services/red_flag_service.py
"""
Bridge between the /red-flags route and the Red Flag Agent.

Layer 1 (this file + agents/red_flag_agent/rules.py): deterministic
numeric rule engine over ExtractionResponse data -- no LLM involved,
fully reproducible.

Layer 2 (agents/red_flag_agent/tasks.py + agent.py, added separately):
LLM-based auditor-remarks classification over raw document text via
CrewAI + Ollama. Not called from here yet -- see run_full_analysis
once that layer is wired in.
"""
from datetime import datetime, timezone

from fastapi import HTTPException

from agents.extraction_agent.tasks import run_extraction
from agents.extraction_agent.document_fetcher import fetch_document_text
from agents.red_flag_agent.rules import run_all_rules, compute_overall_risk
from models.red_flag import RedFlagResult, RedFlag
from schemas.red_flag_schema import RedFlagResponse
import logging
from agents.red_flag_agent.document_context import fetch_auditor_context
from agents.red_flag_agent.crew import run_auditor_classification

logger = logging.getLogger(__name__)

def _to_response(result: RedFlagResult) -> RedFlagResponse:
    data = result.model_dump()
    data["id"] = str(result.id)
    return RedFlagResponse.model_validate(data)


async def run_red_flag_analysis(document_id: str) -> RedFlagResponse:
    document_text = fetch_document_text(document_id)
    if document_text is None:
        raise HTTPException(status_code=404, detail="document not found")

    extraction = run_extraction(document_text, document_id=document_id)
    if "error" in extraction:
        raise HTTPException(status_code=500, detail=extraction["error"])

    metric_id = extraction["metric_id"]

    raw_flags = run_all_rules(extraction, metric_id)
    # Layer 2: auditor remarks (LLM), scoped to retrieved excerpts only.
    try:
        auditor_context = fetch_auditor_context(document_id)
        if auditor_context:
            auditor_findings = await run_auditor_classification(auditor_context)
            for f in auditor_findings:
                raw_flags.append({
                    "category": "auditor_remarks",
                    "title": f.get("title", "Auditor Remark"),
                    "severity": f.get("severity", "MEDIUM"),
                    "explanation": f.get("explanation", ""),
                    "evidence": f.get("evidence", ""),
                    "source_metric_id": None,
                    "page_number": f.get("page_number"),
                })
    except Exception:
        logger.exception(
            "Auditor-remarks classification failed for document_id=%s",
            document_id,
        )
    overall_risk = compute_overall_risk(raw_flags)

    result = RedFlagResult(
        document_id=document_id,
        company=extraction["company"],
        fiscal_year=extraction["fiscal_year"],
        metric_id=metric_id,
        flags=[RedFlag(**f) for f in raw_flags],
        overall_risk=overall_risk,
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    await result.insert()

    return _to_response(result)


async def get_red_flag_result(red_flag_id: str) -> RedFlagResponse:
    from beanie import PydanticObjectId
    try:
        obj_id = PydanticObjectId(red_flag_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid red flag result id")

    result = await RedFlagResult.get(obj_id)
    if not result:
        raise HTTPException(status_code=404, detail="Red flag result not found")
    return _to_response(result)


async def list_red_flags_for_document(document_id: str) -> list[RedFlagResponse]:
    results = await RedFlagResult.find(
        RedFlagResult.document_id == document_id
    ).to_list()
    return [_to_response(r) for r in results]