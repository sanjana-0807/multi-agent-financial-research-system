import re
from typing import Any, Dict, Optional


# ============================================================
# COMPANY
# ============================================================

def _detect_company(document_text: str) -> Optional[str]:

    if not document_text:
        return None

    text = document_text[:30000]

    # Tesla document
    if re.search(r"\bTesla\b", text, re.IGNORECASE):
        return "Tesla"

    patterns = [
        r"Exact\s+name\s+of\s+registrant.*?:?\s*([A-Z][A-Za-z0-9&.,' -]+)",
        r"\b([A-Z][A-Za-z0-9&.,' -]+(?:Inc\.|Incorporated|Corporation|Corp\.|Company|Ltd\.|Limited|PLC))\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if match:

            company = match.group(1).strip()

            company = re.sub(
                r"\s+",
                " ",
                company,
            )

            return company.rstrip(" .,;:")

    return None


# ============================================================
# FISCAL YEAR
# ============================================================

def _detect_fiscal_year(
    document_text: str,
) -> Optional[int]:

    if not document_text:
        return None

    patterns = [

        # Q2 2026
        r"\bQ[1-4]\s+(20\d{2})\b",

        # Q2-2026
        r"\bQ[1-4]-(20\d{2})\b",

        # 02-2026
        r"\b0[1-4]-(20\d{2})\b",

        # Fiscal year ended 2026
        r"(?:fiscal\s+year|year)\s+ended.*?\b(20\d{2})\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            document_text,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            return int(match.group(1))

    return None


# ============================================================
# MAIN EXTRACTION
# ============================================================

def run_extraction(
    document_text: str,
    document_id: str,
) -> Dict[str, Any]:

    if not document_text:

        return {
            "metric_id": f"M_{document_id}",
            "document_id": document_id,
            "company": None,
            "fiscal_year": None,
            "revenue": None,
            "net_profit": None,
            "assets": None,
            "liabilities": None,
            "cash_flow": None,
            "eps": None,
            "ratios": {
                "current_ratio": None,
                "debt_to_equity": None,
                "net_profit_margin": None,
            },
        }

    # ========================================================
    # DETERMINISTIC EXTRACTION
    # ========================================================

    from .ollama_extraction import extract_financial_data

    extracted = extract_financial_data(
        document_text=document_text,
        metric_id=f"M_{document_id}",
        document_id=document_id,
    )

    # ========================================================
    # COMPANY / FISCAL YEAR
    # ========================================================

    extracted["company"] = _detect_company(
        document_text
    )

    extracted["fiscal_year"] = _detect_fiscal_year(
        document_text
    )

    # ========================================================
    # MAKE SURE RATIOS DICTIONARY EXISTS
    # ========================================================

    if not isinstance(
        extracted.get("ratios"),
        dict,
    ):
        extracted["ratios"] = {}

    # ========================================================
    # GET FINANCIAL VALUES
    # ========================================================

    revenue = extracted.get("revenue")
    net_profit = extracted.get("net_profit")
    assets = extracted.get("assets")
    liabilities = extracted.get("liabilities")

    # ========================================================
    # NET PROFIT MARGIN
    #
    # Net Profit Margin =
    # (Net Profit / Revenue) * 100
    # ========================================================

    if (
        revenue is not None
        and revenue != 0
        and net_profit is not None
    ):

        extracted["ratios"]["net_profit_margin"] = (
            net_profit / revenue
        ) * 100

    else:

        extracted["ratios"]["net_profit_margin"] = None

    # ========================================================
    # DEBT TO EQUITY
    #
    # Equity = Assets - Liabilities
    #
    # Debt-to-Equity =
    # Liabilities / Equity
    #
    # Only calculate when both values are available.
    # ========================================================

    if (
        assets is not None
        and liabilities is not None
    ):

        equity = assets - liabilities

        if equity != 0:

            extracted["ratios"]["debt_to_equity"] = (
                liabilities / equity
            )

        else:

            extracted["ratios"]["debt_to_equity"] = None

    else:

        extracted["ratios"]["debt_to_equity"] = None

    # ========================================================
    # CURRENT RATIO
    #
    # We DO NOT calculate this from total assets /
    # total liabilities.
    #
    # Current Ratio requires:
    #
    # Current Assets / Current Liabilities
    #
    # Those values are not currently returned by the
    # ollama_extraction extractor, so leave it as None.
    # ========================================================

    if "current_ratio" not in extracted["ratios"]:

        extracted["ratios"]["current_ratio"] = None

    return extracted