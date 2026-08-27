import re
from typing import Optional


# =========================================================
# METRIC DETECTION
# =========================================================

def detect_metric(question: str) -> Optional[str]:
    """
    Detect the financial metric requested by the user.

    Specific metrics are checked before generic metrics.

    Examples:
        net income attributable to Walmart
            -> net_income_attributable

        net income
            -> net_income

        net sales
            -> net_sales
    """

    if not question:
        return None

    q = question.lower().strip()

    # -----------------------------------------------------
    # DILUTED EPS
    # -----------------------------------------------------

    if (
        "diluted earnings per share" in q
        or "diluted eps" in q
    ):
        return "diluted_eps"

    # -----------------------------------------------------
    # EPS
    # -----------------------------------------------------

    if (
        "earnings per share" in q
        or re.search(r"\beps\b", q)
    ):
        return "eps"

    # -----------------------------------------------------
    # NET INCOME ATTRIBUTABLE
    # MUST COME BEFORE NET INCOME
    # -----------------------------------------------------

    if (
        "net income attributable to walmart" in q
        or "net income attributable to wal-mart" in q
        or "consolidated net income attributable to walmart" in q
        or "consolidated net income attributable to wal-mart" in q
    ):
        return "net_income_attributable"

    # -----------------------------------------------------
    # TOTAL REVENUE
    # -----------------------------------------------------

    if (
        "total revenue" in q
        or "total revenues" in q
    ):
        return "total_revenue"

    # -----------------------------------------------------
    # NET SALES
    # MUST COME BEFORE REVENUE
    # -----------------------------------------------------

    if "net sales" in q:
        return "net_sales"

    # -----------------------------------------------------
    # OPERATING INCOME
    # -----------------------------------------------------

    if (
        "operating income" in q
        or "operating profit" in q
    ):
        return "operating_income"

    # -----------------------------------------------------
    # GROSS MARGIN
    # MUST COME BEFORE GROSS PROFIT
    # -----------------------------------------------------

    if "gross margin" in q:
        return "gross_margin"

    # -----------------------------------------------------
    # GROSS PROFIT
    # -----------------------------------------------------

    if "gross profit" in q:
        return "gross_profit"

    # -----------------------------------------------------
    # NET INCOME
    # -----------------------------------------------------

    if "net income" in q:
        return "net_income"

    # -----------------------------------------------------
    # REVENUE
    # -----------------------------------------------------

    if "revenue" in q:
        return "revenue"

    return None


# =========================================================
# YEAR EXTRACTION
# =========================================================

def extract_year(question: str) -> Optional[str]:
    """
    Extract a year from the user's question.

    Examples:
        fiscal 2025 -> 2025
        FY 2025     -> 2025
        2025        -> 2025
    """

    if not question:
        return None

    match = re.search(
        r"\b(?:fiscal\s+|fy\s*)?(20\d{2})\b",
        question.lower(),
    )

    if match:
        return match.group(1)

    return None