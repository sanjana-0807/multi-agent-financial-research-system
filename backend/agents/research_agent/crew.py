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
- Include [Page X] when a page number is available.

EXTERNAL WEB INFORMATION:

If external web information is supplied, clearly identify it
as:

External web information:

Do not present external web information as if it came from
the uploaded financial document.

MODEL KNOWLEDGE:

If the requested information is not available in the supplied
document evidence or external web information, general model
knowledge may be used.

When doing this, explicitly write:

Additional information from AI/model knowledge:

Never pretend model knowledge came from the uploaded document.

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
        },
    }


    async with httpx.AsyncClient(
        timeout=90.0,
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