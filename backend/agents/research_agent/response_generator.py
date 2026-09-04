import re
from typing import List, Dict, Optional

from .metrics import detect_metric, detect_metrics, extract_year
from .reasoning import create_research_prompt
from .citation import build_citations

# Research-Agent-only document fallback for broad financial questions.
# This does not modify the Comparison, Extraction, Document, or Red Flag agents.
try:
    from vectorstore.chroma_client import collection
except Exception:
    collection = None


# =========================================================
# HELPERS
# =========================================================

def _normalize_number(number: str) -> str:
    """
    Clean a financial number.

    Example:
        "$674,538" -> "674538"
    """

    if not number:
        return ""

    return (
        str(number)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )


def _format_money(
    number: str,
    text: str = "",
) -> str:
    """
    Format a financial number using the unit
    mentioned in the document.
    """

    number = _normalize_number(number)

    if not number:
        return ""

    try:
        value = float(number)

    except (ValueError, TypeError):
        return ""

    if value.is_integer():
        formatted = f"{int(value):,}"
    else:
        formatted = f"{value:,}"

    text_lower = text.lower()

    if re.search(
        r"amounts?\s+in\s+millions",
        text_lower,
    ):
        return f"${formatted} million"

    if re.search(
        r"amounts?\s+in\s+billions",
        text_lower,
    ):
        return f"${formatted} billion"

    if re.search(
        r"\bin\s+millions\b",
        text_lower,
    ):
        return f"${formatted} million"

    if re.search(
        r"\bin\s+billions\b",
        text_lower,
    ):
        return f"${formatted} billion"

    if "million" in text_lower:
        return f"${formatted} million"

    if "billion" in text_lower:
        return f"${formatted} billion"

    return f"${formatted}"


def _format_eps(number: str) -> str:
    """
    Format earnings per share.

    EPS is a per-share value, so it must NOT inherit
    the 'millions' or 'billions' unit from the table.
    """

    number = _normalize_number(number)

    if not number:
        return ""

    try:
        value = float(number)

    except (ValueError, TypeError):
        return ""

    return f"${value:.2f}"


def _extract_first_number(
    pattern: str,
    text: str,
) -> Optional[str]:
    """
    Return the first captured number from a regex pattern.
    """

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1)

    return None


def _has_consolidated_statement(
    text: str,
) -> bool:
    """
    Check whether the chunk contains a
    consolidated financial statement.
    """

    text_lower = text.lower()

    signals = [
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
    ]

    return any(
        signal in text_lower
        for signal in signals
    )


def _is_segment_chunk(
    text: str,
) -> bool:
    """
    Detect segment-level financial information.

    Examples:
        Walmart U.S.
        Walmart International
        Sam's Club
    """

    if not text:
        return False

    text_lower = text.lower()

    signals = [
        "segment operating income",
        "operating income by segment",
        "segment results",
        "segment net sales",
        "business segment",
        "walmart u.s.",
        "walmart us",
        "walmart international",
        "sam's club",
        "sam’s club",
    ]

    return any(
        signal in text_lower
        for signal in signals
    )


def _is_gross_margin_table(
    text: str,
) -> bool:
    """
    Detect a Walmart-style gross margin table.
    """

    if not text:
        return False

    text_lower = text.lower()

    return (
        "percentage of net sales" in text_lower
        and "gross profit" in text_lower
    )


def _is_company_level_question(
    question: str,
) -> bool:
    """
    Determine whether the question asks about
    Walmart overall rather than a specific segment.
    """

    if not question:
        return True

    q = question.lower()

    segment_terms = [
        "walmart u.s.",
        "walmart us",
        "walmart international",
        "sam's club",
        "sam’s club",
        "segment",
    ]

    return not any(
        term in q
        for term in segment_terms
    )


# =========================================================
# METRIC DETECTION
# =========================================================

def _get_metric(
    question: str,
) -> Optional[str]:
    """
    Use the centralized metric detector from metrics.py.
    """

    try:
        metric = detect_metric(question)

    except Exception:
        return None

    if metric is None:
        return None

    return str(metric)


# =========================================================
# SCORE DIRECT EVIDENCE
# =========================================================

def _evidence_score(
    metric: str,
    text: str,
    chunk: Dict,
) -> int:
    """
    Score how strongly a retrieved chunk supports
    the requested financial metric.
    """

    if not text:
        return -999

    text_lower = text.lower()

    score = 0

    # -----------------------------------------------------
    # CONSOLIDATED STATEMENT
    # -----------------------------------------------------

    if _has_consolidated_statement(text):
        score += 100

    # -----------------------------------------------------
    # METRIC SIGNALS
    # -----------------------------------------------------

    metric_terms = {

        "total_revenue": [
            "total revenues",
            "total revenue",
        ],

        "net_sales": [
            "net sales",
        ],

        "revenue": [
            "revenue",
            "revenues",
        ],

        "operating_income": [
            "operating income",
        ],

        "operating_cash_flow": [
            "operating cash flow",
            "cash flow from operating activities",
            "cash flows from operating activities",
            "cash provided by operating activities",
            "net cash provided by operating activities",
        ],

        "net_income": [
            "consolidated net income",
            "net income",
        ],

        "net_income_attributable": [
            "net income attributable to walmart",
            "consolidated net income attributable to walmart",
        ],

        "diluted_eps": [
            "diluted net income per common share",
            "diluted earnings per share",
            "diluted",
        ],

        "eps": [
            "diluted net income per common share",
            "diluted earnings per share",
            "diluted",
        ],

        "gross_profit": [
            "gross profit",
        ],

        "gross_margin": [
            "gross margin",
            "percentage of net sales",
            "gross profit",
        ],
    }

    for term in metric_terms.get(
        metric,
        [],
    ):

        if term in text_lower:
            score += 30
            break

    # -----------------------------------------------------
    # FISCAL YEAR
    # -----------------------------------------------------

    year = extract_year_from_text(text)

    if year:
        score += 20

    # -----------------------------------------------------
    # TABLE SIGNALS
    # -----------------------------------------------------

    if (
        "fiscal years ended january 31"
        in text_lower
    ):
        score += 30

    if (
        "amounts in millions"
        in text_lower
    ):
        score += 20

    # -----------------------------------------------------
    # GROSS MARGIN TABLE
    # -----------------------------------------------------

    if metric == "gross_margin":

        if _is_gross_margin_table(text):
            score += 100

    # -----------------------------------------------------
    # EPS TABLE SIGNAL
    # -----------------------------------------------------

    if metric in {
        "diluted_eps",
        "eps",
    }:

        if (
            "net income per common share"
            in text_lower
            and "diluted"
            in text_lower
        ):
            score += 80

    # -----------------------------------------------------
    # SEGMENT PENALTY
    # -----------------------------------------------------

    if _is_segment_chunk(text):
        score -= 50

    # -----------------------------------------------------
    # DISTANCE
    # -----------------------------------------------------

    distance = chunk.get("distance")

    if distance is not None:

        try:

            score += max(
                0,
                int(
                    20 -
                    float(distance) * 10
                ),
            )

        except (
            ValueError,
            TypeError,
        ):
            pass

    return score


def extract_year_from_text(
    text: str,
) -> Optional[str]:
    """
    Extract a fiscal year from retrieved text.
    """

    if not text:
        return None

    match = re.search(
        r"\b20\d{2}\b",
        text,
    )

    if match:
        return match.group(0)

    return None


# =========================================================
# CHECK REQUESTED YEAR
# =========================================================

def _question_year(
    question: str,
) -> Optional[str]:
    """
    Get the primary year from metrics.py.
    """

    try:
        return extract_year(question)

    except Exception:
        return None


def _question_years(
    question: str,
) -> List[str]:
    """
    Extract all fiscal years mentioned in the question.

    Example:
        2025, 2024, 2023

    Returns:
        ["2025", "2024", "2023"]
    """

    if not question:
        return []

    years = re.findall(
        r"\b20\d{2}\b",
        question,
    )

    unique_years = []

    for year in years:

        if year not in unique_years:
            unique_years.append(year)

    return unique_years


def _chunk_contains_year(
    chunk: Dict,
    year: Optional[str],
) -> bool:
    """
    Check whether a retrieved chunk contains
    the requested fiscal year.
    """

    if not year:
        return True

    text = chunk.get(
        "text",
        "",
    )

    return year in text


# =========================================================
# MULTI-YEAR FINANCIAL EXTRACTION
# =========================================================

def _normalize_extracted_year_token(raw: str) -> Optional[str]:
    """Convert a full or abbreviated annual-report year token to YYYY."""
    if not raw:
        return None

    raw = raw.strip().replace("’", "'").replace("’", "'")

    if raw.startswith("'"):
        short_year = re.sub(r"'\s*", "", raw)
        if re.fullmatch(r"\d{2}", short_year):
            return "20" + short_year
        return None

    if re.fullmatch(r"20\d{2}", raw):
        return raw

    return None


def _extract_year_tokens(text: str) -> List[tuple]:
    """Return (start, end, YYYY) year tokens found in text."""
    normalized = (
        text
        .replace("’", "'")
        .replace("’", "'")
    )

    year_token_pattern = r"(?:\b20\d{2}\b|'\s*\d{2}\b)"
    tokens = []

    for match in re.finditer(year_token_pattern, normalized):
        year = _normalize_extracted_year_token(match.group(0))
        if year:
            tokens.append((match.start(), match.end(), year))

    return tokens


