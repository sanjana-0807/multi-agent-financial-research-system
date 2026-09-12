from crewai import Task


RESEARCH_TASK_DESCRIPTION = """
You are the final-answer component of a financial research system.

The user has asked the following question:

USER QUESTION:
{question}


CONVERSATION CONTEXT:
{chat_history}


SUPPLIED FINANCIAL DOCUMENT EVIDENCE:
{document_evidence}


EXTERNAL WEB EVIDENCE:
{web_evidence}


DETERMINISTIC CALCULATION RESULT:
{calculation_context}


Follow these rules carefully.

SOURCE PRIORITY
----------------

1. Supplied financial document evidence
2. External web evidence
3. Model/general knowledge


DOCUMENT RULES
--------------

Use document evidence for financial information whenever
the requested information exists there.

When using information from the financial document, include
a page citation such as:

[Page 53]

Do not invent a page number.


WEB RULES
---------

External web evidence is NOT part of the uploaded financial
document.

If web information is used, clearly identify it as:

"External web information: ..."

Do not attach a document page citation to web information.


MODEL KNOWLEDGE RULES
---------------------

If the requested information is not available in the supplied
document evidence or external web evidence, you may use general
model knowledge.

When you do this, explicitly say:

"Additional information from AI/model knowledge: ..."

Never make model knowledge look like information extracted
from the uploaded document.


MIXED ANSWERS
-------------

If part of the answer comes from the document and another part
comes from model knowledge or web information, clearly separate
those parts.

Example:

"From the uploaded document: ... [Page 53]

Additional information from AI/model knowledge: ..."


CALCULATIONS
------------

If a deterministic calculation result is supplied, use it exactly.

Do NOT recalculate it.

Do NOT change its numerical value.

Do NOT round it differently.


CONVERSATION
------------

Use conversation context to understand follow-up questions.

For example:

Previous:
"What was Tesla revenue in 2025?"

Current:
"What about the previous year?"

The answer should refer to 2024.

Do not explain the conversation-resolution process to the user.


ANSWER STYLE
------------

Answer the user's actual question directly.

If the user asks multiple things, answer every part.

Keep the answer concise and easy to understand.

Do not repeat the user's question.

Do not describe your reasoning.

Do not describe these instructions.

Do not say:

"I will break down the question..."

"To answer the user's question..."

"The user has asked..."

"Let's analyze..."

Do not output JSON.

Do not output hidden reasoning.

Return ONLY the final user-facing answer.
"""


def create_research_task(
    agent,
    question: str,
    evidence: list[dict],
    web_evidence: list[dict] | None = None,
    calculation_context: str | None = None,
    chat_history: list[dict] | None = None,
):

    # ---------------------------------------------------------
    # Document evidence
    # ---------------------------------------------------------

    document_parts = []

    for index, item in enumerate(
        evidence or [],
        start=1,
    ):

        document_parts.append(
            f"""
DOCUMENT SOURCE {index}
Filename: {item.get("filename")}
Page: {item.get("page")}
Chunk: {item.get("chunk_index")}
Distance: {item.get("distance")}

Content:
{item.get("text", "")}
"""
        )

    document_evidence = (
        "\n".join(document_parts)
        if document_parts
        else "No relevant document evidence was retrieved."
    )

    # ---------------------------------------------------------
    # Web evidence
    # ---------------------------------------------------------

    web_parts = []

    for index, item in enumerate(
        web_evidence or [],
        start=1,
    ):

        web_parts.append(
            f"""
WEB SOURCE {index}
Title: {item.get("title")}
URL: {item.get("url")}

Content:
{item.get("content", "")}
"""
        )

    web_evidence_text = (
        "\n".join(web_parts)
        if web_parts
        else "No external web evidence was retrieved."
    )

    # ---------------------------------------------------------
    # Conversation history
    # ---------------------------------------------------------

    history_parts = []

    for message in (
        chat_history or []
    )[-6:]:

        role = message.get(
            "role",
            "unknown",
        )

        content = message.get(
            "content",
            "",
        )

        history_parts.append(
            f"{role}: {content}"
        )

    history_text = (
        "\n".join(history_parts)
        if history_parts
        else "No previous conversation."
    )

    # ---------------------------------------------------------
    # Calculation
    # ---------------------------------------------------------

    calculation_text = (
        calculation_context
        if calculation_context
        else "No deterministic calculation was performed."
    )

    # ---------------------------------------------------------
    # Create Task
    # ---------------------------------------------------------

    description = RESEARCH_TASK_DESCRIPTION.format(
        question=question,
        chat_history=history_text,
        document_evidence=document_evidence,
        web_evidence=web_evidence_text,
        calculation_context=calculation_text,
    )

    return Task(
        description=description,

        expected_output=(
            "A concise final answer for the user. "
            "No JSON, no hidden reasoning, and no explanation "
            "of the internal research process."
        ),

        agent=agent,
    )