import re
from typing import Optional


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalize_text(text: str) -> str:
    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


# ============================================================
# NUMBER PARSER
# ============================================================

def _parse_number(value: str) -> Optional[float]:

    if not value:
        return None

    value = value.strip()

    negative = (
        value.startswith("(")
        and value.endswith(")")
    )

    value = (
        value
        .replace("$", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    try:
        number = float(value)
    except ValueError:
        return None

    if negative:
        number = -number

    return number


# ============================================================
# FINANCIAL ROW PATTERNS
# ============================================================

def _get_row_patterns(metric: str) -> list[str]:

    metric = metric.lower().strip()

    if metric in (
        "total revenue",
        "total revenues",
        "revenue",
        "revenues",
        "net sales",
        "sales",
    ):

        return [
            r"total\s+revenues?",
            r"total\s+revenue",
            r"net\s+sales",
            r"revenue",
            r"revenues",
        ]

    if metric in (
        "net income",
        "net profit",
    ):

        return [
            r"net\s+income",
            r"net\s+profit",
        ]

    if metric == "gross profit":

        return [
            r"gross\s+profit",
        ]

    if metric in (
        "operating income",
        "operating profit",
        "income from operations",
    ):

        return [
            r"income\s+from\s+operations",
            r"operating\s+income",
            r"operating\s+profit",
        ]

    return [
        re.escape(metric)
    ]


# ============================================================
# FIND YEAR SEQUENCE NEAR METRIC ROW
# ============================================================

def _find_year_sequence_near_row(
    text: str,
    row_start: int,
) -> list[int]:

    # Look only before the row.
    #
    # This is important because annual reports contain many
    # years elsewhere in the same chunk.

    start = max(
        0,
        row_start - 1000,
    )

    preceding = text[
        start:row_start
    ]

    # Find years in their displayed order.
    matches = re.findall(
        r"\b20\d{2}\b",
        preceding,
    )

    years = [
        int(year)
        for year in matches
    ]

    # Remove duplicates but preserve order.
    years = list(
        dict.fromkeys(
            years
        )
    )

    # Financial statements normally show 2–4 years.
    if len(years) > 4:

        years = years[-4:]

    return years


# ============================================================
# EXTRACT NUMBERS AFTER ROW LABEL
# ============================================================

def _extract_row_numbers(
    row_text: str,
) -> list[float]:

    if not row_text:
        return []

    pattern = re.compile(
        r"""
        (?:
            \$
            \s*
        )?
        (
            \(
                \s*
                \d[\d,]*
                (?:\.\d+)?
                \s*
            \)
            |
            \d[\d,]*
            (?:\.\d+)?
        )
        """,
        re.VERBOSE,
    )

    values = []

    for match in pattern.finditer(
        row_text
    ):

        value = _parse_number(
            match.group(1)
        )

        if value is not None:
            values.append(
                value
            )

    return values


# ============================================================
# FIND HIGH-CONFIDENCE FINANCIAL ROW
# ============================================================

def _find_financial_row(
    text: str,
    metric: str,
) -> list[tuple[int, str, int]]:

    """
    Returns candidate rows as:

        (
            score,
            row_text,
            row_position
        )

    Higher score = stronger financial-table match.
    """

    if not text:
        return []

    normalized = _normalize_text(
        text
    )

    patterns = _get_row_patterns(
        metric
    )

    candidates = []

    # --------------------------------------------------------
    # Strategy 1:
    # Look for a row where the metric is immediately followed
    # by multiple financial numbers.
    # --------------------------------------------------------

    for pattern in patterns:

        regex = re.compile(
            rf"""
            (?<![\w])
            (?P<label>{pattern})
            (?![\w])
            \s*
            (?P<values>
                (?:
                    \$?\s*
                    \(
                        \s*
                        \d[\d,]*
                        (?:\.\d+)?
                        \s*
                    \)
                    |
                    \$?\s*
                    \d[\d,]*
                    (?:\.\d+)?
                )
                (?:
                    \s+
                    \$?\s*
                    \(
                        \s*
                        \d[\d,]*
                        (?:\.\d+)?
                        \s*
                    \)
                    |
                    \s+
                    \$?\s*
                    \d[\d,]*
                    (?:\.\d+)?
                )
                {1,5}
            )
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        for match in regex.finditer(
            normalized
        ):

            row_start = match.start()
            row_end = match.end()

            row_text = normalized[
                row_start:row_end
            ]

            numbers = _extract_row_numbers(
                match.group("values")
            )

            if len(numbers) < 2:
                continue

            label = (
                match.group("label")
                .lower()
                .strip()
            )

            score = 0

            # Exact "Revenue" row is stronger than
            # a generic occurrence of revenue.
            if label == "revenue":
                score += 100

            if label in (
                "total revenue",
                "total revenues",
            ):
                score += 100

            if label == "net sales":
                score += 90

            # More values generally means a proper
            # multi-year financial statement row.
            if len(numbers) >= 3:
                score += 30

            # Strong signal: consolidated income statement.
            context_start = max(
                0,
                row_start - 600,
            )

            context = normalized[
                context_start:row_start
            ].lower()

            if (
                "consolidated statements of income"
                in context
            ):
                score += 100

            if (
                "consolidated statement of income"
                in context
            ):
                score += 100

            if (
                "income statement"
                in context
            ):
                score += 80

            # Strong signal: nearby "cost of revenue".
            after_context = normalized[
                row_end:min(
                    len(normalized),
                    row_end + 300,
                )
            ].lower()

            if "cost of revenue" in after_context:
                score += 60

            candidates.append(
                (
                    score,
                    row_text,
                    row_start,
                )
            )

    # Highest confidence first.
    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_metric_value(
    text: str,
    metric: str,
    year: int,
) -> Optional[float]:

    if not text:
        return None

    if not metric:
        return None

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    normalized = _normalize_text(
        text
    )

    # --------------------------------------------------------
    # Find high-confidence financial rows
    # --------------------------------------------------------

    candidates = _find_financial_row(
        normalized,
        metric,
    )

    if not candidates:
        return None

    # --------------------------------------------------------
    # Evaluate candidates
    # --------------------------------------------------------

    best_value = None
    best_score = -1

    for score, row_text, row_start in candidates:

        # Find the years associated with THIS row.
        years = _find_year_sequence_near_row(
            normalized,
            row_start,
        )

        if year not in years:
            continue

        year_index = years.index(
            year
        )

        numbers = _extract_row_numbers(
            row_text
        )

        if year_index >= len(numbers):
            continue

        value = numbers[
            year_index
        ]

        if score > best_score:

            best_score = score
            best_value = value

    return best_value


# ============================================================
# PERCENTAGE CHANGE
# ============================================================

def calculate_percentage_change(
    old_value: float,
    new_value: float,
) -> float:

    if old_value == 0:
        raise ValueError(
            "Cannot calculate percentage change from zero."
        )

    return (
        (
            new_value
            - old_value
        )
        / old_value
    ) * 100