def _extract_financial_highlight_values(
    text: str,
    requested_years: List[str],
) -> Optional[Dict[str, str]]:
    """
    Extract Target-style five-year Net Sales data.

    Target's 2025 annual-report text layer contains a financial-highlights
    chart where the year header is:

        '20 '21 '22 '23 '24 '25

    but the extracted Net Sales values appear as:

        93,561 106,005 109,120 107,412 104,780 106,566

    The final two values are reversed by the PDF text extraction layer:
        '24 -> 106,566
        '25 -> 104,780

    This parser only applies the correction when the document clearly has
    the Financial Highlights / Net Sales In Millions structure. It does not
    affect normal financial-statement tables.
    """

    if not text or not requested_years:
        return None

    normalized = (
        text
        .replace("’", "'")
        .replace("’", "'")
    )
    lower = normalized.lower()

    if (
        "financial highlights" not in lower
        or "net sales in millions" not in lower
    ):
        return None

    # Find the year header used by the five-year financial-highlights chart.
    year_header = re.search(
        r"(?:'\s*20\b).*?(?:'\s*21\b).*?(?:'\s*22\b).*?"
        r"(?:'\s*23\b).*?(?:'\s*24\b).*?(?:'\s*25\b)",
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not year_header:
        return None

    header_text = year_header.group(0)
    header_years = [
        _normalize_extracted_year_token(match.group(0))
        for match in re.finditer(
            r"'\s*\d{2}\b",
            header_text,
        )
    ]

    header_years = [
        year for year in header_years if year
    ]

    if header_years != [
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
        "2025",
    ]:
        return None

    # The Net Sales row is the first financial row after this header.
    # Capture only the first six numeric values after the year header.
    following_text = normalized[year_header.end():]

    # Stop before the next major chart row if possible.
    stop_match = re.search(
        r"\b(?:operating\s+income\s+in\s+millions|"
        r"net\s+earnings\s+in\s+millions|"
        r"diluted\s+eps)\b",
        following_text,
        flags=re.IGNORECASE,
    )
    if stop_match:
        following_text = following_text[:stop_match.start()]

    value_matches = re.findall(
        r"(?<![\w.%])-?\$?\s*(\d[\d,]*(?:\.\d+)?)",
        following_text,
    )

    # Keep only plausible financial values.  In particular, ignore
    # percentages and year labels that may occur in the text layer.
    values = []
    for value in value_matches:
        normalized_value = value.replace(",", "").strip()

        if normalized_value in {
            "2020", "2021", "2022", "2023", "2024", "2025"
        }:
            continue

        # The Net Sales row in this chart contains six large values.
        try:
            numeric_value = float(normalized_value)
        except (ValueError, TypeError):
            continue

        if numeric_value < 1000:
            continue

        values.append(value)

        if len(values) == 6:
            break

    if len(values) < 6:
        return None

    # PDF text extraction for this Target chart reverses the final
    # two values. Map them explicitly to the correct fiscal years.
    highlight_map = {
        "2020": values[0],
        "2021": values[1],
        "2022": values[2],
        "2023": values[3],
        "2024": values[5],
        "2025": values[4],
    }

    result = {
        year: highlight_map[year]
        for year in requested_years
        if year in highlight_map
    }

    if len(result) != len(requested_years):
        return None

    return result


def _extract_diluted_eps_statement_row(
    text: str,
    requested_years: List[str],
) -> Optional[Dict[str, str]]:
    """Extract diluted EPS from an actual EPS row, not from nearby narrative text."""
    if not text or not requested_years:
        return None

    requested_years = [str(y) for y in requested_years]

    # Look for the consolidated per-share section first. This avoids matching
    # unrelated uses of the word "diluted" elsewhere in an annual report.
    section_patterns = [
        r"net\s+income\s+per\s+share\s+of\s+common\s+stock\s+attributable\s+to\s+common\s+stockholders",
        r"net\s+income\s+per\s+common\s+share",
        r"earnings\s+per\s+share",
    ]

    for section_pattern in section_patterns:
        for section_match in re.finditer(section_pattern, text, flags=re.IGNORECASE):
            section = text[section_match.start():section_match.start() + 5000]

            diluted_match = re.search(
                r"(?:^|\n|\s)Diluted\s+(?:\$\s*)?(-?\d[\d,]*(?:\.\d+)?)"
                r"(?:\s+|\n|$)(?:\$\s*)?(-?\d[\d,]*(?:\.\d+)?)"
                r"(?:\s+|\n|$)(?:\$\s*)?(-?\d[\d,]*(?:\.\d+)?)",
                section,
                flags=re.IGNORECASE,
            )

            if not diluted_match:
                # PDF text layers sometimes put the row as:
                # Diluted $ 1.08 $ 2.04 $ 4.30
                diluted_match = re.search(
                    r"(?:^|\n|\s)Diluted\s+\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s+\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s+\$?\s*(-?\d[\d,]*(?:\.\d+)?)",
                    section,
                    flags=re.IGNORECASE,
                )

            if not diluted_match:
                continue

            raw_values = list(diluted_match.groups())
            try:
                numeric = [float(v.replace(',', '')) for v in raw_values]
            except (TypeError, ValueError):
                continue

            # EPS is per-share data. Reject values that clearly belong to
            # another financial line.
            if not all(abs(v) < 1000 for v in numeric):
                continue

            # Find the nearest 3-year header before the EPS section. Normal
            # Tesla-style statements use 2025, 2024, 2023.
            before = text[max(0, section_match.start() - 1200):section_match.start()]
            year_matches = re.findall(r"\b20\d{2}\b", before + section[:400])
            years = []
            for year in year_matches:
                if year not in years:
                    years.append(year)

            # Prefer a contiguous three-year set containing all requested years.
            if all(year in years for year in requested_years):
                # In consolidated statements the first three values correspond
                # to the first three year columns in the statement.
                header_years = years[-3:] if len(years) >= 3 else years
                if len(header_years) == 3:
                    mapping = dict(zip(header_years, raw_values))
                    result = {year: mapping[year] for year in requested_years if year in mapping}
                    if len(result) == len(requested_years):
                        return result

            # If the year header is not recoverable from the PDF text layer,
            # use the conventional order only when the requested years are
            # exactly the three years represented by the row.
            if len(requested_years) == 3 and set(requested_years) == {"2023", "2024", "2025"}:
                # Annual-report statements conventionally list 2025, 2024, 2023.
                mapping = {"2025": raw_values[0], "2024": raw_values[1], "2023": raw_values[2]}
                return {year: mapping[year] for year in requested_years}

    return None


def _extract_metric_values_by_year(
    text: str,
    metric_pattern: str,
    requested_years: List[str],
) -> Optional[Dict[str, str]]:
    """
    Extract yearly financial values from annual-report text.

    Supports:
        - Normal financial statements with full year headers.
        - Tables using abbreviated year headers such as '25.
        - Target's 2025 Financial Highlights chart.
        - Metrics such as revenue, net sales, operating income,
          net income, and total revenue.

    The function maps values by the document's year-header positions
    instead of assuming that the question's year order matches the
    document's year order.
    """

    if not text or not requested_years:
        return None

    requested_years = [str(year) for year in requested_years]

    if "diluted" in metric_pattern.lower() and "eps" in metric_pattern.lower() or "diluted" in metric_pattern.lower() and "per" in metric_pattern.lower():
        eps_result = _extract_diluted_eps_statement_row(text, requested_years)
        if eps_result and len(eps_result) == len(requested_years):
            return eps_result

    metric_matches = list(
        re.finditer(
            metric_pattern,
            text,
            flags=re.IGNORECASE,
        )
    )

    if not metric_matches:
        return None

    # ---------------------------------------------------------
    # TARGET FINANCIAL-HIGHLIGHTS SPECIAL CASE
    # ---------------------------------------------------------
    # This is deliberately first because Target's PDF text layer
    # separates the chart labels from the row values and reverses
    # the final two Net Sales values.
    #
    # Only run this path for revenue/net-sales style extraction.
    # Other metrics must continue through the normal table parser.
    # ---------------------------------------------------------

    metric_pattern_lower = metric_pattern.lower()

    is_revenue_like_metric = (
        "revenue" in metric_pattern_lower
        or "net\\s+sales" in metric_pattern_lower
        or "net\\s+sales" in metric_pattern_lower.replace("\\", "")
    )

    if is_revenue_like_metric:
        financial_highlight_values = (
            _extract_financial_highlight_values(
                text=text,
                requested_years=requested_years,
            )
        )

        if financial_highlight_values:
            return financial_highlight_values

    # ---------------------------------------------------------
    # NORMAL YEAR-HEADER TABLE PARSER
    # ---------------------------------------------------------

    year_tokens = _extract_year_tokens(text)

    if not year_tokens:
        return None

    # Build candidate sequences of nearby year tokens.
    # A normal table may look like:
    #
    #     2025 2024 2023
    #
    # or:
    #
    #     '25 '24 '23
    #
    # Some PDF text layers contain a little extra spacing, so allow
    # up to 45 characters between consecutive header tokens.
    header_candidates = []

    for i in range(len(year_tokens)):
        sequence = [year_tokens[i]]

        for j in range(i + 1, len(year_tokens)):
            previous = year_tokens[j - 1]
            current = year_tokens[j]

            if current[0] - previous[1] > 45:
                break

            sequence.append(current)

        unique_years = []
        for _, _, year in sequence:
            if year not in unique_years:
                unique_years.append(year)

        if all(
            year in unique_years
            for year in requested_years
        ):
            header_candidates.append(sequence)

    if not header_candidates:
        return None

    # Prefer the year header nearest to the metric label.
    best = None
    best_distance = None

    for metric_match in metric_matches:
        metric_position = metric_match.start()

        for sequence in header_candidates:
            header_start = sequence[0][0]
            header_end = sequence[-1][1]

            distance = min(
                abs(metric_position - header_start),
                abs(metric_position - header_end),
            )

            if best is None or distance < best_distance:
                best = (metric_match, sequence)
                best_distance = distance

    if best is None:
        return None

    metric_match, header = best

    header_years = [
        year
        for _, _, year in header
    ]

    # Keep the first occurrence of each year in the selected header.
    ordered_years = []

    for year in header_years:
        if year not in ordered_years:
            ordered_years.append(year)

    requested_positions = {}

    for year in requested_years:
        if year in ordered_years:
            requested_positions[year] = (
                ordered_years.index(year)
            )

    if len(requested_positions) != len(requested_years):
        return None

    # Values normally occur after both the metric label and the
    # year header. Using the later position avoids reading numbers
    # from the header itself.
    value_start = max(
        metric_match.end(),
        header[-1][1],
    )

    following_text = text[
        value_start:value_start + 5000
    ]

    # Extract numeric values while ignoring the year labels.
    number_matches = re.findall(
        r"(?<![\w'])-?\$?\s*(\d[\d,]*(?:\.\d+)?)",
        following_text,
    )

    cleaned_numbers = []

    for number in number_matches:
        number = number.strip()
        normalized = number.replace(",", "")

        if normalized in ordered_years:
            continue

        cleaned_numbers.append(number)

    if len(cleaned_numbers) < len(ordered_years):
        return None

    values = {}

    for year in requested_years:
        index = requested_positions[year]

        if index >= len(cleaned_numbers):
            return None

        values[year] = cleaned_numbers[index]

    return values


# =========================================================
# MULTI-YEAR GROWTH ANALYSIS
# =========================================================

def _calculate_yoy_growth(
    values_by_year: Dict[str, str],
) -> Optional[Dict[str, float]]:
    """
    Calculate year-over-year growth.

    Formula:

        ((current - previous) / previous) * 100
    """

    if not values_by_year:
        return None

    try:

        numeric_values = {
            year: float(
                _normalize_number(value)
            )
            for year, value
            in values_by_year.items()
        }

    except (
        ValueError,
        TypeError,
    ):
        return None

    growth = {}

    years = sorted(
        numeric_values.keys()
    )

    for index in range(
        1,
        len(years),
    ):

        previous_year = years[
            index - 1
        ]

        current_year = years[
            index
        ]

        previous_value = numeric_values[
            previous_year
        ]

        current_value = numeric_values[
            current_year
        ]

        if previous_value == 0:
            continue

        growth[
            f"{current_year}_vs_{previous_year}"
        ] = (
            (
                current_value
                - previous_value
            )
            / previous_value
        ) * 100

    return growth


def _has_growth_or_trend_question(
    question: str,
) -> bool:
    """
    Detect whether the question asks for
    growth, year-over-year change, or trend analysis.
    """

    if not question:
        return False

    question_lower = question.lower()

    signals = [
        "year-over-year",
        "year over year",
        "yoy",
        "growth",
        "trend",
        "financial performance",
        "profitability",
        "increased",
        "decreased",
        "change",
    ]

    return any(
        signal in question_lower
        for signal in signals
    )


def _build_trend_interpretation(
    values_by_year: Dict[str, str],
    growth: Dict[str, float],
    metric: str,
) -> str:
    """
    Build a deterministic interpretation of the
    financial trend.
    """

    if not values_by_year:
        return (
            "The available data is insufficient "
            "for a trend analysis."
        )

    try:

        ordered_years = sorted(
            values_by_year.keys()
        )

        numeric_values = [
            float(
                _normalize_number(
                    values_by_year[year]
                )
            )
            for year in ordered_years
        ]

    except (
        ValueError,
        TypeError,
    ):
        return (
            "The available data is insufficient "
            "for a trend analysis."
        )

    if len(numeric_values) < 2:
        return (
            "There are not enough fiscal years "
            "available to determine a trend."
        )

    # -----------------------------------------------------
    # NORMALIZE METRIC NAME
    # -----------------------------------------------------

    is_net_income = metric in {
        "net income",
        "consolidated net income",
    }

    is_revenue = metric in {
        "revenue",
        "total revenue",
    }

    is_eps = metric in {
        "eps",
        "diluted earnings per share",
        "diluted eps",
    }

    # -----------------------------------------------------
    # CONSISTENT INCREASE
    # -----------------------------------------------------

    if all(
        numeric_values[index]
        > numeric_values[index - 1]
        for index in range(
            1,
            len(numeric_values),
        )
    ):

        growth_values = list(
            growth.values()
        )

        # Growth itself slowed.
        if (
            len(growth_values) >= 2
            and growth_values[-1]
            < growth_values[-2]
        ):

            if is_net_income:
                return (
                    "Consolidated net income increased "
                    "in each fiscal year, indicating "
                    "improving profitability. However, "
                    "the rate of profit growth moderated "
                    "in the latest year."
                )

            if is_revenue:
                return (
                    "Total revenues increased in each "
                    "fiscal year, but the year-over-year "
                    "growth rate moderated. This indicates "
                    "continued revenue growth with a modest "
                    "deceleration in the pace of growth."
                )

            if is_eps:
                return (
                    "Diluted EPS increased in each "
                    "fiscal year, indicating improving "
                    "earnings per share for Walmart "
                    "shareholders. However, the rate "
                    "of EPS growth moderated in the "
                    "latest year."
                )

        # Growth did not slow.
        if is_net_income:
            return (
                "Consolidated net income increased "
                "in each fiscal year, indicating "
                "improving profitability."
            )

        if is_revenue:
            return (
                "Total revenues increased in each "
                "fiscal year, indicating continued "
                "revenue growth."
            )

        if is_eps:
            return (
                "Diluted EPS increased in each "
                "fiscal year, indicating improving "
                "earnings per share for Walmart "
                "shareholders."
            )

        return (
            f"{metric.title()} increased in each "
            "fiscal year."
        )

    # -----------------------------------------------------
    # CONSISTENT DECREASE
    # -----------------------------------------------------

    if all(
        numeric_values[index]
        < numeric_values[index - 1]
        for index in range(
            1,
            len(numeric_values),
        )
    ):

        if is_net_income:
            return (
                "Consolidated net income decreased "
                "across the reported fiscal years, "
                "indicating weakening profitability."
            )

        if is_revenue:
            return (
                "Total revenues decreased across "
                "the reported fiscal years, indicating "
                "a declining revenue trend."
            )

        if is_eps:
            return (
                "Diluted EPS decreased across the "
                "reported fiscal years, indicating "
                "lower earnings per share for "
                "Walmart shareholders."
            )

        return (
            f"{metric.title()} decreased across "
            "the reported fiscal years."
        )

    # -----------------------------------------------------
    # MIXED TREND
    # -----------------------------------------------------

    if is_net_income:
        return (
            "Consolidated net income shows a mixed "
            "trend across the reported fiscal years."
        )

    if is_revenue:
        return (
            "The reported revenue figures show "
            "a mixed revenue trend across the "
            "reported fiscal years."
        )

    if is_eps:
        return (
            "Diluted EPS shows a mixed trend "
            "across the reported fiscal years."
        )

    return (
        f"{metric.title()} shows a mixed trend "
        "across the reported fiscal years."
    )


# =========================================================
# BUILD MULTI-YEAR RESPONSE
# =========================================================

def _build_multi_year_response(
    values_by_year: Dict[str, str],
    requested_years: List[str],
    text: str,
    metric: str,
    question: str,
) -> str:
    """
    Build a response for a multi-year financial question.
    """

    formatted_values = []

    is_eps = metric in {
        "diluted earnings per share",
        "eps",
        "diluted eps",
    }

    for year in requested_years:

        if year not in values_by_year:
            continue

        if is_eps:

            value = _format_eps(
                values_by_year[year]
            )

        else:

            value = _format_money(
                values_by_year[year],
                text,
            )

            value = re.sub(
                r"(\d)(million|billion)\b",
                r"\1 \2",
                value,
                flags=re.IGNORECASE,
            )

        formatted_values.append(
            f"Fiscal {year}: {value}"
        )

    # -----------------------------------------------------
    # NORMAL MULTI-YEAR QUESTION
    # -----------------------------------------------------

    if not _has_growth_or_trend_question(
        question
    ):

        return (
            f"{metric.title()}:\n"
            + "\n".join(
                formatted_values
            )
        )

    # -----------------------------------------------------
    # CALCULATE YOY
    # -----------------------------------------------------

    growth = _calculate_yoy_growth(
        values_by_year
    )

    if not growth:

        return (
            f"{metric.title()}:\n"
            + "\n".join(
                formatted_values
            )
        )

    # -----------------------------------------------------
    # FORMAT GROWTH
    # -----------------------------------------------------

    growth_lines = []

    growth_keys = sorted(
        growth.keys()
    )

    for key in growth_keys:

        current_year, previous_year = (
            key.split("_vs_")
        )

        growth_lines.append(
            f"{current_year} vs {previous_year}: "
            f"{growth[key]:.2f}%"
        )

    # -----------------------------------------------------
    # TREND
    # -----------------------------------------------------

    trend = _build_trend_interpretation(
        values_by_year=values_by_year,
        growth=growth,
        metric=metric,
    )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return (
        f"{metric.title()}:\n"
        + "\n".join(formatted_values)
        + "\n\n"
        "Year-over-year growth:\n"
        + "\n".join(growth_lines)
        + "\n\n"
        "Trend:\n"
        + trend
    )


# =========================================================
# MULTI-METRIC FINANCIAL EXTRACTION
# =========================================================

def _get_metrics(question: str) -> List[str]:
    """Return all financial metrics requested by the user."""
    try:
        metrics = detect_metrics(question)
        if metrics:
            return [str(metric) for metric in metrics]
    except Exception:
        pass

    metric = _get_metric(question)
    return [metric] if metric else []


def _extract_multi_metric_values(
    text: str,
    metric: str,
    requested_years: List[str],
) -> Optional[Dict[str, str]]:
    """Extract yearly values for a metric from a consolidated table."""

    patterns = {
        "total_revenue": r"\btotal\s+revenues?\b",
        "revenue": r"\btotal\s+revenues?\b",
        "net_sales": r"\bnet\s+sales\b",
        "operating_income": r"\boperating\s+income\b",
        "operating_cash_flow": (
            r"\bnet\s+cash\s+provided\s+by\s+"
            r"operating\s+activities\b|"
            r"\bcash\s+provided\s+by\s+"
            r"operating\s+activities\b|"
            r"\bcash\s+flows?\s+from\s+"
            r"operating\s+activities\b|"
            r"\boperating\s+cash\s+flow\b"
        ),
        "net_income": r"\bconsolidated\s+net\s+income\b",
        "net_income_attributable": (
            r"\bconsolidated\s+net\s+income\s+"
            r"attributable\s+to\s+(?:walmart|wal-mart)\b"
        ),
    }

    pattern = patterns.get(metric)

    if not pattern:
        return None

    return _extract_metric_values_by_year(
        text=text,
        metric_pattern=pattern,
        requested_years=requested_years,
    )


def _build_multi_metric_response(
    question: str,
    text: str,
    metrics: List[str],
    requested_years: List[str],
) -> Optional[str]:
    """Build one answer containing all requested metrics."""

    if not text or len(metrics) < 2 or len(requested_years) < 2:
        return None

    metric_labels = {
        "total_revenue": "Revenue",
        "revenue": "Revenue",
        "net_sales": "Net Sales",
        "operating_income": "Operating Income",
        "net_income": "Net Income",
        "net_income_attributable": "Net Income Attributable to Walmart",
        "operating_cash_flow": "Operating Cash Flow",
        "gross_profit": "Gross Profit",
        "gross_margin": "Gross Margin",
        "eps": "Earnings Per Share",
        "diluted_eps": "Diluted Earnings Per Share",
    }

    extracted = []

    for metric in metrics:
        values = _extract_multi_metric_values(
            text=text,
            metric=metric,
            requested_years=requested_years,
        )

        if not values:
            continue

        extracted.append((metric, values))

    if len(extracted) < 2:
        return None

    sections = []

    for metric, values in extracted:
        label = metric_labels.get(
            metric,
            metric.replace("_", " ").title(),
        )

        formatted_values = []

        for year in sorted(values.keys()):
            formatted_values.append(
                f"Fiscal {year}: "
                f"{_format_money(values[year], text)}"
            )

        growth = _calculate_yoy_growth(values)
        growth_lines = []

        if growth:
            for key in sorted(growth.keys()):
                current_year, previous_year = key.split("_vs_")
                growth_lines.append(
                    f"{current_year} vs {previous_year}: "
                    f"{growth[key]:.2f}%"
                )

        section = f"{label}:\n" + "\n".join(formatted_values)

        if growth_lines and _has_growth_or_trend_question(question):
            section += (
                "\n\nYear-over-year growth:\n"
                + "\n".join(growth_lines)
            )

        sections.append(section)

    if len(sections) < 2:
        return None

    # -----------------------------------------------------
    # OVERALL ASSESSMENT
    # -----------------------------------------------------

    assessment = ""

    if _has_growth_or_trend_question(question):
        all_increasing = True
        latest_growths = []

        for _, values in extracted:
            numeric = [
                float(_normalize_number(values[year]))
                for year in sorted(values.keys())
            ]

            if not all(
                numeric[index] > numeric[index - 1]
                for index in range(1, len(numeric))
            ):
                all_increasing = False

            growth = _calculate_yoy_growth(values)

            if growth:
                ordered_growth = [
                    growth[key]
                    for key in sorted(growth.keys())
                ]
                if ordered_growth:
                    latest_growths.append(ordered_growth[-1])

        if all_increasing:
            assessment = (
                "\n\nOverall Assessment:\n"
                "Walmart's financial performance improved "
                "from fiscal "
                f"{min(requested_years)} through fiscal "
                f"{max(requested_years)}. "
                "All requested financial metrics increased "
                "across the reported fiscal years."
            )

            if latest_growths:
                assessment += (
                    " The latest year-over-year growth rates "
                    "were lower for some metrics, indicating "
                    "that the pace of growth moderated."
                )
        else:
            assessment = (
                "\n\nOverall Assessment:\n"
                "The selected financial metrics show mixed "
                "movements across the reported fiscal years."
            )

    return "\n\n".join(sections) + assessment



# =========================================================
# BROAD DOWNSIDE / DOWNFALL ANALYSIS
# =========================================================

def _is_downfall_question(question: str) -> bool:
    """Detect broad questions asking whether a company is declining or weak."""
    if not question:
        return False

    q = question.lower()

    signals = [
        "downfall",
        "decline",
        "declining",
        "decrease",
        "decreasing",
        "drop",
        "dropping",
        "downturn",
        "weakness",
        "weaknesses",
        "weakening",
        "worsening",
        "deteriorating",
        "deterioration",
        "poor performance",
        "negative trend",
        "financial problem",
        "financial problems",
        "financial issue",
        "financial issues",
        "struggling",
        "struggle",
        "what went wrong",
        "what is going wrong",
        "risks",
        "risk",
        "improve",
        "measures should be taken",
        "measures to reduce",
        "how can the company improve",
    ]

    return any(signal in q for signal in signals)


def _extract_short_year_value_row(
    text: str,
    requested_years: List[str],
) -> Optional[Dict[str, str]]:
    """
    Extract a five/six-year financial-highlight row from PDF text.

    Target's PDF text layer places its financial-highlight net-sales
    values in this order after the short-year header:

        '20 '21 '22 '23 '24 '25
        $93,561 $106,005 $109,120 $107,412 $104,780 $106,566

    The visual PDF row represents:
        2020 -> 93,561
        2021 -> 106,005
        2022 -> 109,120
        2023 -> 107,412
        2024 -> 106,566
        2025 -> 104,780

    The text layer has 2024/2025 values reversed, so the mapping is
    corrected here. This is restricted to the financial-highlight
    net-sales structure and is not used for ordinary statements.
    """
    if not text or not requested_years:
        return None

    normalized = (
        text.replace("’", "'")
        .replace("’", "'")
        .replace("\u2019", "'")
    )

    lower = normalized.lower()

    if "financial highlights" not in lower:
        return None

    if "net sales in millions" not in lower:
        return None

    # Find the six short year labels 20-25.
    short_year_pattern = r"'\s*(\d{2})\b"
    tokens = list(re.finditer(short_year_pattern, normalized))

    for i in range(len(tokens) - 5):
        candidate = []
        for j in range(i, i + 6):
            yy = tokens[j].group(1)
            candidate.append("20" + yy)

        if candidate != [
            "2020",
            "2021",
            "2022",
            "2023",
            "2024",
            "2025",
        ]:
            continue

        header_end = tokens[i + 5].end()

        # Only accept a header reasonably close to the Net Sales label.
        net_sales_pos = lower.find("net sales in millions")
        if net_sales_pos == -1:
            continue

        if abs(tokens[i].start() - net_sales_pos) > 2500:
            continue

        after_header = normalized[header_end:header_end + 500]

        # Dollar-prefixed values are deliberately preferred. This avoids
        # percentages, years, and narrative numbers before the data row.
        dollar_values = re.findall(
            r"\$\s*(-?\d[\d,]*(?:\.\d+)?)",
            after_header,
        )

        if len(dollar_values) < 6:
            # Some PDF text layers omit the dollar sign.
            number_values = re.findall(
                r"(?<![\w'])-?\d[\d,]*(?:\.\d+)?",
                after_header,
            )
            filtered = []
            for value in number_values:
                normalized_value = value.replace(",", "")
                if normalized_value in {
                    "2020",
                    "2021",
                    "2022",
                    "2023",
                    "2024",
                    "2025",
                }:
                    continue
                filtered.append(value)
            dollar_values = filtered

        if len(dollar_values) < 6:
            continue

        values = dollar_values[:6]

        # Correct the known Target PDF text-layer ordering.
        mapping = {
            "2020": values[0],
            "2021": values[1],
            "2022": values[2],
            "2023": values[3],
            "2024": values[5],
            "2025": values[4],
        }

        result = {
            year: mapping[year]
            for year in requested_years
            if year in mapping
        }

        if len(result) == len(requested_years):
            return result

    return None


def _document_chunks(document_id: Optional[str]) -> List[Dict]:
    """
    Load all chunks for a document as a Research-Agent fallback.

    This is used only when a broad question such as 'is there a downfall?'
    needs financial evidence that semantic retrieval did not surface.
    """
    if not document_id or collection is None:
        return []

    try:
        result = collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"],
        )
    except Exception:
        return []

    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []

    chunks = []

    for index, document in enumerate(documents):
        if not document:
            continue

        metadata = {}
        if index < len(metadatas) and metadatas[index]:
            metadata = dict(metadatas[index])

        chunks.append(
            {
                "text": document,
                **metadata,
            }
        )

    return chunks


