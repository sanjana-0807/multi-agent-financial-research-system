# agents/comparison_agent/crew.py
import json
import re

from crewai import Crew, Process

from agents.comparison_agent.agent import create_comparison_agent
from agents.comparison_agent.tasks import create_comparison_task


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output: {raw[:200]}")
    return json.loads(match.group(0))


async def run_comparison_narrative(comparison_context: str) -> dict:
    """
    Runs the Comparison Agent's crew against an already-computed
    numeric comparison table and returns:

        {"summary": "...", "highlights": [{"metric": ..., "finding": ...}]}

    Falls back to an empty-but-valid shape if the model output can't be
    parsed, so a flaky LLM call never breaks the deterministic numbers
    already stored on the ComparisonResult -- the numeric comparison
    itself does not depend on this succeeding.

    Uses kickoff_async() because this is always called from FastAPI's
    async event loop (see services/comparison_service.py) -- CrewAI's
    synchronous kickoff() raises RuntimeError if invoked from inside a
    running event loop.
    """
    agent = create_comparison_agent()
    task = create_comparison_task(agent, comparison_context)

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
        return {"summary": None, "highlights": []}

    return {
        "summary": parsed.get("summary"),
        "highlights": parsed.get("highlights", []),
    }