# agents/report_agent/crew.py

import httpx

from agents.report_agent.agent import create_report_agent
from agents.report_agent.tasks import create_report_task


OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"


async def _generate_with_ollama(prompt: str) -> str:
    """
    Generate the final response using local Ollama.
    """

    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 700,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
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

    content = data["message"].get("content", "").strip()

    if not content:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    return content


async def run_report(
    question: str,
    evidence: dict,
    conversation_context: str = "",
) -> str:
    """
    Generate the final user-facing answer.

    The Report Agent receives evidence collected by the orchestrator
    and does not perform independent document retrieval.
    """

    agent = create_report_agent()

    task = create_report_task(
        agent=agent,
        question=question,
        evidence=evidence,
        conversation_context=conversation_context,
    )

    prompt = task.description

    return await _generate_with_ollama(prompt)