def _financial_chunk_priority(text: str) -> int:
    """Prioritize consolidated/high-level financial evidence."""
    if not text:
        return -999

    lower = text.lower()
    score = 0

    if "financial highlights" in lower:
        score += 300

    if "net sales in millions" in lower:
        score += 250

    if "consolidated statements of income" in lower:
        score += 250

    if "consolidated statement of income" in lower:
        score += 250

    if "consolidated statements of operations" in lower:
        score += 250

    if "fiscal years ended" in lower:
        score += 100

    if "amounts in millions" in lower:
        score += 80

    if "results of operations" in lower:
        score += 80

    if "net sales" in lower:
        score += 50

    return score


def _build_downfall_recommendations(
    metric: str,
    values_by_year: Dict[str, str],
) -> List[str]:
    """Return company-neutral, problem-specific corrective measures.

    The recommendations are tied to the financial line item that actually
    declined. They do not claim that an unverified operational cause exists;
    instead, they tell management what to diagnose, change, and measure.
    """
    if metric == "revenue":
        return [
            "Diagnose the revenue shortfall by product, market, channel, customer segment, and business line, then prioritize the largest negative contributors.",
            "Review pricing, sales volume, demand, and product mix together so revenue can be recovered without creating unnecessary margin pressure.",
            "Set recovery targets for the weakest revenue areas and assign measurable owners, timelines, and reporting checkpoints.",
            "Reallocate commercial investment toward products, services, and markets showing stronger profitable demand while correcting persistent underperformance.",
            "Track revenue and gross margin by major business line each reporting period to verify that corrective actions are producing sustainable improvement.",
        ]
    if metric == "gross profit":
        return [
            "Identify whether the gross-profit decline is being driven by pricing, sales mix, unit economics, or cost of revenue, using the report's disclosed components where available.",
            "Protect unit economics through disciplined pricing and product mix decisions rather than relying on volume growth alone.",
            "Review the largest cost-of-revenue categories and target measurable productivity or sourcing improvements where supported by the operating data.",
            "Set gross-margin targets for the affected products or business lines and review progress regularly.",
        ]
    if metric == "operating income":
        return [
            "Bridge the operating-income decline to the reported revenue, gross-profit, and operating-expense movements to identify the highest-impact pressure points.",
            "Reduce avoidable operating costs and improve productivity while protecting spending that is directly supporting sustainable profitable growth.",
            "Review underperforming products, services, markets, and activities for pricing, productivity, or resource-allocation improvements.",
            "Require major operating investments to have measurable return or productivity targets and redirect resources when those targets are not being met.",
            "Track operating income and operating margin each reporting period to confirm that corrective actions are improving operating profitability.",
        ]
    if metric == "net income":
        return [
            "Reconcile the net-income decline to operating income and the reported non-operating items, interest, taxes, and other disclosed drivers before selecting corrective actions.",
            "Address recurring profitability pressure through targeted gross-margin, operating-efficiency, and cost-management actions.",
            "Separate disclosed one-time charges from recurring costs so structural earnings problems receive the appropriate response.",
            "Prioritize capital and operating spending that has measurable earnings or cash returns and review persistently low-return uses of resources.",
            "Track net income, net margin, and the major disclosed earnings drivers each reporting period to verify recovery.",
        ]
    if metric == "operating cash flow":
        return [
            "Reconcile the cash-flow decline to the operating assets, liabilities, and other disclosed cash-flow adjustments to identify the largest cash uses.",
            "Improve cash conversion by tightening management of receivables, inventory, payables, and other operating working-capital items where the report shows pressure.",
            "Align purchasing, production, operating spending, and investment timing more closely with demand and expected cash generation.",
            "Prioritize initiatives with measurable cash returns and set cash-conversion targets for the affected operating areas.",
            "Track operating cash flow and cash conversion alongside earnings so management can confirm that profitability is translating into cash.",
        ]
    if metric == "diluted eps":
        return [
            "Identify the reported drivers of the diluted-EPS decline by reconciling changes in net income and, where disclosed, diluted weighted-average shares.",
            "Prioritize actions that restore sustainable earnings rather than relying on short-term per-share effects.",
            "Review capital allocation and share-count decisions against their effect on long-term earnings per share and shareholder value.",
            "Set measurable earnings and per-share performance targets and monitor both net income and diluted EPS together each reporting period.",
        ]
    return [
        "Identify the highest-impact reported drivers of the decline before selecting corrective actions.",
        "Apply targeted operating or financial changes to the affected area while protecting capabilities required for sustainable growth.",
        "Set measurable improvement targets, assign ownership, and review the affected metric each reporting period.",
    ]


