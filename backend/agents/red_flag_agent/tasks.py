# agents/red_flag_agent/tasks.py
from crewai import Task

AUDITOR_TASK_DESCRIPTION = """
You are given excerpts retrieved from a company's financial filing
(auditor's report and/or related notes). Each excerpt is labeled with
its page number.

Excerpts:
---
{document_text}
---

Classify ONLY what is explicitly stated in these excerpts. Look for:
- Qualified or adverse audit opinions
- Going-concern language / substantial doubt about continuing as a
  going concern
- Material weaknesses in internal control over financial reporting
- Material uncertainties or significant audit observations

Respond with ONLY valid JSON (no markdown fences, no commentary
before or after) in exactly this shape:

{{
  "findings": [
    {{
      "title": "short title",
      "severity": "LOW" | "MEDIUM" | "HIGH",
      "explanation": "why this matters, in your own words",
      "evidence": "short paraphrase of the relevant excerpt (not a verbatim quote)",
      "page_number": <integer or null>
    }}
  ]
}}

If the excerpts do not contain any qualification, going-concern
language, or material weakness disclosure, return:

{{"findings": []}}

Never invent a finding that is not supported by the excerpts above.
"""


def create_red_flag_task(agent, document_text: str):
    return Task(
        description=AUDITOR_TASK_DESCRIPTION.format(document_text=document_text),
        expected_output=(
            "A single valid JSON object with a 'findings' array, and "
            "nothing else."
        ),
        agent=agent,
    )