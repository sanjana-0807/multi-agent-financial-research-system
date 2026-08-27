from typing import Dict, Optional

from .integrated_llm import generate_integrated_answer

from agents.research_agent.research_agent import (
    answer_research_question,
)

from agents.extraction_agent.tasks import (
    run_extraction,
)

from agents.extraction_agent.document_fetcher import (
    fetch_document_text,
)

from agents.red_flag_agent.crew import (
    run_auditor_classification,
)

from agents.red_flag_agent.document_context import (
    fetch_auditor_context,
)

from agents.red_flag_agent.rules import (
    run_all_rules,
)


async def build_integrated_research(
    question: str,
    document_id: str,
    comparison_context: Optional[str] = None,
) -> Dict:
    """
    Integrates:

    1. Research Agent
    2. Extraction Agent
    3. Deterministic Red Flag Agent
    4. Auditor Remarks Agent
    5. Optional Comparison Agent
    6. Integrated LLM
    """

    # ---------------------------------------------------------
    # 1. VALIDATE INPUTS
    # ---------------------------------------------------------

    if not question or not question.strip():

        return {
            "question": question,
            "pdf_analysis": {
                "answer": "Please provide a research question.",
                "evidence": None,
                "citations": [],
            },
            "llm_analysis": {
                "answer": "Please provide a research question.",
                "insights": [],
                "risks": [],
                "limitations": [],
            },
            "agent_data": {},
        }

    if not document_id or not document_id.strip():

        return {
            "question": question,
            "pdf_analysis": {
                "answer": "A document ID is required.",
                "evidence": None,
                "citations": [],
            },
            "llm_analysis": {
                "answer": "A document ID is required.",
                "insights": [],
                "risks": [],
                "limitations": [],
            },
            "agent_data": {},
        }

    # ---------------------------------------------------------
    # 2. RESEARCH AGENT
    # ---------------------------------------------------------

    research_result = answer_research_question(
        question=question,
        document_id=document_id,
        top_k=5,
    )

    # ---------------------------------------------------------
    # 3. FETCH COMPLETE DOCUMENT
    # ---------------------------------------------------------

    document_text = fetch_document_text(
        document_id
    )

    if not document_text:

        return {
            "question": question,

            "pdf_analysis": {
                "answer": research_result.get(
                    "answer",
                    "No answer available.",
                ),

                "evidence": research_result.get(
                    "evidence"
                ),

                "citations": research_result.get(
                    "citations",
                    [],
                ),
            },

            "llm_analysis": {
                "answer": (
                    "The document could not be loaded "
                    "for integrated analysis."
                ),
                "insights": [],
                "risks": [],
                "limitations": [
                    "The source document could not be loaded."
                ],
            },

            "agent_data": {
                "extraction": {},
                "red_flags": [],
                "comparison": comparison_context,
            },
        }

    # ---------------------------------------------------------
    # 4. EXTRACTION AGENT
    # ---------------------------------------------------------

    try:

        extraction_result = run_extraction(
            document_text=document_text,
            document_id=document_id,
        )

    except Exception as exc:

        extraction_result = {
            "error": str(exc),
            "document_id": document_id,
        }

    # ---------------------------------------------------------
    # 5. DETERMINISTIC RED FLAGS
    # ---------------------------------------------------------

    red_flags = []

    try:

        metric_id = extraction_result.get(
            "metric_id"
        )

        if metric_id:

            red_flags = run_all_rules(
                extraction_result,
                metric_id,
            )

    except Exception:

        red_flags = []

    # ---------------------------------------------------------
    # 6. AUDITOR REMARKS
    # ---------------------------------------------------------

    auditor_findings = []

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

    except Exception:

        auditor_findings = []

    # ---------------------------------------------------------
    # 7. COMBINE RED FLAGS
    # ---------------------------------------------------------

    all_red_flags = (
        red_flags +
        auditor_findings
    )

    # ---------------------------------------------------------
    # 8. BUILD INTEGRATED CONTEXT
    # ---------------------------------------------------------

    integrated_context = {

        "question": question,

        "pdf_research": research_result,

        "pdf_chunks": research_result.get(
            "retrieved_chunks",
            [],
        ),

        "extraction": extraction_result,

        "red_flags": all_red_flags,

        "comparison": comparison_context,
    }

    # ---------------------------------------------------------
    # 9. INTEGRATED LLM
    # ---------------------------------------------------------

    try:

        llm_analysis = generate_integrated_answer(
            integrated_context
        )

    except Exception as exc:

        llm_analysis = {
            "answer": (
                "Integrated LLM analysis failed."
            ),
            "insights": [],
            "risks": [],
            "limitations": [
                str(exc)
            ],
        }

    # ---------------------------------------------------------
    # 10. FINAL RESPONSE
    # ---------------------------------------------------------

    return {

        "question": question,

        "pdf_analysis": {

            "answer": research_result.get(
                "answer"
            ),

            "evidence": research_result.get(
                "evidence"
            ),

            "citations": research_result.get(
                "citations",
                [],
            ),
        },

        "llm_analysis": llm_analysis,

        "agent_data": {

            "extraction": extraction_result,

            "red_flags": all_red_flags,

            "comparison": comparison_context,
        },
    }