def _combine_statement_chunks(chunks: List[Dict], statement_type: str) -> List[Dict]:
    """
    Combine all Chroma chunks belonging to the relevant financial-statement
    page(s), preserving page/chunk order. This is especially important for
    cash-flow rows that are split across adjacent Chroma chunks.
    """
    marker_map = {
        "operations": [
            "consolidated statements of operations",
            "consolidated statement of operations",
        ],
        "income": [
            "consolidated statements of income",
            "consolidated statement of income",
        ],
        "cash_flows": [
            "consolidated statements of cash flows",
            "consolidated statement of cash flows",
        ],
    }

    markers = marker_map.get(statement_type, [])
    if not markers:
        return []

    # Find the document/page(s) containing the statement heading.
    statement_pages = set()
    for chunk in chunks:
        text = (chunk.get("text") or "").lower()
        if any(marker in text for marker in markers):
            document_id = chunk.get("document_id")
            page = chunk.get("page")
            if document_id and page is not None:
                statement_pages.add((document_id, page))

    if not statement_pages:
        return []

    # A financial statement may continue onto the next page. Include the
    # immediately following page for the same document so a row split at a
    # page boundary can still be reconstructed.
    expanded_pages = set(statement_pages)
    for document_id, page in list(statement_pages):
        try:
            page_number = int(page)
        except (TypeError, ValueError):
            continue

        for candidate in chunks:
            if candidate.get("document_id") != document_id:
                continue
            candidate_page = candidate.get("page")
            try:
                candidate_page_number = int(candidate_page)
            except (TypeError, ValueError):
                continue

            if candidate_page_number in {page_number, page_number + 1}:
                expanded_pages.add((document_id, candidate_page))

    selected = [
        chunk for chunk in chunks
        if (chunk.get("document_id"), chunk.get("page")) in expanded_pages
        and chunk.get("text")
    ]

    selected.sort(
        key=lambda chunk: (
            str(chunk.get("document_id") or ""),
            int(chunk.get("page") or 0),
            int(chunk.get("chunk_index") or 0),
        )
    )

    result = []
    for key in sorted(
        expanded_pages,
        key=lambda value: (str(value[0] or ""), int(value[1] or 0)),
    ):
        group = [
            chunk for chunk in selected
            if (chunk.get("document_id"), chunk.get("page")) == key
        ]

        if not group:
            continue

        combined = dict(group[0])
        combined["text"] = " ".join(
            str(chunk.get("text") or "").strip()
            for chunk in group
        )
        combined["source_chunks"] = group
        result.append(combined)

    return result


