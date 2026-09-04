import re
from typing import Optional


# =========================================================
# METRIC DETECTION
# =========================================================

def detect_metric(question: str) -> Optional[str]:
    """
    Detect the primary financial metric requested by the user.

    Specific metrics are checked before generic metrics.
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
    # OPERATING CASH FLOW
    # -----------------------------------------------------

    if (
        "operating cash flow" in q
        or "operating cash flows" in q
        or "cash flow from operating activities" in q
        or "cash flows from operating activities" in q
        or "cash provided by operating activities" in q
        or "net cash provided by operating activities" in q
        or "cash generated from operations" in q
        or "operating cash" in q
    ):
        return "operating_cash_flow"

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

    if (
        "revenue" in q
        or "revenues" in q
    ):
        return "revenue"

    return None


# =========================================================
# MULTI-METRIC DETECTION
# =========================================================

def detect_metrics(question: str) -> list[str]:
    """
    Detect all financial metrics requested by the user.
    """

    if not question:
        return []

    q = question.lower()

    metrics = []

    # -----------------------------------------------------
    # REVENUE / SALES
    # -----------------------------------------------------

    if "net sales" in q:
        metrics.append("net_sales")

    elif (
        "total revenue" in q
        or "total revenues" in q
    ):
        metrics.append("total_revenue")

    elif (
        "revenue" in q
        or "revenues" in q
    ):
        metrics.append("revenue")

    # -----------------------------------------------------
    # OPERATING INCOME
    # -----------------------------------------------------

    if (
        "operating income" in q
        or "operating profit" in q
    ):
        metrics.append("operating_income")

    # -----------------------------------------------------
    # NET INCOME
    # -----------------------------------------------------

    if (
        "net income attributable to walmart" in q
        or "net income attributable to wal-mart" in q
    ):
        metrics.append("net_income_attributable")

    elif (
        "net income" in q
        or "net profit" in q
    ):
        metrics.append("net_income")

    # -----------------------------------------------------
    # OPERATING CASH FLOW
    # -----------------------------------------------------

    if (
        "operating cash flow" in q
        or "operating cash flows" in q
        or "cash flow from operating activities" in q
        or "cash flows from operating activities" in q
        or "cash provided by operating activities" in q
        or "net cash provided by operating activities" in q
        or "cash generated from operations" in q
        or "cash generated" in q
        or "cashflow" in q
    ):
        metrics.append("operating_cash_flow")

    # -----------------------------------------------------
    # EPS
    # -----------------------------------------------------

    if (
        "diluted eps" in q
        or "diluted earnings per share" in q
    ):
        metrics.append("diluted_eps")

    elif (
        "eps" in q
        or "earnings per share" in q
    ):
        metrics.append("eps")

    # -----------------------------------------------------
    # GROSS PROFIT
    # -----------------------------------------------------

    if "gross profit" in q:
        metrics.append("gross_profit")

    # -----------------------------------------------------
    # GROSS MARGIN
    # -----------------------------------------------------

    if "gross margin" in q:
        metrics.append("gross_margin")

    # -----------------------------------------------------
    # PROFITABILITY
    # -----------------------------------------------------

    if "profitability" in q:

        if "operating_income" not in metrics:
            metrics.append("operating_income")

        if "net_income" not in metrics:
            metrics.append("net_income")

    return list(dict.fromkeys(metrics))


# =========================================================
# YEAR EXTRACTION
# =========================================================

def extract_year(question: str) -> Optional[str]:
    """
    Extract the first year from the user's question.

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


def extract_years(question: str) -> list[str]:
    """
    Extract all distinct years from a question.

    Example:
        "What was revenue in 2023, 2024, and 2025?"

    Returns:
        ["2023", "2024", "2025"]
    """

    if not question:
        return []

    years = re.findall(
        r"\b(?:fiscal\s+|fy\s*)?(20\d{2})\b",
        question.lower(),
    )

    return list(dict.fromkeys(years))