import json
from crewai import Task, Crew
from agents.extraction_agent.agent import extraction_agent


def build_extraction_task(document_text, document_id="D001"):
    return Task(
        description=f"""
Read the following financial document text and extract these fields:
- company (string)
- fiscal_year (integer)
- revenue (number)
- net_profit (number)
- assets (number)
- liabilities (number)
- cash_flow (number)
- eps (number)
- ratios.current_ratio (number)
- ratios.debt_to_equity (number)
- ratios.net_profit_margin (number)

IMPORTANT UNIT RULE:
revenue, net_profit, assets, liabilities, and cash_flow are typically reported
"in thousands" or "in millions" in the source text - extract them exactly as
stated in the document, with no additional scaling.

eps (Earnings Per Share) is ALWAYS a small raw per-share dollar amount
(e.g. 8.47, 6.13) - it is NEVER reported in thousands or millions, and must
NEVER be multiplied, scaled, or converted by any factor. Copy the eps number
exactly as it appears in the text, character for character, converted to a
plain decimal.

If current_ratio, debt_to_equity, or net_profit_margin are not directly stated,
calculate them from the other extracted numbers:
current_ratio = current_assets / current_liabilities
debt_to_equity = liabilities / (assets - liabilities)
net_profit_margin = (net_profit / revenue) * 100

If a field cannot be found or calculated, set it to null. Do not invent numbers.

DOCUMENT TEXT:
{document_text}

Return ONLY valid JSON, no markdown, no explanation, in exactly this shape:
{{
  "metric_id": "M001",
  "document_id": "{document_id}",
  "company": "",
  "fiscal_year": 0,
  "revenue": 0,
  "net_profit": 0,
  "assets": 0,
  "liabilities": 0,
  "cash_flow": 0,
  "eps": 0,
  "ratios": {{
    "current_ratio": 0,
    "debt_to_equity": 0,
    "net_profit_margin": 0
  }}
}}
""",
        expected_output="A single valid JSON object matching the schema above.",
        agent=extraction_agent,
    )


def _sanity_check(result: dict) -> dict:
    """
    Catches the exact class of bug we saw in production: EPS coming back
    scaled up by ~100,000x instead of as a raw per-share dollar value.
    Real-world EPS for any public company is virtually always under 1000.
    If it's wildly out of range, we don't silently trust it - we null it
    out and flag it so the frontend/team can see something went wrong
    instead of displaying a nonsense number.
    """
    eps = result.get("eps")
    if eps is not None and isinstance(eps, (int, float)) and abs(eps) > 1000:
        result["eps"] = None
        result["_warnings"] = result.get("_warnings", [])
        result["_warnings"].append(
            f"eps value {eps} was out of realistic range and has been nulled out - "
            "check the raw agent output for a scaling/extraction error"
        )
    return result


def run_extraction(document_text, document_id="D001"):
    task = build_extraction_task(document_text, document_id)
    crew = Crew(agents=[extraction_agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    raw = str(result).strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        parsed = json.loads(raw)
        return _sanity_check(parsed)
    except json.JSONDecodeError:
        return {"error": "could not parse output as json", "raw_output": raw}
