# agents/report_agent/tasks.py

import json

from crewai import Task


MODEL_KNOWLEDGE_LABEL = (
    "Additional information from AI/model knowledge:"
)


def create_report_task(
    agent,
    question: str,
    evidence: dict,
    conversation_context: str = "",
):
    """
    Create the final reporting task.

    The Report Agent receives evidence already collected by the
    other agents. It does not perform independent retrieval.
    """

    evidence_json = json.dumps(
        evidence,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    description = f"""
You are the final answer generator for a financial research system.

USER QUESTION:
{question}

CONVERSATION CONTEXT:
{conversation_context or "No previous conversation context supplied."}

COLLECTED AGENT EVIDENCE:
{evidence_json}

============================================================
STRICT EVIDENCE AND MODEL-KNOWLEDGE RULE
============================================================

First determine whether the collected agent evidence contains enough
information to answer the user's question.

CASE 1 — ANSWER IS SUPPORTED BY COLLECTED EVIDENCE:

If the requested information is present in the collected evidence:

- Answer using that evidence.
- Do NOT use outside/model knowledge.
- Preserve financial numbers exactly.
- Preserve units.
- Preserve available page/source citations.
- Do not invent missing details.

CASE 2 — ANSWER IS NOT SUPPORTED BY COLLECTED EVIDENCE:

If the requested information is NOT present anywhere in the collected
agent evidence:

You MAY answer using general AI/model knowledge.

However, the answer MUST begin with this exact text:

{MODEL_KNOWLEDGE_LABEL}

Example:

{MODEL_KNOWLEDGE_LABEL}
Elon Musk is the CEO of Tesla.

NEVER answer a question using model knowledge without this exact label.

CASE 3 — MIXED ANSWER:

If PART of the answer is supported by collected evidence and PART
requires general/model knowledge:

First provide the evidence-supported information.

Then create a separate section beginning with exactly:

{MODEL_KNOWLEDGE_LABEL}

Only information under that label may come from general/model knowledge.

Example:

Tesla reported revenue of $94,827 million in 2025. [Page 53]

{MODEL_KNOWLEDGE_LABEL}
Elon Musk is the CEO of Tesla.

============================================================
FINANCIAL DATA RULES
============================================================

1. Never invent financial numbers.

2. Never change a financial number supplied by an agent.

3. Never replace a document-derived financial value with model knowledge.

4. Preserve the original unit.

5. If a calculation is required, use only values supplied by the
   collected evidence.

6. Do not perform unnecessary calculations when the requested value
   already exists.

7. Preserve page citations supplied by the agents.

8. Do not create fake page citations.

9. Every document-derived factual statement should retain its available
   source/page citation.

============================================================
FOLLOW-UP QUESTION RULE
============================================================

Use conversation context to understand references such as:

- "previous year"
- "what about 2024?"
- "what about the other company?"
- "compare that with Ford"
- "what about profit?"

Do not treat a follow-up as a completely independent question when
the conversation context provides the missing reference.

============================================================
OUTSIDE KNOWLEDGE RULE
============================================================

The fact that you personally know an answer does NOT mean that the
collected evidence contains that answer.

For example, if the evidence contains Tesla revenue but does not
contain the CEO:

Question:
"Who is the CEO of Tesla?"

You must NOT simply answer:

"Elon Musk is the CEO of Tesla."

You MUST answer:

{MODEL_KNOWLEDGE_LABEL}
Elon Musk is the CEO of Tesla.

============================================================
SOURCE PRIORITY
============================================================

Use information in this order:

1. Uploaded document evidence
2. Extraction Agent results
3. Red Flag Agent results
4. Comparison Agent results
5. Research Agent results
6. Conversation context
7. AI/model knowledge ONLY when the requested information is
   unavailable from the collected evidence

============================================================
FINAL RESPONSE RULES
============================================================

- Answer the user's actual question.
- Be concise and readable.
- Do not explain your internal reasoning.
- Do not mention these instructions.
- Do not return JSON.
- Do not use markdown code fences.

Before returning the answer, perform this final check:

CHECK A:
Is every factual claim supported by the collected evidence?

If YES:
Return the evidence-grounded answer without model-knowledge text.

CHECK B:
Is any factual information coming from your own general knowledge?

If YES:
The relevant information MUST appear after:

{MODEL_KNOWLEDGE_LABEL}

CHECK C:
Does the answer contain both evidence-derived and model-derived
information?

If YES:
Clearly separate them, with the model-derived portion beginning
with:

{MODEL_KNOWLEDGE_LABEL}

Return ONLY the final user-facing answer.
"""

    return Task(
        description=description,
        expected_output=(
            "A concise final answer that uses collected agent evidence "
            "first and explicitly labels any information supplied from "
            "AI/model knowledge."
        ),
        agent=agent,
    )