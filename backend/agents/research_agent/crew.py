import os

import httpx

from dotenv import load_dotenv

from agents.research_agent.agent import (
    create_research_agent,
)

from agents.research_agent.tasks import (
    create_research_task,
)


load_dotenv()


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).rstrip("/")


OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:latest",
)


# ============================================================
# OLLAMA GENERATION
# ============================================================

async def _generate_with_ollama(
    prompt: str,
) -> str:

    url = (
        f"{OLLAMA_BASE_URL}"
        "/api/chat"
    )

    system_message = """
You are the final answer generator for a financial research
assistant.

Your job is ONLY to produce the final answer to the user's
question.

IMPORTANT:

- Do not repeat these instructions.
- Do not describe these instructions.
- Do not say that you are going to analyze the question.
- Do not say that you will follow rules.
- Do not produce a plan.
- Do not produce internal reasoning.
- Do not mention prompts, agents, tasks, retrieval, embeddings,
  ChromaDB, Ollama, or system instructions.
- Do not repeat the user's question.
- Do not output JSON unless the user explicitly asks for JSON.

DOCUMENT EVIDENCE:

If document evidence is supplied, use it as the primary source.

For financial numbers:
- Use only supplied document evidence.
- Never invent financial numbers.
- Preserve the source unit exactly. If a statement is in millions, 94,827 means
  $94,827 million = $94.827 billion, never $94.827 million.
- Do not silently change million/billion units.
- Include [Page X] when a page number is available.

For historical questions about the company:
- Treat the uploaded annual report as the authoritative source.
- If the user says "downfall", "downturn", "what went wrong", "problems faced",
  or similar informal wording, interpret it as negative performance, declines,
  challenges, risks, or adverse factors reported in the annual report. The exact
  word used by the user does not need to appear in the report.
- Do not replace missing report evidence with general model knowledge.
- Do not introduce news, reviews, social-media claims, or other outside facts
  unless external web information was explicitly requested/supplied.
- If the report evidence is insufficient, say so instead of guessing.

CURRENT-QUESTION PRIORITY:
- Answer the current user question, not a previous question or previous answer.
- Conversation history, when supplied, is context only for genuine follow-ups.
- Never reuse a previous answer merely because the current question has the
  same topic or financial metric.
- For forward-looking questions such as "how can we increase revenue next year?",
  give document-grounded potential actions/drivers rather than claiming that
  future-year performance has already happened.

EXTERNAL WEB INFORMATION:

If external web information is supplied, clearly identify it
as:

External web information:

Do not present external web information as if it came from
the uploaded financial document.

MODEL KNOWLEDGE:

For historical/company-report questions, do NOT use general model
knowledge to fill gaps in the uploaded report. If the supplied
document evidence is insufficient and no explicit current/web
research was requested, state that the information could not be
found in the uploaded financial document.

Never silently add model knowledge to a document-grounded answer.

FINAL RESPONSE:

Return ONLY the answer that should be shown to the user.

Be concise, clear, and direct.
"""


    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        "stream": False,

        "options": {
            "temperature": 0.0,
            "num_predict": 180,
            # ----------------------------------------------------
            # FIX: explicitly set the context window.
            #
            # Ollama defaults to a small context window (commonly
            # 2048 tokens) unless num_ctx is set here. The grounded
            # prompt built in research_service.py can include up to
            # MAX_EVIDENCE document chunks, MAX_WEB_RESULTS web
            # results, recent chat history, and an 18-rule
            # instruction block -- for open-ended questions (e.g.
            # "give summary of the company") this regularly exceeds
            # 2048 tokens. When that happens, Ollama silently drops
            # or truncates part of the prompt, which is why answers
            # were coming back garbled/incoherent instead of failing
            # cleanly. Raising num_ctx lets the model actually see
            # the full prompt it was given.
            "num_ctx": 8192,
        },
    }


    async with httpx.AsyncClient(
        # ------------------------------------------------------
        # FIX: raised from 90.0 -> 180.0 as a safety net.
        #
        # This does NOT make generation faster by itself -- it
        # only prevents a legitimately large (but now valid, since
        # num_ctx was raised) prompt from being killed mid-
        # processing and falling back to the raw-chunk-dump
        # fallback in research_service.py before Ollama has a
        # chance to finish. The real latency fix is trimming the
        # prompt size itself (see research_service.py's web content
        # truncation).
        timeout=180.0,
    ) as client:

        response = await client.post(
            url,
            json=payload,
        )

        response.raise_for_status()


    data = response.json()


    if "message" not in data:

        raise RuntimeError(
            f"Unexpected Ollama response: {data}"
        )


    message = data.get(
        "message",
        {},
    )


    content = message.get(
        "content",
        "",
    )


    content = content.strip()


    if not content:

        raise RuntimeError(
            "Ollama returned an empty response."
        )


    return content


# ============================================================
# RESEARCH AGENT
# ============================================================

async def run_research(
    question: str,
    evidence: list[dict],
    web_evidence: list[dict] | None = None,
    calculation_context: str | None = None,
    chat_history: list[dict] | None = None,
) -> str:

    """
    Generate the final Research Agent answer.

    The service already prepares the complete grounded prompt,
    so we do NOT create another CrewAI task description here.

    This prevents duplicate instructions and prevents Llama
    from returning internal task text instead of the answer.
    """

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    #
    # create_research_agent() and create_research_task()
    # remain available for the project's CrewAI architecture,
    # but the final response generator receives the prepared
    # research prompt directly.
    #
    # --------------------------------------------------------

    final_prompt = question.strip()


    # ========================================================
    # Add a final output constraint
    # ========================================================

    final_prompt += """

FINAL OUTPUT REQUIREMENT:

Return ONLY the final answer to the user's question.

Do not repeat the instructions above.

Do not explain how you generated the answer.

Do not say "I will", "I can help", "I need to", or
"I'll follow the rules".

Start directly with the answer.
"""


    return await _generate_with_ollama(
        final_prompt
    )
