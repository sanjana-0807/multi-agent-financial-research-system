import re
from typing import List, Dict, Optional

from .metrics import detect_metric, extract_year
from .reasoning import create_research_prompt
from .citation import build_citations


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

    Walmart annual report tables commonly say:

        (Amounts in millions, except per share data)

    Therefore:

        674,538 -> $674,538 million
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

    # -----------------------------------------------------
    # UNIT DETECTION
    # -----------------------------------------------------

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

    Example:

        Percentage of net sales
        Gross profit 27.2% 26.8% 26.6%
    """

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

    This is intentionally NOT another implementation of
    metric detection.

    The project should have one source of truth:
        metrics.py -> detect_metric()
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
        ],

        "eps": [
            "diluted net income per common share",
            "diluted earnings per share",
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

    requested_year = None

    # We don't need the question here.
    # Presence of a fiscal-year table is useful evidence.
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

    This is only used for evidence scoring.
    """

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
    Get the year from the centralized metrics.py
    implementation.
    """

    try:
        return extract_year(question)

    except Exception:
        return None


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
# DIRECT FINANCIAL EVIDENCE
# =========================================================

def find_direct_financial_evidence(
    question: str,
    retrieved_chunks: List[Dict],
):
    """
    Try to answer common financial questions directly
    from retrieved document evidence.

    This avoids unnecessary LLM calls for straightforward
    numerical questions.
    """

    metric = _get_metric(question)

    if metric is None:
        return None

    requested_year = _question_year(
        question
    )

    candidates = []

    # -----------------------------------------------------
    # SCORE ALL CHUNKS
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

        # Prefer chunks that actually contain
        # the requested fiscal year.
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
    # SORT BEST FIRST
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
    # SEARCH BEST CANDIDATES
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
                "net_sales",
                "revenue",
            }
        ):
            continue

        # =================================================
        # TOTAL REVENUE
        # =================================================

        if metric == "total_revenue":

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

                # Example:
                # Net sales $674,538

                r"\bnet\s+sales\b"
                r"\s*:?\s*\$?\s*"
                r"([\d,]+(?:\.\d+)?)",

                # Example:
                # net sales of $121.9 billion

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
        # OPERATING INCOME
        # =================================================

        elif metric == "operating_income":

            # For a company-level question,
            # only use consolidated statements.

            if not _has_consolidated_statement(
                text
            ):
                continue

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

            patterns = [

                r"\bdiluted\s+net\s+income\s+per\s+common\s+share"
                r"(?:\s+attributable\s+to\s+walmart)?"
                r"\s+\$?\s*"
                r"(\d+\.\d+)",

                r"\bdiluted\s+earnings\s+per\s+share\b"
                r".{0,50}?"
                r"\$?\s*"
                r"(\d+\.\d+)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    return {
                        "value": f"${number}",
                        "metric": (
                            "diluted earnings per share"
                        ),
                        "chunk": chunk,
                    }

        # =================================================
        # EPS
        # =================================================

        elif metric == "eps":

            patterns = [

                r"\bdiluted\s+net\s+income\s+per\s+common\s+share"
                r"(?:\s+attributable\s+to\s+walmart)?"
                r"\s+\$?\s*"
                r"(\d+\.\d+)",

                r"\bdiluted\s+earnings\s+per\s+share\b"
                r".{0,50}?"
                r"\$?\s*"
                r"(\d+\.\d+)",
            ]

            for pattern in patterns:

                number = _extract_first_number(
                    pattern,
                    text,
                )

                if number:

                    return {
                        "value": f"${number}",
                        "metric": (
                            "diluted earnings per share"
                        ),
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

            # -------------------------------------------------
            # CASE 1: EXPLICIT GROSS MARGIN
            # -------------------------------------------------

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

            # -------------------------------------------------
            # CASE 2: WALMART TABLE
            # -------------------------------------------------

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
                f"{metric} of {value}."
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