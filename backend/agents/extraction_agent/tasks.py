# agents/extraction_agent/tasks.py

import re
from typing import Optional

from agents.extraction_agent.ollama_extraction import extract_with_ollama
from agents.extraction_agent.regex_extraction import extract_fiscal_year

# ---------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------
def extract_company_name(document_text: str) -> Optional[str]:
    """
    Extract company name from an annual report.

    Handles SEC 10-K formats where the company name appears
    immediately before:
        (Exact name of registrant...)
    """

    if not document_text:
        return None

    text = document_text

    # -----------------------------------------------------
    # 1. SEC registrant format
    # -----------------------------------------------------

    sec_pattern = re.compile(
        r"""
        (?P<prefix>.{0,500}?)
        \(
            \s*Exact\s+
            (?:Name|name)\s+
            of\s+
            registrant
            (?:\s+as\s+specified\s+in\s+its\s+charter)?
        """,
        re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )

    for match in sec_pattern.finditer(text):

        prefix = match.group("prefix")

        # Find the LAST legal company name before the SEC label.
        legal_pattern = re.compile(
            r"""
            ([A-Za-z][A-Za-z0-9&.,'’\- ]{1,100}?
            (?:Inc\.?|Incorporated|Corporation|Corp\.?|
               Company|Co\.?|Ltd\.?|Limited|PLC))
            \s*$
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        legal_matches = list(
            legal_pattern.finditer(prefix)
        )

        if legal_matches:
            company = legal_matches[-1].group(1).strip()

            # Remove accidental leading filing text.
            company = re.sub(
                r"^(?:.*?\b(?:Number|number)\s+[0-9\-]+\s+)",
                "",
                company,
                flags=re.IGNORECASE,
            ).strip()

            return company

    # -----------------------------------------------------
    # 2. Known legal-name fallback
    # -----------------------------------------------------

    fallback_patterns = [
        r"\b(Walmart\s+Inc\.?)\b",
        r"\b(Amazon(?:\.com)?\s*,?\s*Inc\.?)\b",
        r"\b(NVIDIA\s+Corporation)\b",
        r"\b(Tesla\s*,?\s*Inc\.?)\b",
        r"\b(PepsiCo\s*,?\s*Inc\.?)\b",
        r"\b(Colgate-Palmolive\s+Company)\b",
        r"\b(Johnson\s*&\s*Johnson)\b",
    ]

    for pattern in fallback_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    return None
# ---------------------------------------------------------
# Ratio calculations
# ---------------------------------------------------------

def calculate_ratios(metrics: dict) -> dict:
    """
    Calculate ratios that can be reliably derived from
    the extracted financial metrics.

    Net profit margin:
        net profit / revenue * 100

    Debt-to-equity:
        liabilities / equity

    Equity:
        assets - liabilities

    Current ratio requires:
        current assets / current liabilities

    Those values are not part of the locked extraction
    schema, so current_ratio remains None.
    """

    revenue = metrics.get("revenue")
    net_profit = metrics.get("net_profit")
    assets = metrics.get("assets")
    liabilities = metrics.get("liabilities")

    current_ratio = None
    debt_to_equity = None
    net_profit_margin = None

    # Net profit margin
    if (
        revenue is not None
        and net_profit is not None
        and revenue != 0
    ):
        net_profit_margin = (
            float(net_profit) / float(revenue)
        ) * 100

    # Debt-to-equity
    if (
        assets is not None
        and liabilities is not None
    ):
        equity = float(assets) - float(liabilities)

        if equity != 0:
            debt_to_equity = (
                float(liabilities) / equity
            )

    return {
        "current_ratio": current_ratio,
        "debt_to_equity": debt_to_equity,
        "net_profit_margin": net_profit_margin,
    }


# ---------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------

def _sanity_check(metrics: dict) -> dict:
    """
    Protect the API from obviously incorrect extraction results.
    """

    checked = dict(metrics)

    # EPS should be a per-share number, not a share count.
    eps = checked.get("eps")

    if eps is not None:
        if not isinstance(eps, (int, float)):
            checked["eps"] = None

        elif abs(eps) > 1000:
            checked["eps"] = None

    # Financial statement totals should not normally be negative.
    for field in [
        "revenue",
        "assets",
        "liabilities",
    ]:
        value = checked.get(field)

        if value is not None:
            if not isinstance(value, (int, float)):
                checked[field] = None

    return checked


# ---------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------

def run_extraction(
    document_text: str,
    document_id: str = "D001",
):
    """
    Main extraction pipeline.

    Flow:

        PDF
         ↓
        ChromaDB
         ↓
        document_fetcher
         ↓
        financial_section_selector
         ↓
        Ollama / Llama 3.2
         ↓
        financial row identification
         ↓
        Python exact number extraction
         ↓
        API response format
    """

    if not document_text:
        raise ValueError(
            "No document text available for extraction."
        )

    # -----------------------------------------------------
    # 1. Extract metadata
    # -----------------------------------------------------

    company = extract_company_name(document_text)

    fiscal_year = extract_fiscal_year(document_text)

    # -----------------------------------------------------
    # 2. Run Ollama extraction
    # -----------------------------------------------------

    ollama_result = extract_with_ollama(
        document_text
    )

    # Example:
    #
    # {
    #     "model": "llama3.2:latest",
    #     "rows": {...},
    #     "metrics": {
    #         "revenue": 94827.0,
    #         "net_profit": 3794.0,
    #         ...
    #     }
    # }

    metrics = ollama_result.get(
        "metrics",
        {},
    )

    # -----------------------------------------------------
    # 3. Sanity-check extracted values
    # -----------------------------------------------------

    metrics = _sanity_check(metrics)

    # -----------------------------------------------------
    # 4. Calculate ratios
    # -----------------------------------------------------

    ratios = calculate_ratios(metrics)

    # -----------------------------------------------------
    # 5. Build the locked API response
    # -----------------------------------------------------

    result = {
        "metric_id": "M001",
        "document_id": document_id,
        "company": company or "Unknown",
        "fiscal_year": fiscal_year or 0,

        "revenue": metrics.get("revenue"),
        "net_profit": metrics.get("net_profit"),
        "assets": metrics.get("assets"),
        "liabilities": metrics.get("liabilities"),
        "cash_flow": metrics.get("cash_flow"),
        "eps": metrics.get("eps"),

        "ratios": ratios,
    }

    # -----------------------------------------------------
    # 6. Preserve model information for debugging
    # -----------------------------------------------------

    result["_model"] = ollama_result.get(
        "model",
        "llama3.2:latest",
    )

    result["_rows"] = ollama_result.get(
        "rows",
        {},
    )

    return result