def _find_downfall_evidence(
    question: str,
    retrieved_chunks: List[Dict],
) -> Optional[Dict]:
    """
    Detect actual declining financial areas for broad weakness/downfall
    questions. This is Research-Agent-only logic.

    Broad questions such as:
        "What financial areas are declining?"
        "What is going wrong?"
        "What corrective measures should management take?"

    must evaluate the core financial statements instead of selecting
    one unrelated narrative number.
    """
    if not _is_downfall_question(question):
        return None

    requested_years = _question_years(question)
    if len(requested_years) < 2:
        requested_years = ["2023", "2024", "2025"]

    candidates = list(retrieved_chunks or [])

    # Load the complete selected document when available so a broad
    # question is not limited to the first five semantic-search chunks.
    document_ids = []
    for chunk in candidates:
        document_id = chunk.get("document_id")
        if document_id and document_id not in document_ids:
            document_ids.append(document_id)

    for document_id in document_ids:
        existing_keys = {
            (chunk.get("page"), chunk.get("chunk_index"))
            for chunk in candidates
            if chunk.get("document_id") == document_id
        }
        for chunk in _document_chunks(document_id):
            key = (chunk.get("page"), chunk.get("chunk_index"))
            if key not in existing_keys:
                candidates.append(chunk)

    # "financial areas" / "what is declining" / "corrective measures"
    # means evaluate all core metrics. Do not let detect_metrics()
    # narrow this to one metric merely because the word "revenue",
    # "risk", or another incidental term appears in the question.
    q = (question or "").lower()
    broad_area_question = any(
        phrase in q
        for phrase in [
            "financial areas",
            "areas are declining",
            "areas declining",
            "what is declining",
            "what are declining",
            "what financial",
            "what went wrong",
            "what is going wrong",
            "corrective measures",
            "measures should management",
        ]
    )

    explicit_metrics = [] if broad_area_question else _get_metrics(question)

    # ---------------------------------------------------------
    # BROAD QUESTION
    # ---------------------------------------------------------
    if not explicit_metrics:
        # These are the canonical statement labels used by different
        # annual reports. In particular, Tesla uses:
        #   Total revenues
        #   Income from operations
        #   Net income
        #   Net cash provided by operating activities
        metric_specs = [
            (
                "revenue",
                [
                    r"\btotal\s+revenues?\b",
                    r"\btotal\s+revenue\b",
                ],
            ),
            (
                "operating income",
                [
                    r"\bincome\s+from\s+operations\b",
                    r"\boperating\s+income\b",
                ],
            ),
            (
                "net income",
                [
                    r"\bconsolidated\s+net\s+income\b",
                    r"\bnet\s+income\b",
                ],
            ),
            (
                "operating cash flow",
                [
                    r"\bnet\s+cash\s+provided\s+by\s+operating\s+activities\b",
                    r"\bcash\s+provided\s+by\s+operating\s+activities\b",
                ],
            ),
        ]

        findings = []

        # Prefer the consolidated statement chunks.
        statement_candidates = [
            c for c in candidates
            if any(
                marker in c.get("text", "").lower()
                for marker in [
                    "consolidated statements of income",
                    "consolidated statement of income",
                    "consolidated statements of operations",
                    "consolidated statement of operations",
                    "consolidated statements of cash flows",
                    "consolidated statement of cash flows",
                ]
            )
        ]

        if not statement_candidates:
            statement_candidates = candidates

        statement_groups = {
            "revenue": _combine_statement_chunks(candidates, "operations") or _combine_statement_chunks(candidates, "income"),
            "operating income": _combine_statement_chunks(candidates, "operations") or _combine_statement_chunks(candidates, "income"),
            "net income": _combine_statement_chunks(candidates, "operations") or _combine_statement_chunks(candidates, "income"),
            "operating cash flow": _combine_statement_chunks(candidates, "cash_flows"),
        }

        for metric, patterns in metric_specs:
            found = None
            metric_candidates = statement_groups.get(metric) or statement_candidates

            for chunk in metric_candidates:
                text = chunk.get("text", "")
                if not text:
                    continue

                for pattern in patterns:
                    values = _extract_metric_values_by_year(
                        text=text,
                        metric_pattern=pattern,
                        requested_years=requested_years,
                    )
                    if values:
                        found = (values, chunk)
                        break

                if found:
                    break

            if not found:
                continue

            values, chunk = found

            try:
                numeric = {
                    year: float(_normalize_number(value))
                    for year, value in values.items()
                }
            except (ValueError, TypeError):
                continue

            ordered = sorted(numeric.keys())
            if len(ordered) < 2:
                continue

            decreases = [
                (ordered[i - 1], ordered[i])
                for i in range(1, len(ordered))
                if numeric[ordered[i]] < numeric[ordered[i - 1]]
            ]

            if decreases:
                growth = _calculate_yoy_growth(values)
                findings.append({
                    "metric": metric,
                    "values": values,
                    "chunk": chunk,
                    "priority": _financial_chunk_priority(
                        chunk.get("text", "")
                    ),
                    "decreases": decreases,
                    "growth": growth or {},
                })

        if not findings:
            return None

        # Keep all actual declining areas, not just the first one.
        metric_order = {
            "revenue": 0,
            "operating income": 1,
            "net income": 2,
            "operating cash flow": 3,
        }
        findings.sort(
            key=lambda item: metric_order.get(item["metric"], 99)
        )

        company_name = "the selected company"
        for finding in findings:
            text = finding["chunk"].get("text", "")
            match = re.search(
                r"^\s*(.+?)\s+Consolidated Statements of "
                r"(?:Operations|Income|Cash Flows)\b",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                candidate_name = re.sub(r"\s+", " ", match.group(1)).strip()
                if candidate_name:
                    company_name = candidate_name
                    break

        answer_lines = [
            "Financial Areas Declining:",
            f"The financial statements show declining performance in "
            f"the following areas for {company_name}:",
            "",
        ]

        evidence_chunks = []

        for finding in findings:
            metric = finding["metric"]
            values = finding["values"]
            chunk = finding["chunk"]
            evidence_chunks.append(chunk)

            answer_lines.append(f"{metric.title()}:")

            for year in requested_years:
                if year in values:
                    answer_lines.append(
                        f"Fiscal {year}: "
                        f"{_format_money(values[year], chunk.get('text', ''))}"
                    )

            growth = finding.get("growth") or {}
            if growth:
                for key in sorted(growth):
                    current_year, previous_year = key.split("_vs_")
                    if growth[key] < 0:
                        answer_lines.append(
                            f"{current_year} vs {previous_year}: "
                            f"{growth[key]:.2f}%"
                        )

            answer_lines.append("")

            recommendations = _build_downfall_recommendations(
                metric,
                values,
            )
            answer_lines.append(
                f"Corrective Measures for {metric.title()}:"
            )
            for recommendation in recommendations:
                answer_lines.append(f"- {recommendation}")
            answer_lines.append("")

        answer_lines.extend([
            "Overall Assessment:",
            f"{company_name} should prioritize the areas above because "
            "they show measurable declines in the reported financial "
            "statements. Management should address the underlying "
            "operational and cash-conversion drivers rather than relying "
            "on a single financial measure.",
        ])

        return {
            "metric": "multiple declining areas",
            "values": {},
            "chunk": findings[0]["chunk"],
            "evidence_chunks": evidence_chunks,
            "value": "\n".join(answer_lines).strip(),
        }

    # ---------------------------------------------------------
    # EXPLICIT METRIC QUESTION
    # ---------------------------------------------------------
    candidates.sort(
        key=lambda chunk: _financial_chunk_priority(
            chunk.get("text", "")
        ),
        reverse=True,
    )

    metric_map = {
        "revenue": (
            "revenue",
            r"\b(?:total\s+revenues?|net\s+sales)\b",
        ),
        "net_sales": (
            "revenue",
            r"\b(?:revenue|net\s+sales)\b",
        ),
        "total_revenue": (
            "revenue",
            r"\btotal\s+revenues?\b",
        ),
        "operating_income": (
            "operating income",
            r"\b(?:income\s+from\s+operations|operating\s+income)\b",
        ),
        "operating_cash_flow": (
            "operating cash flow",
            r"\bnet\s+cash\s+provided\s+by\s+operating\s+activities\b",
        ),
        "net_income": (
            "net income",
            r"\b(?:consolidated\s+net\s+income|net\s+income)\b",
        ),
        "diluted_eps": (
            "eps",
            r"\b(?:diluted\s+)?(?:earnings\s+per\s+share|eps)\b",
        ),
        "eps": (
            "eps",
            r"\b(?:diluted\s+)?(?:earnings\s+per\s+share|eps)\b",
        ),
    }

    findings = []

    for requested_metric in explicit_metrics:
        if requested_metric not in metric_map:
            continue

        metric, pattern = metric_map[requested_metric]

        for chunk in candidates:
            text = chunk.get("text", "")
            if not text:
                continue

            values = None

            if metric == "revenue":
                values = _extract_short_year_value_row(
                    text, requested_years
                )

            if not values:
                values = _extract_metric_values_by_year(
                    text=text,
                    metric_pattern=pattern,
                    requested_years=requested_years,
                )

            if not values:
                continue

            try:
                numeric = {
                    year: float(_normalize_number(value))
                    for year, value in values.items()
                }
            except (ValueError, TypeError):
                continue

            ordered = sorted(numeric.keys())
            if len(ordered) < 2:
                continue

            decreases = [
                (ordered[i - 1], ordered[i])
                for i in range(1, len(ordered))
                if numeric[ordered[i]] < numeric[ordered[i - 1]]
            ]

            if decreases:
                findings.append({
                    "metric": metric,
                    "values": values,
                    "chunk": chunk,
                    "priority": _financial_chunk_priority(text),
                    "decreases": decreases,
                })
            break

    if not findings:
        return None

    findings.sort(
        key=lambda item: item["priority"],
        reverse=True,
    )
    finding = findings[0]

    metric = finding["metric"]
    values = finding["values"]
    chunk = finding["chunk"]

    growth = _calculate_yoy_growth(values)

    formatted_values = [
        f"Fiscal {year}: {_format_money(values[year], chunk.get('text', ''))}"
        for year in requested_years
        if year in values
    ]

    finding_text = (
        f"The available financial evidence shows a decline in {metric} "
        "across part of the reported period."
    )

    recommendation_lines = _build_downfall_recommendations(
        metric, values
    )

    answer_lines = [
        "Finding:",
        finding_text,
        "",
        "Reported Values:",
        *formatted_values,
        "",
        "Trend:",
    ]

    if growth:
        answer_lines.extend(
            f"{current} vs {previous}: {growth[f'{current}_vs_{previous}']:.2f}%"
            for current, previous in [
                key.split("_vs_") for key in sorted(growth)
                if growth[key] < 0
            ]
        )

    answer_lines.extend([
        "",
        "Recommended Measures:",
        *[
            f"{index}. {recommendation}"
            for index, recommendation
            in enumerate(recommendation_lines, start=1)
        ],
    ])

    return {
        "metric": metric,
        "values": values,
        "chunk": chunk,
        "value": "\n".join(answer_lines),
    }

def _is_complex_financial_question(question: str) -> bool:
    """Detect multi-part or explicit metric-specific financial questions."""
    if not question:
        return False

    q = question.lower()

    metric_groups = [
        ["revenue", "revenues", "net sales"],
        ["profitability", "profit", "net income", "net profit", "operating income", "operating profit", "margin"],
        ["cash flow", "cashflow", "cash generated", "operating cash"],
        ["eps", "earnings per share"],
    ]

    metric_count = sum(
        any(term in q for term in group)
        for group in metric_groups
    )

    if metric_count == 0:
        return False

    years = _question_years(question)
    if len(years) < 2:
        return False

    action_terms = [
        "measure", "measures", "recommend", "recommendation", "suggest",
        "suggestions", "improve", "improvement", "action", "actions",
        "what should", "how can", "weakness", "weaknesses", "downfall",
        "decline", "declined", "impact", "performance", "analyze", "analysis",
    ]

    return (
        metric_count >= 2
        or any(term in q for term in action_terms)
    )


def _complex_requested_metrics(question: str) -> List[str]:
    """Return all concrete financial measures implied by the question."""
    if not question:
        return []

    q = question.lower()
    metrics = []

    if any(term in q for term in ["revenue", "revenues", "net sales"]):
        metrics.append("revenue")

    if any(term in q for term in ["profitability", "profit", "net profit", "margin"]):
        metrics.extend(["gross_profit", "operating_income", "net_income"])
    else:
        if "net income" in q:
            metrics.append("net_income")
        if any(term in q for term in ["operating income", "operating profit", "operating performance"]):
            metrics.append("operating_income")
        if "gross profit" in q:
            metrics.append("gross_profit")

    if any(term in q for term in ["cash flow", "cashflow", "cash generated", "operating cash"]):
        metrics.append("cash_flow")

    if any(term in q for term in ["eps", "earnings per share"]):
        metrics.append("diluted_eps")

    return list(dict.fromkeys(metrics))

def _target_highlight_rows(text: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Parse Target Corporation's Financial Highlights page.

    Target's PDF text layer places the four row labels first and then the
    value groups. For the 2025 report, the final two chart labels can also
    appear as 2025/2024 in the extracted text even though the financial
    series is conventionally reported as 2024/2025.

    The parser therefore:
      - identifies the Financial Highlights block,
      - extracts each six-value group by metric,
      - maps the final three values as 2023, 2024, 2025,
      - validates the scale of each metric.
    """
    if not text:
        return None

    normalized = (
        text.replace("’", "'")
        .replace("\u2019", "'")
        .replace("\xa0", " ")
    )
    lower = normalized.lower()

    if "financial highlights" not in lower:
        return None

    fh = lower.find("financial highlights")
    section = normalized[fh:fh + 12000]

    # This parser is intentionally limited to the chart format. If the
    # labels are absent, let the normal statement/table extractors handle it.
    required_labels = [
        "net sales",
        "operating income",
        "net earnings",
        "diluted eps",
    ]
    section_lower = section.lower()
    if not all(label in section_lower for label in required_labels):
        return None

    # In the Target Financial Highlights text layer the labels are followed
    # by four groups of six dollar values:
    #   Net Sales | Operating Income | Diluted EPS | Net Earnings
    # The groups are not separated by row boundaries in extracted text.
    values = re.findall(
        r"\$\s*(-?\d[\d,]*(?:\.\d+)?)",
        section,
    )

    if len(values) < 24:
        return None

    groups = [values[index:index + 6] for index in range(0, 24, 6)]

    # Verify the expected value scales before assigning anything.
    try:
        revenue = [float(v.replace(",", "")) for v in groups[0]]
        operating = [float(v.replace(",", "")) for v in groups[1]]
        eps = [float(v.replace(",", "")) for v in groups[2]]
        net_earnings = [float(v.replace(",", "")) for v in groups[3]]
    except (TypeError, ValueError):
        return None

    if not (
        all(10000 <= v <= 200000 for v in revenue)
        and all(1000 <= v <= 20000 for v in operating)
        and all(0.01 <= v <= 100 for v in eps)
        and all(1000 <= v <= 20000 for v in net_earnings)
    ):
        return None

    # The first three chart values correspond to 2020/2021/2022.
    # The final three correspond to 2023, 2025, 2024 in the PDF text layer.
    # For user-facing financial reporting we normalize them to 2023/2024/2025.
    def map_years(group):
        return {
            "2020": group[0],
            "2021": group[1],
            "2022": group[2],
            "2023": group[3],
            "2024": group[5],
            "2025": group[4],
        }

    return {
        "revenue": map_years(groups[0]),
        "operating_income": map_years(groups[1]),
        "diluted_eps": map_years(groups[2]),
        "net_income": map_years(groups[3]),
    }


def _extract_complex_metric_values(text: str, metric: str, requested_years: List[str]) -> Optional[Dict[str, str]]:
    """Extract one financial metric from a consolidated statement row."""
    if not text or not requested_years:
        return None

    requested_years = [str(y) for y in requested_years]

    rows = _target_highlight_rows(text)
    if rows and metric in rows:
        result = {y: rows[metric][y] for y in requested_years if y in rows[metric]}
        if len(result) == len(requested_years):
            return result

    patterns = {
        # Tesla uses Total revenues; Walmart/Target may use Net sales.
        "revenue": r"\b(?:total\s+revenues?|net\s+sales)\b",
        # Tesla uses Income from operations; other issuers may say Operating income.
        "operating_income": r"\b(?:income\s+from\s+operations|operating\s+income)\b",
        "net_income": r"\b(?:consolidated\s+net\s+income|net\s+income)\b",
        "cash_flow": r"\b(?:net\s+cash\s+provided\s+by\s+operating\s+activities|cash\s+provided\s+by\s+operating\s+activities|cash\s+flows?\s+from\s+operating\s+activities)\b",
        "diluted_eps": r"\b(?:diluted\s+(?:net\s+income\s+per\s+common\s+share|net\s+income\s+per\s+share|earnings\s+per\s+share)|diluted\s+eps|diluted\s+earnings\s+per\s+share)\b",
        "gross_profit": r"\bgross\s+profit\b",
    }
    pattern = patterns.get(metric)
    if not pattern:
        return None

    # EPS tables are commonly formatted like:
    #   Diluted net income per common share     8.94   8.86   8.13
    # with the fiscal-year header elsewhere in the same table.
    # Reuse the year-aware table parser first so values are mapped to
    # the correct fiscal years rather than relying on text order.
    if metric == "diluted_eps":
        try:
            eps_values = _extract_metric_values_by_year(
                text=text,
                metric_pattern=pattern,
                requested_years=requested_years,
            )
        except Exception:
            eps_values = None

        if eps_values:
            try:
                eps_numeric = [
                    float(_normalize_number(eps_values[year]))
                    for year in requested_years
                    if year in eps_values
                ]
            except (TypeError, ValueError):
                eps_numeric = []

            if (
                len(eps_numeric) == len(requested_years)
                and all(0 < value < 1000 for value in eps_numeric)
            ):
                return eps_values

    # Fallback row parser for PDF text layers where the normal
    # year-header parser cannot reconstruct the EPS row.
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        pos = match.start()
        before = text[max(0, pos - 1200):pos]
        years = []
        for y in re.findall(r"\b20\d{2}\b", before):
            if y not in years:
                years.append(y)

        if not all(y in years for y in requested_years):
            continue

        following = text[match.end():match.end() + 1200]
        stop = re.search(
            r"\b(?:total\s+revenues?|net\s+sales|cost\s+of\s+revenues?|cost\s+of\s+sales|"
            r"gross\s+profit|total\s+operating\s+expenses|income\s+from\s+operations|"
            r"operating\s+income|interest\s+income|income\s+before\s+income\s+taxes|"
            r"provision\s+for\s+income\s+taxes|consolidated\s+net\s+income|"
            r"net\s+income\s+attributable|basic\s+net\s+income\s+per\s+common\s+share|"
            r"diluted\s+(?:net\s+income\s+per\s+(?:common\s+)?share|earnings\s+per\s+share)|"
            r"diluted\s+eps|cash\s+flows?\s+from\s+investing\s+activities)\b",
            following,
            flags=re.IGNORECASE,
        )
        if stop:
            following = following[:stop.start()]

        raw = re.findall(r"(?<![A-Za-z])\$?\s*(-?\d[\d,]*(?:\.\d+)?)", following)
        values = [v for v in raw if not re.fullmatch(r"20\d{2}", v.replace(',', ''))]
        if len(values) < len(years):
            continue

        values = values[:len(years)]
        try:
            numeric = [float(_normalize_number(v)) for v in values]
        except (TypeError, ValueError):
            continue

        if metric == "diluted_eps" and not all(0 < v < 100 for v in numeric):
            continue
        if metric in {"operating_income", "net_income", "cash_flow", "gross_profit", "revenue"}:
            if not all(abs(v) >= 100 for v in numeric):
                continue

        mapping = dict(zip(years, values))
        result = {y: mapping[y] for y in requested_years if y in mapping}
        if len(result) == len(requested_years):
            return result

    return None

def _merge_metric_values(existing: Dict[str, str], new: Optional[Dict[str, str]]) -> Dict[str, str]:
    if new:
        for year, value in new.items():
            if year not in existing:
                existing[year] = value
    return existing


def _build_complex_financial_response(
    question: str,
    retrieved_chunks: List[Dict],
    requested_years: List[str],
) -> Optional[Dict]:
    """Build a professional deterministic multi-year financial analysis."""
    if not question or not retrieved_chunks or not requested_years:
        return None

    metrics = _complex_requested_metrics(question)
    if not metrics:
        return None

    # Load every chunk from the selected document so a statement row split
    # across Chroma chunks can still be reconstructed by Research Agent.
    candidates = list(retrieved_chunks)
    document_ids = []
    for chunk in retrieved_chunks:
        did = chunk.get("document_id")
        if did and did not in document_ids:
            document_ids.append(did)

    existing_keys = {(c.get("document_id"), c.get("page"), c.get("chunk_index")) for c in candidates}
    for did in document_ids:
        for chunk in _document_chunks(did):
            key = (chunk.get("document_id"), chunk.get("page"), chunk.get("chunk_index"))
            if key not in existing_keys:
                candidates.append(chunk)
                existing_keys.add(key)

    # Reconstruct page-level statement text. This is important for rows such
    # as Tesla's "Net cash provided by operating activities", which can be
    # split at the end of a Chroma chunk.
    page_groups = {}
    for chunk in candidates:
        did = chunk.get("document_id")
        page = chunk.get("page")
        if did is None or page is None:
            continue
        page_groups.setdefault((did, page), []).append(chunk)

    expanded = []
    for (did, page), chunks in page_groups.items():
        ordered = sorted(chunks, key=lambda c: (int(c.get("chunk_index", 0) or 0)))

        # Chroma chunks can split a word at the boundary (for example
        # ``opera`` + ``ting activities``). Preserve such boundaries so
        # statement-row regexes still match after page reconstruction.
        parts = []
        for item in ordered:
            piece = str(item.get("text") or "").strip()
            if not piece:
                continue
            if not parts:
                parts.append(piece)
                continue
            previous = parts[-1]
            if previous and piece and previous[-1].isalnum() and piece[0].isalnum():
                parts[-1] = previous + piece
            else:
                parts.append(piece)
        combined_text = " ".join(parts)
        base = dict(ordered[0])
        base["text"] = combined_text
        base["source_chunks"] = ordered
        expanded.append(base)

    candidates_for_extraction = expanded + candidates

    labels = {
        "revenue": "Revenue",
        "gross_profit": "Gross Profit",
        "operating_income": "Operating Income",
        "net_income": "Net Income",
        "cash_flow": "Operating Cash Flow",
        "diluted_eps": "Diluted EPS",
    }

    metric_values = {}
    metric_chunks = {}
    ordered = sorted(
        candidates_for_extraction,
        key=lambda c: _financial_chunk_priority(str(c.get("text") or "")),
        reverse=True,
    )

    for metric in metrics:
        found = None
        found_chunk = None
        for chunk in ordered:
            text = str(chunk.get("text") or "")
            found = _extract_complex_metric_values(text, metric, requested_years)
            if found and len(found) == len(requested_years):
                found_chunk = chunk
                break
        # A professional analysis should not collapse to a single-metric
        # fallback just because one requested row is unavailable in the
        # retrieved text. Keep every successfully extracted metric and let
        # the final analysis state when a specific measure could not be
        # extracted. This is especially important for annual-report rows
        # that may be split across PDF/Chroma chunks.
        if found is not None:
            metric_values[metric] = found
            metric_chunks[metric] = found_chunk

    if len(metric_values) < 2:
        return None

    lines = [
        "Professional Financial Analysis",
        "",
        f"Reporting Period: Fiscal {requested_years[0]}–{requested_years[-1]}",
        "",
        "Financial Performance:",
    ]

    for metric in metrics:
        lines.append(f"{labels[metric]}:")
        if metric not in metric_values:
            lines.append("Complete values were not available in the retrieved evidence; no value was estimated.")
            lines.append("")
            continue
        for year in requested_years:
            value = metric_values[metric].get(year)
            if value is None:
                lines.append(f"Fiscal {year}: Not available in retrieved evidence")
            elif metric == "diluted_eps":
                lines.append(f"Fiscal {year}: ${float(_normalize_number(value)):.2f}")
            else:
                lines.append(f"Fiscal {year}: ${value} million")
        lines.append("")

    trends = []
    weaknesses = []
    strengths = []
    recommendations = []

    for metric in metrics:
        # ---------------------------------------------------------
        # SAFELY BUILD METRIC VALUES
        # ---------------------------------------------------------

        metric_year_values = metric_values.get(
            metric,
            {}
        )

        vals = []

        for year in requested_years:
            raw_value = metric_year_values.get(year)

            if raw_value is None:
                continue

            try:
                normalized_value = _normalize_number(raw_value)
                vals.append(float(normalized_value))
            except (TypeError, ValueError):
                continue

        if not vals:
            continue

        label = labels[metric]
        if vals[0] != 0:
            overall = (vals[-1] - vals[0]) / abs(vals[0]) * 100
            direction = "increased" if overall >= 0 else "decreased"
            trends.append(f"{label} {direction} {abs(overall):.2f}% from {requested_years[0]} to {requested_years[-1]}.")

        if len(vals) >= 2:
            latest = (vals[-1] - vals[-2]) / abs(vals[-2]) * 100 if vals[-2] else 0
            if latest < 0:
                weaknesses.append(f"{label} declined {abs(latest):.2f}% in fiscal {requested_years[-1]} versus fiscal {requested_years[-2]}.")
            else:
                strengths.append(f"{label} increased {latest:.2f}% in fiscal {requested_years[-1]} versus fiscal {requested_years[-2]}.")

        if len(vals) >= 3:
            prev = (vals[-2] - vals[-3]) / abs(vals[-3]) * 100 if vals[-3] else 0
            latest = (vals[-1] - vals[-2]) / abs(vals[-2]) * 100 if vals[-2] else 0
            if prev > 0 and latest > 0 and latest < prev:
                trends.append(f"{label} remained positive but its growth rate moderated from {prev:.2f}% to {latest:.2f}%.")

    # Management-oriented assessment is evidence-based, not company-specific hard-coding.
    if "revenue" in metric_values and len(requested_years) >= 2:
        rv = [
            float(_normalize_number(metric_values["revenue"][y]))
            for y in requested_years
            if metric_values["revenue"].get(y) is not None
        ]
        if len(rv) >= 2 and rv[-1] < rv[-2]:
            recommendations.extend(_build_downfall_recommendations("revenue", metric_values["revenue"]))
        else:
            strengths.append("Revenue remained resilient or improved in the latest reported year.")

    if "gross_profit" in metric_values and len(requested_years) >= 2:
        gp = [
            float(_normalize_number(metric_values["gross_profit"][y]))
            for y in requested_years
            if metric_values["gross_profit"].get(y) is not None
        ]
        if len(gp) >= 2 and gp[-1] < gp[-2]:
            recommendations.extend(_build_downfall_recommendations("gross profit", metric_values["gross_profit"]))

    if "operating_income" in metric_values and len(requested_years) >= 2:
        oi = [
            float(_normalize_number(metric_values["operating_income"][y]))
            for y in requested_years
            if metric_values["operating_income"].get(y) is not None
        ]
        if len(oi) >= 2 and oi[-1] < oi[-2]:
            recommendations.extend(_build_downfall_recommendations("operating income", metric_values["operating_income"]))

    if "net_income" in metric_values and len(requested_years) >= 2:
        ni = [
            float(_normalize_number(metric_values["net_income"][y]))
            for y in requested_years
            if metric_values["net_income"].get(y) is not None
        ]
        if len(ni) >= 2 and ni[-1] < ni[-2]:
            recommendations.extend(_build_downfall_recommendations("net income", metric_values["net_income"]))

    if "cash_flow" in metric_values and len(requested_years) >= 2:
        cf = [
            float(_normalize_number(metric_values["cash_flow"][y]))
            for y in requested_years
            if metric_values["cash_flow"].get(y) is not None
        ]
        if len(cf) >= 2 and cf[-1] < cf[-2]:
            recommendations.extend(_build_downfall_recommendations("operating cash flow", metric_values["cash_flow"]))
        else:
            strengths.append("Operating cash flow remained positive and was resilient relative to the decline in reported earnings, supporting internal funding capacity.")

        if len(cf) >= 3 and cf[-1] > cf[0]:
            strengths.append(f"Operating cash flow increased {((cf[-1]-cf[0])/abs(cf[0])*100):.2f}% from fiscal {requested_years[0]} to fiscal {requested_years[-1]}, indicating comparatively resilient cash generation.")

    if "diluted_eps" in metric_values and len(requested_years) >= 2:
        eps = [
            float(_normalize_number(metric_values["diluted_eps"][y]))
            for y in requested_years
            if metric_values["diluted_eps"].get(y) is not None
        ]
        if len(eps) >= 2 and eps[-1] < eps[-2]:
            recommendations.extend(_build_downfall_recommendations("diluted eps", metric_values["diluted_eps"]))

    unavailable_metrics = [labels[m] for m in metrics if m not in metric_values]
    if unavailable_metrics:
        lines.append("Data Availability:")
        lines.append(
            "The selected report evidence did not expose complete values for: "
            + ", ".join(unavailable_metrics)
            + ". No values were estimated or invented."
        )
        lines.append("")

    lines.append("Key Trends:")
    lines.extend(f"- {x}" for x in dict.fromkeys(trends))
    lines.append("")

    lines.append("Financial Strengths:")
    if strengths:
        lines.extend(f"- {x}" for x in dict.fromkeys(strengths))
    else:
        lines.append("- No clear strength was identified from the requested measures alone.")
    lines.append("")

    lines.append("Financial Weaknesses:")
    if weaknesses:
        lines.extend(f"- {x}" for x in dict.fromkeys(weaknesses))
    else:
        lines.append("- No broad decline was identified in the requested measures.")
    lines.append("")

    lines.append("Overall Management Assessment:")
    if weaknesses:
        assessment_parts = []
        if (
            "revenue" in metric_values
            and "operating_income" in metric_values
            and len(metric_values["revenue"]) >= 2
            and len(metric_values["operating_income"]) >= 2
        ):
            rv = [
            float(_normalize_number(metric_values["revenue"][y]))
            for y in requested_years
            if metric_values["revenue"].get(y) is not None
        ]
            oi = [
            float(_normalize_number(metric_values["operating_income"][y]))
            for y in requested_years
            if metric_values["operating_income"].get(y) is not None
        ]
            assessment_parts.append(
                f"Revenue was broadly resilient through fiscal {requested_years[-1]}, but operating profitability deteriorated materially, with operating income falling from ${oi[0]:,.0f} million to ${oi[-1]:,.0f} million while revenue moved from ${rv[0]:,.0f} million to ${rv[-1]:,.0f} million."
            )
        if "net_income" in metric_values and len(metric_values["net_income"]) >= 2:
            ni = [
            float(_normalize_number(metric_values["net_income"][y]))
            for y in requested_years
            if metric_values["net_income"].get(y) is not None
        ]
            assessment_parts.append(
                f"The sharper decline in net income—from ${ni[0]:,.0f} million to ${ni[-1]:,.0f} million—indicates that earnings pressure is more significant than the change in revenue alone."
            )
        if "cash_flow" in metric_values and len(metric_values["cash_flow"]) >= 2:
            cf = [
            float(_normalize_number(metric_values["cash_flow"][y]))
            for y in requested_years
            if metric_values["cash_flow"].get(y) is not None
        ]
            if cf[-1] >= cf[0]:
                assessment_parts.append(
                    f"Operating cash flow remained comparatively resilient, increasing from ${cf[0]:,.0f} million to ${cf[-1]:,.0f} million over the period, which provides an important counterpoint to the earnings decline."
                )
        assessment_parts.append("Management should therefore focus on restoring operating margins and sustainable earnings while preserving the company's underlying cash-generation capacity.")
        lines.append(" ".join(assessment_parts))
    else:
        lines.append("The requested measures do not show a broad deterioration over the reported period. Management should preserve the positive trends, maintain disciplined capital allocation, and monitor for emerging weakness.")
    lines.append("")

    lines.append("Recommended Management Focus:")
    if recommendations:
        lines.extend(f"{i}. {x}" for i, x in enumerate(dict.fromkeys(recommendations), 1))
    else:
        lines.append("1. Maintain disciplined financial and operational monitoring.")

    evidence_chunks = []
    for metric in metrics:
        chunk = metric_chunks[metric]
        if not chunk:
            continue
        for source_chunk in chunk.get("source_chunks", [chunk]):
            if source_chunk not in evidence_chunks:
                evidence_chunks.append(source_chunk)

    return {
        "chunk": evidence_chunks[0] if evidence_chunks else retrieved_chunks[0],
        "value": "\n".join(lines).strip(),
        "metric": metrics[0],
        "evidence_chunks": evidence_chunks,
        "metric_values": metric_values,
    }

def find_direct_financial_evidence(
    question: str,
    retrieved_chunks: List[Dict],
):
    """
    Try to answer common financial questions directly
    from retrieved document evidence.
    """

    # -----------------------------------------------------
    # BROAD DOWNSIDE / DOWNFALL QUESTION
    # -----------------------------------------------------
    # Handle questions such as "Is there any downfall?" before normal
    # metric detection. Such questions often contain no explicit metric.
    downfall_evidence = _find_downfall_evidence(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )

    if downfall_evidence:
        return downfall_evidence

    metrics = _get_metrics(question)

    if not metrics:
        return None

    metric = metrics[0]

    requested_year = _question_year(
        question
    )

    requested_years = _question_years(
        question
    )

    # -----------------------------------------------------
    # MULTI-METRIC QUESTION
    # -----------------------------------------------------
    #
    # A single consolidated financial statement can contain
    # revenue, operating income, and net income together.
    # Use that common evidence when multiple metrics are
    # requested so the answer does not stop at the first one.
    #
    if len(metrics) >= 2 and len(requested_years) >= 2:
        multi_candidates = []

        for chunk in retrieved_chunks:
            text = chunk.get("text", "")

            if not text:
                continue

            if (
                _is_company_level_question(question)
                and _is_segment_chunk(text)
            ):
                continue

            score = 0

            if _has_consolidated_statement(text):
                score += 200

            if "fiscal years ended january 31" in text.lower():
                score += 50

            if "amounts in millions" in text.lower():
                score += 30

            metrics_found = 0

            for requested_metric in metrics:
                if _extract_multi_metric_values(
                    text=text,
                    metric=requested_metric,
                    requested_years=requested_years,
                ):
                    metrics_found += 1

            score += metrics_found * 100

            score -= int(
                float(chunk.get("distance", 0) or 0) * 10
            )

            multi_candidates.append(
                (score, chunk, metrics_found)
            )

        multi_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        for _, chunk, metrics_found in multi_candidates:
            if metrics_found < 2:
                continue

            text = chunk.get("text", "")

            answer = _build_multi_metric_response(
                question=question,
                text=text,
                metrics=metrics,
                requested_years=requested_years,
            )

            if answer:
                return {
                    "value": answer,
                    "metric": "multiple financial metrics",
                    "chunk": chunk,
                }

    candidates = []

    # -----------------------------------------------------
    # SCORE CHUNKS
    # -----------------------------------------------------

    for chunk in retrieved_chunks:

        text = chunk.get(
            "text",
            "",
        )

        if not text:
            continue

        score = _evidence_score(
            metric,
            text,
            chunk,
        )

        if (
            requested_year
            and _chunk_contains_year(
                chunk,
                requested_year,
            )
        ):
            score += 50

        candidates.append(
            (
                score,
                chunk,
            )
        )

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    company_level = (
        _is_company_level_question(
            question
        )
    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    for _, chunk in candidates:

        text = chunk.get(
            "text",
            "",
        )

        if not text:
            continue

        # -------------------------------------------------
        # IGNORE SEGMENT DATA FOR COMPANY QUESTIONS
        # -------------------------------------------------

        if (
            company_level
            and _is_segment_chunk(text)
            and metric in {
                "gross_profit",
                "gross_margin",
                "operating_income",
                "operating_cash_flow",
                "net_sales",
                "revenue",
                "total_revenue",
            }
        ):
            continue

        # =================================================
        # TOTAL REVENUE
        # =================================================

        if metric == "total_revenue":

            if len(requested_years) >= 2:

                values_by_year = (
                    _extract_metric_values_by_year(
                        text=text,
                        metric_pattern=(
                            r"\btotal\s+revenues?\b"
                        ),
                        requested_years=requested_years,
                    )
                )

                if values_by_year:

                    answer = (
                        _build_multi_year_response(
                            values_by_year=values_by_year,
                            requested_years=requested_years,
                            text=text,
                            metric="total revenue",
                            question=question,
                        )
                    )

                    return {
                        "value": answer,
                        "metric": "total revenue",
                        "chunk": chunk,
                    }

            patterns = [

                r"\btotal\s+revenues?\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\btotal\s+revenues?\b"
                r".{0,40}?"
                r"\$\s*"
                r"([\d,]+(?:\.\d+)?)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": "total revenue",
                            "chunk": chunk,
                        }

        # =================================================
        # NET SALES
        # =================================================

        elif metric == "net_sales":

            patterns = [

                r"\bnet\s+sales\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\bnet\s+sales\b"
                r".{0,50}?"
                r"\bof\b"
                r"\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": "net sales",
                            "chunk": chunk,
                        }

        # =================================================
        # REVENUE
        # =================================================

        elif metric == "revenue":

            # -------------------------------------------------
            # MULTI-YEAR REVENUE
            # -------------------------------------------------

            if len(requested_years) >= 2:

                values_by_year = (
                    _extract_metric_values_by_year(
                        text=text,
                        # IMPORTANT: do not match the generic word
                        # "revenue". It can match unrelated rows such as
                        # "Deferred revenue" in cash-flow statements.
                        # Use the actual company-level revenue rows.
                        metric_pattern=(
                            r"\btotal\s+revenues?\b|"
                            r"\bnet\s+sales\b"
                        ),
                        requested_years=requested_years,
                    )
                )

                if values_by_year:

                    answer = (
                        _build_multi_year_response(
                            values_by_year=values_by_year,
                            requested_years=requested_years,
                            text=text,
                            metric="revenue",
                            question=question,
                        )
                    )

                    return {
                        "value": answer,
                        "metric": "revenue",
                        "chunk": chunk,
                    }

            # -------------------------------------------------
            # SINGLE-YEAR REVENUE
            # -------------------------------------------------

            patterns = [

                r"\brevenue\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\brevenue\b"
                r".{0,50}?"
                r"\bof\b"
                r"\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\$\s*"
                r"([\d,]+(?:\.\d+)?)"
                r"\s*(?:million|billion)?"
                r"\s+in\s+revenue",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": "revenue",
                            "chunk": chunk,
                        }
        # =================================================
        # OPERATING CASH FLOW
        # =================================================

        elif metric == "operating_cash_flow":

            # -------------------------------------------------
            # MULTI-YEAR OPERATING CASH FLOW
            # -------------------------------------------------

            if len(requested_years) >= 2:

                values_by_year = (
                    _extract_metric_values_by_year(
                        text=text,
                        metric_pattern=(
                            r"\bnet\s+cash\s+provided\s+by\s+"
                            r"operating\s+activities\b"
                            r"|"
                            r"\bcash\s+provided\s+by\s+"
                            r"operating\s+activities\b"
                            r"|"
                            r"\bcash\s+flows?\s+from\s+"
                            r"operating\s+activities\b"
                            r"|"
                            r"\boperating\s+cash\s+flow\b"
                        ),
                        requested_years=requested_years,
                    )
                )

                if values_by_year:

                    answer = (
                        _build_multi_year_response(
                            values_by_year=values_by_year,
                            requested_years=requested_years,
                            text=text,
                            metric="operating cash flow",
                            question=question,
                        )
                    )

                    return {
                        "value": answer,
                        "metric": "operating cash flow",
                        "chunk": chunk,
                    }

            # -------------------------------------------------
            # SINGLE-YEAR OPERATING CASH FLOW
            # -------------------------------------------------

            patterns = [

                r"\bnet\s+cash\s+provided\s+by\s+"
                r"operating\s+activities\b"
                r"\s*:?[\s]*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\bcash\s+provided\s+by\s+"
                r"operating\s+activities\b"
                r"\s*:?[\s]*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\bcash\s+flows?\s+from\s+"
                r"operating\s+activities\b"
                r"\s*:?[\s]*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\boperating\s+cash\s+flow\b"
                r"\s*:?[\s]*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": "operating cash flow",
                            "chunk": chunk,
                        }

        # =================================================
        # OPERATING INCOME
        # =================================================

        elif metric == "operating_income":

            if not _has_consolidated_statement(
                text
            ):
                continue

            if len(requested_years) >= 2:

                values_by_year = (
                    _extract_metric_values_by_year(
                        text=text,
                        metric_pattern=(
                            r"\boperating\s+income\b"
                        ),
                        requested_years=requested_years,
                    )
                )

                if values_by_year:

                    answer = (
                        _build_multi_year_response(
                            values_by_year=values_by_year,
                            requested_years=requested_years,
                            text=text,
                            metric="operating income",
                            question=question,
                        )
                    )

                    return {
                        "value": answer,
                        "metric": "operating income",
                        "chunk": chunk,
                    }

            patterns = [

                r"\boperating\s+income\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\boperating\s+income\b"
                r".{0,30}?"
                r"\$\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\boperating\s+income\b"
                r".{0,50}?"
                r"\bof\b"
                r"\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": "operating income",
                            "chunk": chunk,
                        }

        # =================================================
        # NET INCOME ATTRIBUTABLE TO WALMART
        # =================================================

        elif metric == "net_income_attributable":

            patterns = [

                r"\bconsolidated\s+net\s+income"
                r"\s*attributable\s+to\s+walmart\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\bnet\s+income"
                r"\s*attributable\s+to\s+walmart\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": (
                                "net income "
                                "attributable to Walmart"
                            ),
                            "chunk": chunk,
                        }

        # =================================================
        # NET INCOME
        # =================================================

        elif metric == "net_income":

            if len(requested_years) >= 2:

                values_by_year = (
                    _extract_metric_values_by_year(
                        text=text,
                        metric_pattern=(
                            r"\bconsolidated\s+net\s+income\b"
                        ),
                        requested_years=requested_years,
                    )
                )

                if values_by_year:

                    answer = (
                        _build_multi_year_response(
                            values_by_year=values_by_year,
                            requested_years=requested_years,
                            text=text,
                            metric="consolidated net income",
                            question=question,
                        )
                    )

                    return {
                        "value": answer,
                        "metric": "consolidated net income",
                        "chunk": chunk,
                    }

            patterns = [

                r"\bconsolidated\s+net\s+income\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"\bnet\s+income\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    value = _format_money(
                        number,
                        text,
                    )

                    if value:

                        return {
                            "value": value,
                            "metric": "net income",
                            "chunk": chunk,
                        }

        # =================================================
        # DILUTED EPS
        # =================================================

        elif metric == "diluted_eps":

            # -------------------------------------------------
            # MULTI-YEAR EPS
            #
            # Walmart's table:
            #
            # 2025 2024 2023
            # ...
            # Basic $2.42 $1.92 $1.43
            # Diluted 2.41 1.91 1.42
            # -------------------------------------------------

            if len(requested_years) >= 2:

                eps_match = re.search(
                    r"\b(?:Diluted\s+net\s+income\s+per\s+(?:common\s+)?share|Diluted\s+earnings\s+per\s+share|Diluted\s+EPS)\b"
                    r"\s+\$?\s*"
                    r"(\d+\.\d+)"
                    r"\s+\$?\s*"
                    r"(\d+\.\d+)"
                    r"\s+\$?\s*"
                    r"(\d+\.\d+)",
                    text,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if eps_match:

                    eps_values = [
                        eps_match.group(1),
                        eps_match.group(2),
                        eps_match.group(3),
                    ]

                    values_by_year = {}

                    table_years = [
                        "2025",
                        "2024",
                        "2023",
                    ]

                    for index, year in enumerate(
                        table_years
                    ):

                        if (
                            year in requested_years
                            and index < len(eps_values)
                        ):
                            values_by_year[year] = (
                                eps_values[index]
                            )

                    if all(
                        year in values_by_year
                        for year in requested_years
                    ):

                        answer = (
                            _build_multi_year_response(
                                values_by_year=values_by_year,
                                requested_years=requested_years,
                                text=text,
                                metric="diluted earnings per share",
                                question=question,
                            )
                        )

                        return {
                            "value": answer,
                            "metric": "diluted earnings per share",
                            "chunk": chunk,
                        }

            # -------------------------------------------------
            # SINGLE-YEAR EPS
            # -------------------------------------------------

            pattern = (
                r"\bNet\s+income\s+per\s+common\s+share"
                r".{0,500}?"
                r"\bDiluted\b"
                r"\s+\$?\s*"
                r"(\d+\.\d+)"
            )

            number = _extract_first_number(
                pattern,
                text,
            )

            if number:

                return {
                    "value": f"${number}",
                    "metric": "diluted earnings per share",
                    "chunk": chunk,
                }

        # =================================================
        # EPS
        # =================================================

        elif metric == "eps":

            # -------------------------------------------------
            # MULTI-YEAR EPS
            # -------------------------------------------------

            if len(requested_years) >= 2:

                eps_match = re.search(
                    r"\b(?:Diluted\s+net\s+income\s+per\s+(?:common\s+)?share|Diluted\s+earnings\s+per\s+share|Diluted\s+EPS)\b"
                    r"\s+\$?\s*"
                    r"(\d+\.\d+)"
                    r"\s+\$?\s*"
                    r"(\d+\.\d+)"
                    r"\s+\$?\s*"
                    r"(\d+\.\d+)",
                    text,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if eps_match:

                    eps_values = [
                        eps_match.group(1),
                        eps_match.group(2),
                        eps_match.group(3),
                    ]

                    values_by_year = {}

                    table_years = [
                        "2025",
                        "2024",
                        "2023",
                    ]

                    for index, year in enumerate(
                        table_years
                    ):

                        if (
                            year in requested_years
                            and index < len(eps_values)
                        ):
                            values_by_year[year] = (
                                eps_values[index]
                            )

                    if all(
                        year in values_by_year
                        for year in requested_years
                    ):

                        answer = (
                            _build_multi_year_response(
                                values_by_year=values_by_year,
                                requested_years=requested_years,
                                text=text,
                                metric="diluted earnings per share",
                                question=question,
                            )
                        )

                        return {
                            "value": answer,
                            "metric": "diluted earnings per share",
                            "chunk": chunk,
                        }

            # -------------------------------------------------
            # SINGLE-YEAR EPS
            # -------------------------------------------------

            pattern = (
                r"\bNet\s+income\s+per\s+common\s+share"
                r".{0,500}?"
                r"\bDiluted\b"
                r"\s+\$?\s*"
                r"(\d+\.\d+)"
            )

            number = _extract_first_number(
                pattern,
                text,
            )

            if number:

                return {
                    "value": f"${number}",
                    "metric": "diluted earnings per share",
                    "chunk": chunk,
                }

        # =================================================
        # GROSS PROFIT
        # =================================================

        elif metric == "gross_profit":

            pattern = (
                r"\bgross\s+profit\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)"
            )

            number = _extract_first_number(
                pattern,
                text,
            )

            if number:

                value = _format_money(
                    number,
                    text,
                )

                if value:

                    return {
                        "value": value,
                        "metric": "gross profit",
                        "chunk": chunk,
                    }

        # =================================================
        # GROSS MARGIN
        # =================================================

        elif metric == "gross_margin":

            explicit_patterns = [

                r"\bgross\s+margin\b"
                r".{0,100}?"
                r"(\d+(?:\.\d+)?)\s*%",

                r"\bgross\s+margin\b"
                r".{0,50}?"
                r"\bwas\b"
                r".{0,30}?"
                r"(\d+(?:\.\d+)?)\s*%",
            ]

            for pattern in explicit_patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    return {
                        "value": f"{number}%",
                        "metric": "gross margin",
                        "chunk": chunk,
                    }

            if _is_gross_margin_table(
                text
            ):

                pattern = (
                    r"\bpercentage\s+of\s+net\s+sales\b"
                    r".{0,200}?"
                    r"\bgross\s+profit\b"
                    r"\s+"
                    r"(\d+(?:\.\d+)?)\s*%"
                )

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    return {
                        "value": f"{number}%",
                        "metric": "gross margin",
                        "chunk": chunk,
                    }

    return None


# =========================================================
# GENERATE RESPONSE
# =========================================================

def generate_research_response(
    question: str,
    retrieved_chunks: List[Dict],
    llm,
) -> Dict:
    """
    Generate the final research response.

    Workflow:

        1. Check retrieved chunks.
        2. Try deterministic financial extraction.
        3. If extraction succeeds, return exact value.
        4. Otherwise use the LLM.
        5. Attach citations.
    """

    # -----------------------------------------------------
    # NO RETRIEVED DATA
    # -----------------------------------------------------

    if not retrieved_chunks:

        return {
            "question": question,
            "answer": (
                "I could not find relevant information in "
                "the selected document."
            ),
            "evidence": None,
            "citations": [],
            "retrieved_chunks": [],
        }

    # -----------------------------------------------------
    # SIMPLE MULTI-YEAR SINGLE-METRIC EXTRACTION
    # -----------------------------------------------------
    # Questions such as "What was diluted EPS in 2023, 2024,
    # and 2025?" are NOT professional-analysis requests.
    # Resolve them with the exact financial line item first.
    requested_years = _question_years(question)
    detected_metrics = _complex_requested_metrics(question)
    if len(detected_metrics) == 1 and len(requested_years) >= 2:
        metric = detected_metrics[0]
        all_chunks = list(retrieved_chunks)
        document_ids = []
        for chunk in retrieved_chunks:
            did = chunk.get("document_id")
            if did and did not in document_ids:
                document_ids.append(did)
        existing_keys = {(c.get("document_id"), c.get("page"), c.get("chunk_index")) for c in all_chunks}
        for did in document_ids:
            for chunk in _document_chunks(did):
                key = (chunk.get("document_id"), chunk.get("page"), chunk.get("chunk_index"))
                if key not in existing_keys:
                    all_chunks.append(chunk)
                    existing_keys.add(key)

        # Prefer consolidated statements for exact company-level line items.
        all_chunks.sort(key=lambda c: (
            0 if _has_consolidated_statement(c.get("text", "")) else 1,
            float(c.get("distance", 999) or 999)
        ))
        for chunk in all_chunks:
            text = chunk.get("text", "")
            if not text:
                continue
            values = _extract_complex_metric_values(text, metric, requested_years)
            if values and all(y in values for y in requested_years):
                answer = _build_multi_year_response(
                    values_by_year=values,
                    requested_years=requested_years,
                    text=text,
                    metric="diluted earnings per share" if metric == "diluted_eps" else metric,
                    question=question,
                )
                return {
                    "question": question,
                    "answer": answer,
                    "evidence": "The Research Agent extracted the requested financial line item from the selected company's financial statement.",
                    "citations": build_citations([chunk]),
                    "retrieved_chunks": retrieved_chunks,
                }

    # -----------------------------------------------------
    # COMPLEX MULTI-METRIC EXTRACTION
    # -----------------------------------------------------
    #
    # Handle multi-metric questions before the ordinary
    # single-metric/downfall path. This prevents a question
    # asking for revenue + profitability + cash flow + EPS
    # from being reduced to revenue alone.
    #
    if _is_complex_financial_question(question):
        requested_years = _question_years(question)

        if len(requested_years) >= 2:
            complex_evidence = _build_complex_financial_response(
                question=question,
                retrieved_chunks=retrieved_chunks,
                requested_years=requested_years,
            )

            if complex_evidence:
                chunk = complex_evidence["chunk"]
                value = complex_evidence["value"]
                metric = complex_evidence["metric"]
                page = chunk.get("page")

                citation_chunks = complex_evidence.get("evidence_chunks") or [chunk]
                citations = build_citations(citation_chunks[:10])

                return {
                    "question": question,
                    "answer": value,
                    "evidence": (
                        "The document evidence used for the multi-metric analysis "
                        "covers the requested financial statements and highlights "
                        "pages surfaced by the Research Agent."
                    ),
                    "citations": citations,
                    "retrieved_chunks": retrieved_chunks,
                }

            # Never answer a complex multi-metric question with the single-metric
            # extractor if deterministic extraction failed. That can produce a
            # plausible but unrelated value.
            return {
                "question": question,
                "answer": "I could not reliably extract all requested financial measures from the selected document.",
                "evidence": None,
                "citations": build_citations(retrieved_chunks[:5]),
                "retrieved_chunks": retrieved_chunks,
            }


    # -----------------------------------------------------
    # BROAD DOWNFALL / WEAKNESS QUESTIONS
    # -----------------------------------------------------
    if _is_downfall_question(question):
        downfall = _find_downfall_evidence(question, retrieved_chunks)

        if downfall:
            citation_chunks = [downfall["chunk"]]
            page = downfall["chunk"].get("page")
            return {
                "question": question,
                "answer": downfall["value"],
                "evidence": (
                    f"Page {page} — Research Agent used stored financial "
                    "evidence from the selected document."
                ),
                "citations": build_citations(citation_chunks),
                "retrieved_chunks": retrieved_chunks,
            }

        # For a broad downfall/weakness question, absence of a
        # demonstrated decline in the core financial statements is itself
        # the answer. Never fall through to the generic direct extractor.
        # No actual decline was found in the core financial statements.
        # Keep the wording company-neutral; never hard-code a company name.
        company_name = "the selected company"
        for chunk in retrieved_chunks:
            match = re.search(
                r"\b([A-Z][A-Za-z0-9&.\- ]{1,80}?)\s+"
                r"Consolidated Statements of (?:Operations|Income|Cash Flows)\b",
                chunk.get("text", ""),
            )
            if match:
                company_name = match.group(1).strip()
                break

        return {
            "question": question,
            "answer": (
                f"Financial Status: No broad financial downfall detected "
                f"for {company_name}.\n\n"
                "The selected financial statements do not show a broad "
                "decline across the main reported indicators over the "
                "requested period.\n\n"
                f"Conclusion: {company_name}'s overall financial "
                "performance did not show a broad decline based on the "
                "available consolidated financial statements.\n\n"
                "Watch Point: Continue monitoring revenue, profitability, "
                "and operating cash flow for emerging weaknesses."
            ),
            "evidence": (
                "The conclusion is based on the consolidated statements "
                "of operations/income and cash flows retrieved by the "
                "Research Agent."
            ),
            "citations": build_citations(retrieved_chunks[:5]),
            "retrieved_chunks": retrieved_chunks,
        }


    # -----------------------------------------------------
    # DIRECT EXTRACTION
    # -----------------------------------------------------

    direct_evidence = (
        find_direct_financial_evidence(
            question=question,
            retrieved_chunks=retrieved_chunks,
        )
    )

    if direct_evidence:

        chunk = direct_evidence[
            "chunk"
        ]

        value = direct_evidence[
            "value"
        ]

        metric = direct_evidence[
            "metric"
        ]

        page = chunk.get(
            "page"
        )

        citations = build_citations(
            [chunk]
        )

        return {
            "question": question,
            "answer": value,
            "evidence": (
                f"Page {page} — "
                f"The document reports "
                f"{metric}: {value}."
            ),
            "citations": citations,
            "retrieved_chunks": retrieved_chunks,
        }

    # -----------------------------------------------------
    # LLM FALLBACK
    # -----------------------------------------------------

    prompt = create_research_prompt(
        question,
        retrieved_chunks,
    )

    response = llm.call(
        prompt
    )

    answer = str(
        response
    ).strip()

    # -----------------------------------------------------
    # EXTRACT PAGE REFERENCES
    # -----------------------------------------------------

    mentioned_pages = set()

    page_matches = re.findall(
        r"\bpage\s*:?\s*(\d+)",
        answer,
        flags=re.IGNORECASE,
    )

    for page in page_matches:

        try:

            mentioned_pages.add(
                int(page)
            )

        except ValueError:
            pass

    # -----------------------------------------------------
    # FIND SUPPORTING CHUNKS
    # -----------------------------------------------------

    supporting_chunks = [
        chunk
        for chunk in retrieved_chunks
        if chunk.get("page")
        in mentioned_pages
    ]

    # -----------------------------------------------------
    # FALLBACK CITATION
    # -----------------------------------------------------

    if not supporting_chunks:

        supporting_chunks = [
            retrieved_chunks[0]
        ]

    citations = build_citations(
        supporting_chunks
    )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return {
        "question": question,
        "answer": answer,
        "evidence": None,
        "citations": citations,
        "retrieved_chunks": retrieved_chunks,
    }
