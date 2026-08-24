# agents/red_flag_agent/crew.py
import json
import re

from crewai import Crew, Process

from backend.agents.red_flag_agent.agent import create_red_flag_agent
from backend.agents.red_flag_agent.tasks import create_red_flag_task


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output: {raw[:200]}")
    return json.loads(match.group(0))


async def run_auditor_classification(document_text: str) -> list[dict]:
    """
    Runs the auditor-remarks-only CrewAI crew against the given
    (already keyword-filtered) excerpts and returns a list of finding
    dicts, or an empty list if none were found or output couldn't be
    parsed.

    Uses kickoff_async() because this is always called from FastAPI's
    async event loop (see services/red_flag_service.py) -- CrewAI's
    synchronous kickoff() raises RuntimeError if invoked from inside a
    running event loop.
    """
    agent = create_red_flag_agent()
    task = create_red_flag_task(agent, document_text)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = await crew.kickoff_async()
    raw_output = str(result)

    try:
        parsed = _extract_json(raw_output)
    except (ValueError, json.JSONDecodeError):
        return []

    return parsed.get("findings", [])