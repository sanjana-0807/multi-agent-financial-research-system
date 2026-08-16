import re
from typing import Optional, Dict, Any


# ---------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------

NUMBER_RE = re.compile(
    r"""
    (?:
        \$\s*
        |₹\s*
        |Rs\.?\s*
    )?
    \(?\s*
    -?
    (?:\d{1,3}(?:,\d{3})+|\d+)
    (?:\.\d+)?
    \s*
    (?:billion|million|thousand|bn|mn|m)?
    \s*\)?
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_number(value: str) -> Optional[float]:
    if not value:
        return None

    value = value.strip()

    negative = value.startswith("(") and value.endswith(")")

    value = re.sub(
        r"^(?:\$|₹|Rs\.?)\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )

    multiplier = 1

    lower = value.lower()

    if "billion" in lower or re.search(r"\bbn\b", lower):
        multiplier = 1_000_000_000
    elif "million" in lower or re.search(r"\bmn\b", lower):
        multiplier = 1_000_000
    elif "thousand" in lower:
        multiplier = 1_000

    value = re.sub(
        r"\b(?:billion|million|thousand|bn|mn|m)\b",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = (
        value
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    try:
        result = float(value) * multiplier
        return -result if negative else result
    except ValueError:
        return None


# ---------------------------------------------------------
# Extract numeric candidates
# ---------------------------------------------------------

def numeric_candidates(text: str):
    results = []

    for match in NUMBER_RE.finditer(text):
        raw = match.group(0).strip()

        value = parse_number(raw)

        if value is None:
            continue

        # Ignore years
        if 1900 <= abs(value) <= 2100:
            continue

        results.append((match.start(), match.end(), raw, value))

    return results


# ---------------------------------------------------------
# Statement-aware metric extraction
# ---------------------------------------------------------

def extract_table_value(
    text: str,
    labels: list[str],
    search_distance: int = 1000,
) -> Optional[float]:

    normalized = re.sub(r"[ \t]+", " ", text)

    candidates = []

    for label in labels:

        for match in re.finditer(
            rf"\b{label}\b",
            normalized,
            re.IGNORECASE,
        ):

            start = match.end()
            end = min(
                len(normalized),
                start + search_distance,
            )

            after = normalized[start:end]

            # Stop at obvious narrative boundaries.
            after = re.split(
                r"\n\s*\n|(?=\b(?:The |Our |In 20\d{2}|We |This |These ))",
                after,
                maxsplit=1,
            )[0]

            numbers = numeric_candidates(after)

            if not numbers:
                continue

            # Strong preference for a financial-table pattern:
            # multiple numbers close together.
            score = 0

            if len(numbers) >= 2:
                score += 5

            if len(numbers) >= 3:
                score += 3

            # Currency markers strongly suggest a financial table.
            if "$" in after or "₹" in after or "Rs." in after:
                score += 3

            # Percentage-heavy text is usually a chart,
            # not the target financial statement.
            percent_count = after.count("%")

            if percent_count >= 2:
                score -= 5

            # Narrative phrases are weaker candidates.
            if re.search(
                r"\b(?:representing|compared to|decrease of|increase of)\b",
                after,
                re.IGNORECASE,
            ):
                score -= 4

            candidates.append(
                (
                    score,
                    numbers[0][3],
                    after[:250],
                )
            )

    if not candidates:
        return None

    # Highest-scoring candidate wins.
    candidates.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return candidates[0][1]


# ---------------------------------------------------------
# Company
# ---------------------------------------------------------

def extract_company(text: str) -> Optional[str]:
    """
    Dynamically extract the company name from an annual report.

    This function does not contain company-specific rules.
    """

    if not text:
        return None

    text = text[:30000]

    patterns = [
        # -----------------------------------------------------
        # SEC registrant format
        # -----------------------------------------------------
        r"""
        (?:Exact\s+name\s+of\s+registrant
        |Exact\s+name\s+of\s+registrant\s+as\s+specified\s+in\s+its\s+charter)
        \s*[:\-]?\s*
        ([A-Z][A-Za-z0-9&.,'’\- ]{2,100}?)
        (?:
            \s*\(|\s*
            Commission\s+File\s+Number|
            \s+I\.R\.S\.|
            \s+IRS
        )
        """,

        # -----------------------------------------------------
        # Company & Consolidated Subsidiaries
        # -----------------------------------------------------
        r"""
        \b(
            [A-Z][A-Za-z0-9&.,'’\- ]{2,100}?
            (?:Inc\.?|Incorporated|Corporation|Corp\.?|Company|
               Co\.?|Ltd\.?|Limited|PLC)
        )
        \s*(?:&|and)\s+
        (?:Consolidated\s+)?(?:Subsidiaries|Companies)
        \b
        """,

        # -----------------------------------------------------
        # Company and Subsidiaries
        # -----------------------------------------------------
        r"""
        \b(
            [A-Z][A-Za-z0-9&.,'’\- ]{2,100}?
            (?:Inc\.?|Incorporated|Corporation|Corp\.?|Company|
               Co\.?|Ltd\.?|Limited|PLC)
        )
        \s+(?:and|&)
        \s+(?:Consolidated\s+)?Subsidiaries
        \b
        """,

        # -----------------------------------------------------
        # Generic legal company name
        # -----------------------------------------------------
        r"""
        \b(
            [A-Z][A-Za-z0-9&.,'’\- ]{2,100}?
            (?:Inc\.?|Incorporated|Corporation|Corp\.?|Company|
               Co\.?|Ltd\.?|Limited|PLC)
        )
        \b
        """,
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.VERBOSE,
        )

        if match:

            company = match.group(1).strip()

            company = re.sub(
                r"\s+",
                " ",
                company,
            )

            company = company.rstrip(
                " .,;:"
            )

            return company

    return None

# ---------------------------------------------------------
# Fiscal year
# ---------------------------------------------------------

def extract_fiscal_year(text: str) -> Optional[int]:

    patterns = [
        r"fiscal year ended.*?\b(20\d{2})\b",
        r"year ended.*?\b(20\d{2})\b",
        r"\b(20\d{2})\s+Annual Report\b",
    ]

    for pattern in patterns:

        match = re.search(
             pattern,
               text,
                 re.IGNORECASE | re.DOTALL,
        )

        if match:
            return int(match.group(1))

    return None


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------

def extract_revenue(text: str):

    return extract_table_value(
        text,
        [
            r"Total revenues",
            r"Total revenue",
            r"Net sales",
            r"Net revenues",
            r"Total net sales",
        ],
    )


def extract_net_profit(text: str):

    return extract_table_value(
        text,
        [
            r"Net income attributable to common stockholders",
            r"Net income attributable to .*?stockholders",
            r"Net income attributable to .*?shareholders",
            r"Net income",
            r"Net earnings",
            r"Net profit",
        ],
    )


def extract_assets(text: str):

    return extract_table_value(
        text,
        [r"Total assets"],
        search_distance=500,
    )


def extract_liabilities(text: str):

    return extract_table_value(
        text,
        [r"Total liabilities"],
        search_distance=500,
    )


def extract_cash_flow(text: str):

    return extract_table_value(
        text,
        [
            r"Net cash provided by operating activities",
            r"Net cash provided by operations",
            r"Cash provided by operating activities",
            r"Operating cash flow",
        ],
        search_distance=500,
    )


def extract_eps(text: str):

    return extract_table_value(
        text,
        [
            r"Diluted earnings per share",
            r"Basic earnings per share",
            r"Earnings per share",
            r"Diluted EPS",
            r"Basic EPS",
        ],
        search_distance=500,
    )


def extract_current_ratio(text: str):

    return extract_table_value(
        text,
        [
            r"Current ratio",
        ],
        search_distance=100,
    )


def extract_debt_to_equity(text: str):

    return extract_table_value(
        text,
        [
            r"Debt-to-equity ratio",
            r"Debt to equity ratio",
            r"Debt/equity ratio",
        ],
        search_distance=100,
    )


# ---------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------

def extract_financial_data(
    document_text: str,
    metric_id: str,
    document_id: str,
) -> Dict[str, Any]:

    if not document_text:
        return {
            "metric_id": metric_id,
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

    company = extract_company(document_text)

    fiscal_year = extract_fiscal_year(document_text)

    revenue = extract_revenue(document_text)

    net_profit = extract_net_profit(document_text)

    assets = extract_assets(document_text)

    liabilities = extract_liabilities(document_text)

    cash_flow = extract_cash_flow(document_text)

    eps = extract_eps(document_text)

    current_ratio = extract_current_ratio(document_text)

    debt_to_equity = extract_debt_to_equity(document_text)

    if revenue is not None and revenue != 0 and net_profit is not None:
        net_profit_margin = (
            net_profit / revenue
        ) * 100
    else:
        net_profit_margin = None

    return {
        "metric_id": metric_id,
        "document_id": document_id,
        "company": company,
        "fiscal_year": fiscal_year,
        "revenue": revenue,
        "net_profit": net_profit,
        "assets": assets,
        "liabilities": liabilities,
        "cash_flow": cash_flow,
        "eps": eps,
        "ratios": {
            "current_ratio": current_ratio,
            "debt_to_equity": debt_to_equity,
            "net_profit_margin": net_profit_margin,
        },
    }