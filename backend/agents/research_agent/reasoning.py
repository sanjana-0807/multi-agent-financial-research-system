from typing import List, Dict


def build_research_context(
    question: str,
    retrieved_chunks: List[Dict]
) -> str:
    """
    Build the evidence context for the Research Agent.

    Retrieved chunks are already ranked by relevance, with the
    strongest evidence appearing first.
    """

    if not retrieved_chunks:
        return (
            "No relevant information was retrieved from the document."
        )

    context_parts = []

    for index, chunk in enumerate(retrieved_chunks, start=1):

        context_parts.append(
            f"""
SOURCE {index}
Document ID: {chunk.get("document_id")}
Filename: {chunk.get("filename", "Unknown")}
Page: {chunk.get("page", "Unknown")}
Source type: {chunk.get("source", "Unknown")}
Relevance score: {chunk.get("relevance_score", "Unknown")}

CONTENT:
{chunk.get("text", "")}
"""
        )

    return (
        f"USER QUESTION:\n{question}\n\n"
        "RETRIEVED DOCUMENT EVIDENCE:\n"
        + "\n".join(context_parts)
    )


def create_research_prompt(
    question: str,
    retrieved_chunks: List[Dict]
) -> str:
    """
    Create a strict grounded-research prompt.
    """

    context = build_research_context(
        question,
        retrieved_chunks
    )

    return f"""
You are a financial research assistant analyzing a company's
financial filing.

Your answer MUST be based ONLY on the retrieved document evidence.

IMPORTANT RULES:

1. Do NOT use outside knowledge.
2. Do NOT invent or estimate financial values.
3. Prioritize evidence that directly answers the user's question.
4. If the retrieved evidence explicitly states the requested metric
   and fiscal year, use that value directly.
5. Do not calculate a value when the document already provides the
   value explicitly.
6. Do not confuse expenses, liabilities, segment revenue,
   customer advances, or other financial metrics with total company
   revenue.
7. Make sure the fiscal year in the evidence matches the fiscal year
   requested by the user.
8. If a direct statement exists in the retrieved evidence, do NOT
   claim that the evidence is insufficient.
9. If multiple sources contain conflicting information, explain the
   conflict instead of silently choosing one.
10. If the evidence truly does not contain enough information, say:
    "The available document evidence is insufficient to answer the
    question."
11. Every important factual claim must include its source page.
12. Keep the answer concise.
13. Do not cite pages that do not support the claim.
IMPORTANT RULES:

1. Do NOT use outside knowledge.
2. Do NOT invent or estimate financial values.
3. Prioritize evidence that directly answers the user's question.
4. If the retrieved evidence explicitly states the requested metric
   and fiscal year, use that value directly.
5. Do not calculate a value when the document already provides the
   value explicitly.
6. Do not confuse expenses, liabilities, segment revenue,
   customer advances, or other financial metrics with total company
   revenue.
7. Make sure the fiscal year in the evidence matches the fiscal year
   requested by the user.
8. If a direct statement exists in the retrieved evidence, do NOT
   claim that the evidence is insufficient.
9. If multiple sources contain conflicting information, explain the
   conflict instead of silently choosing one.
10. If the evidence truly does not contain enough information, say:
    "The available document evidence is insufficient to answer the
    question."
11. Every important factual claim must include its source page.
12. Keep the answer concise.
13. Do not cite pages that do not support the claim.
OUTPUT FORMAT:

Answer:
<direct answer>

Evidence:
Page <page number> — <short explanation of the evidence>

If the question cannot be answered:

Answer:
The available document evidence is insufficient to answer the question.

Evidence:
<explain what information is missing and cite the relevant pages if
appropriate>

{context}

USER QUESTION:
{question}

FINAL ANSWER:
"""
