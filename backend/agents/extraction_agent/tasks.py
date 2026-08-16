# agents/extraction_agent/tasks.py
from agents.extraction_agent.regex_extraction import extract_financial_data


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
            "check the raw extractor output for a scaling/extraction error"
        )
    return result


def run_extraction(document_text, document_id="D001"):
    result = extract_financial_data(document_text, metric_id="M001", document_id=document_id)
    return _sanity_check(result)