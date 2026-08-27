import os
import json
import re

from crewai import LLM


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)


llm = LLM(
    model="ollama/llama3.2:latest",
    base_url=OLLAMA_BASE_URL,
)


def _clean_json_response(raw: str) -> str:
    """
    Remove markdown code fences from an LLM response.
    """

    raw = raw.strip()

    if raw.startswith("```"):

        raw = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw,
            flags=re.IGNORECASE,
        )

        raw = re.sub(
            r"\s*```$",
            "",
            raw,
        )

    return raw.strip()


def generate_integrated_answer(
    context: dict,
) -> dict:

    question = context.get(
        "question",
        "",
    )

    pdf_chunks = context.get(
        "pdf_chunks",
        [],
    )

    extraction = context.get(
        "extraction",
        {},
    )

    red_flags = context.get(
        "red_flags",
        [],
    )

    comparison = context.get(
        "comparison",
    )

    # ---------------------------------------------------------
    # BUILD PDF EVIDENCE
    # ---------------------------------------------------------

    evidence_parts = []

    for chunk in pdf_chunks:

        page = chunk.get(
            "page",
            "Unknown",
        )

        text = chunk.get(
            "text",
            "",
        )

        if text:

            evidence_parts.append(
                f"PAGE {page}\n{text}"
            )

    evidence_text = "\n\n".join(
        evidence_parts
    )

    # ---------------------------------------------------------
    # PROMPT
    # ---------------------------------------------------------

    prompt = f"""
You are the final Financial Research Analyst.

Answer the user's question using ONLY the supplied
financial-document evidence and agent outputs.

USER QUESTION:
{question}

RULES:

1. Do not invent financial facts.
2. Do not invent values, dates, pages, companies,
   ratios, risks, or financial conclusions.
3. Prefer information directly supported by the PDF.
4. Clearly distinguish facts from analytical interpretation.
5. If the evidence is insufficient, explicitly say so.
6. Do not treat missing information as zero.
7. Do not make investment recommendations.
8. If a red flag is supplied by the Red Flag Agent,
   describe it as an identified risk rather than presenting
   it as independently verified unless the PDF evidence
   supports it.
9. Keep the answer focused on the user's question.
10. Return valid JSON only.

PDF EVIDENCE:
{evidence_text}

EXTRACTION AGENT OUTPUT:
{json.dumps(extraction, indent=2, default=str)}

RED FLAG AGENT OUTPUT:
{json.dumps(red_flags, indent=2, default=str)}

COMPARISON AGENT OUTPUT:
{json.dumps(comparison, indent=2, default=str)}

Return exactly this JSON structure:

{{
    "answer": "Clear answer to the user's question.",
    "insights": [
        "Important evidence-based insight"
    ],
    "risks": [
        "Important risk if applicable"
    ],
    "limitations": [
        "Important limitation if applicable"
    ]
}}
"""

    # ---------------------------------------------------------
    # CALL LLM
    # ---------------------------------------------------------

    response = llm.call(
        prompt
    )

    raw = str(response).strip()

    # ---------------------------------------------------------
    # CLEAN RESPONSE
    # ---------------------------------------------------------

    raw = _clean_json_response(
        raw
    )

    # ---------------------------------------------------------
    # PARSE JSON
    # ---------------------------------------------------------

    try:

        result = json.loads(
            raw
        )

        # Ensure expected keys exist.

        return {
            "answer": str(
                result.get(
                    "answer",
                    "",
                )
            ),

            "insights": result.get(
                "insights",
                [],
            ),

            "risks": result.get(
                "risks",
                [],
            ),

            "limitations": result.get(
                "limitations",
                [],
            ),
        }

    except json.JSONDecodeError:

        return {
            "answer": raw,

            "insights": [],

            "risks": [],

            "limitations": [
                "The integrated LLM response was not valid JSON."
            ],
        }