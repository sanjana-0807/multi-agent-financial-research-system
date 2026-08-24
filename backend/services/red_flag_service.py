"""
Red Flag Service.

This service connects the red-flag API routes with:

1. Document fetching
2. Deterministic financial extraction
3. Deterministic red-flag rules
4. Optional auditor-remarks classification using Ollama/CrewAI
5. MongoDB persistence through Beanie
"""

from datetime import datetime, timezone
import logging

from fastapi import HTTPException

from backend.agents.extraction_agent.tasks import run_extraction
from backend.agents.extraction_agent.document_fetcher import (
    fetch_document_text,
)

from backend.agents.red_flag_agent.rules import (
    run_all_rules,
    compute_overall_risk,
)

from backend.models.red_flag import (
    RedFlagResult,
    RedFlag,
)

from backend.schemas.red_flag_schema import (
    RedFlagResponse,
)

from backend.agents.red_flag_agent.document_context import (
    fetch_auditor_context,
)

from backend.agents.red_flag_agent.crew import (
    run_auditor_classification,
)


logger = logging.getLogger(__name__)


# ============================================================
# RESPONSE CONVERSION
# ============================================================

def _to_response(
    result: RedFlagResult,
) -> RedFlagResponse:

    data = result.model_dump()

    # MongoDB / Beanie ObjectId -> string
    if result.id is not None:
        data["id"] = str(result.id)

    return RedFlagResponse.model_validate(data)


# ============================================================
# RUN RED FLAG ANALYSIS
# ============================================================

async def run_red_flag_analysis(
    document_id: str,
) -> RedFlagResponse:

    # --------------------------------------------------------
    # 1. Fetch document
    # --------------------------------------------------------

    document_text = fetch_document_text(
        document_id
    )

    if document_text is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if not document_text.strip():

        raise HTTPException(
            status_code=404,
            detail="Document contains no text",
        )

    # --------------------------------------------------------
    # 2. Extract financial metrics
    # --------------------------------------------------------

    try:

        extraction = run_extraction(
            document_text=document_text,
            document_id=document_id,
        )

    except Exception as exc:

        logger.exception(
            "Financial extraction failed for document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Financial extraction failed: {str(exc)}",
        )

    # --------------------------------------------------------
    # 3. Validate extraction
    # --------------------------------------------------------

    if not extraction:

        raise HTTPException(
            status_code=500,
            detail="Financial extraction returned no data",
        )

    if "error" in extraction:

        raise HTTPException(
            status_code=500,
            detail=extraction["error"],
        )

    metric_id = extraction.get(
        "metric_id",
        f"M_{document_id}",
    )

    # --------------------------------------------------------
    # 4. Run deterministic financial red-flag rules
    # --------------------------------------------------------

    try:

        raw_flags = run_all_rules(
            extraction,
            metric_id,
        )

    except Exception as exc:

        logger.exception(
            "Red-flag rule execution failed for document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Red-flag analysis failed: {str(exc)}",
        )

    # Make sure we always have a list.
    if raw_flags is None:
        raw_flags = []

    # --------------------------------------------------------
    # 5. Auditor remarks classification
    #
    # This is optional.
    #
    # If Ollama/CrewAI fails, the deterministic financial
    # red-flag analysis should still continue.
    # --------------------------------------------------------

    try:

        auditor_context = fetch_auditor_context(
            document_id
        )

        if auditor_context:

            auditor_findings = (
                await run_auditor_classification(
                    auditor_context
                )
            )

            if auditor_findings:

                for finding in auditor_findings:

                    raw_flags.append(
                        {
                            "category":
                                "auditor_remarks",

                            "title":
                                finding.get(
                                    "title",
                                    "Auditor Remark",
                                ),

                            "severity":
                                finding.get(
                                    "severity",
                                    "MEDIUM",
                                ),

                            "explanation":
                                finding.get(
                                    "explanation",
                                    "",
                                ),

                            "evidence":
                                finding.get(
                                    "evidence",
                                    "",
                                ),

                            "source_metric_id":
                                None,

                            "page_number":
                                finding.get(
                                    "page_number"
                                ),
                        }
                    )

    except Exception:

        # Do NOT fail the entire red-flag analysis just because
        # the optional LLM auditor layer failed.

        logger.exception(
            "Auditor-remarks classification failed for document_id=%s",
            document_id,
        )

    # --------------------------------------------------------
    # 6. Calculate overall risk
    # --------------------------------------------------------

    try:

        overall_risk = compute_overall_risk(
            raw_flags
        )

    except Exception as exc:

        logger.exception(
            "Overall risk calculation failed for document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Risk calculation failed: {str(exc)}",
        )

    # --------------------------------------------------------
    # 7. Create MongoDB document
    # --------------------------------------------------------

    try:

        result = RedFlagResult(
            document_id=document_id,

            company=extraction.get(
                "company",
                "Unknown",
            ),

            fiscal_year=extraction.get(
                "fiscal_year"
            ),

            metric_id=metric_id,

            flags=[
                RedFlag(**flag)
                for flag in raw_flags
            ],

            overall_risk=overall_risk,

            status="completed",

            completed_at=datetime.now(
                timezone.utc
            ),
        )

        await result.insert()

    except Exception as exc:

        logger.exception(
            "Failed to save red-flag result for document_id=%s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save red-flag result: {str(exc)}",
        )

    # --------------------------------------------------------
    # 8. Return API response
    # --------------------------------------------------------

    return _to_response(result)


# ============================================================
# GET ONE RED FLAG RESULT
# ============================================================

async def get_red_flag_result(
    red_flag_id: str,
) -> RedFlagResponse:

    from beanie import PydanticObjectId

    try:

        object_id = PydanticObjectId(
            red_flag_id
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid red flag result id",
        )

    result = await RedFlagResult.get(
        object_id
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Red flag result not found",
        )

    return _to_response(result)


# ============================================================
# LIST RED FLAGS FOR DOCUMENT
# ============================================================

async def list_red_flags_for_document(
    document_id: str,
) -> list[RedFlagResponse]:

    results = await RedFlagResult.find(
        RedFlagResult.document_id == document_id
    ).to_list()

    return [
        _to_response(result)
        for result in results
    ]