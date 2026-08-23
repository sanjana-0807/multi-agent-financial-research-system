# agents/comparison_agent/tasks.py
from crewai import Task

COMPARISON_TASK_DESCRIPTION = """
You are given a pre-computed financial comparison table across two or
more companies. Every number below was already calculated
deterministically -- do not recompute, adjust, round differently, or
invent any figure.

{comparison_context}

Write a short analyst-style narrative summarizing the comparison.
Respond with ONLY valid JSON (no markdown fences, no commentary before
or after) in exactly this shape:

{{
  "summary": "2-4 sentence overview of how the companies compare",
  "highlights": [
    {{
      "metric": "exact metric name from the table",
      "finding": "one sentence citing the ticker(s) and value(s) involved"
    }}
  ]
}}

Rules:
- Every ticker, metric name, and number you mention must appear in the
  table above exactly as given.
- Do not use outside knowledge about these companies.
- Keep "highlights" to the 3-5 most meaningful differences.
- Return JSON only.
"""


def create_comparison_task(agent, comparison_context: str):
    return Task(
        description=COMPARISON_TASK_DESCRIPTION.format(
            comparison_context=comparison_context
        ),
        expected_output=(
            "A single valid JSON object with 'summary' and 'highlights' "
            "keys, and nothing else."
        ),
        agent=agent,
    )