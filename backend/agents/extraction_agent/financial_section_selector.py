# agents/extraction_agent/financial_section_selector.py

"""
Generic Financial Statement Section Selector

Purpose
-------
Locate the ACTUAL financial statement tables inside arbitrary
annual reports.

This module is intentionally company-independent.

It does NOT contain:
    - Tesla-specific rules
    - Colgate-specific rules
    - PepsiCo-specific rules
    - Johnson & Johnson-specific rules

Strategy
--------
1. Find candidate statement headings.
2. Examine a window after every candidate.
3. Score each candidate using:
       - financial row keywords
       - year columns
       - numerical density
       - statement-specific terminology
       - table structure
4. Penalize:
       - table of contents
       - narrative text
       - MD&A discussion
       - very sparse candidates
5. Select the strongest candidate.
6. Trim the selected text to the actual statement region.

The result is suitable for downstream deterministic extraction.
"""

import re
from typing import Dict, List, Optional, Tuple


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalize_text(text: str) -> str:
    """
    Normalize PDF-extracted text while preserving useful
    financial information.
    """

    if not text:
        return ""

    replacements = {
        "\u00a0": " ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove repeated whitespace but preserve newlines.
    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# GENERIC HEADING PATTERNS
# ============================================================

INCOME_HEADINGS = [
    r"consolidated\s+statements?\s+of\s+earnings",
    r"consolidated\s+statements?\s+of\s+income",
    r"consolidated\s+statements?\s+of\s+operations",
    r"consolidated\s+income\s+statements?",
    r"statements?\s+of\s+earnings",
    r"statements?\s+of\s+income",
    r"statements?\s+of\s+operations",
    r"income\s+statements?",
    r"statement\s+of\s+profit\s+and\s+loss",
    r"statements?\s+of\s+profit\s+and\s+loss",
    r"consolidated\s+statements?\s+of\s+profit\s+and\s+loss",
]

BALANCE_HEADINGS = [
    r"consolidated\s+balance\s+sheets?",
    r"consolidated\s+balance\s+sheet",
    r"balance\s+sheets?",
    r"balance\s+sheet",
    r"consolidated\s+statements?\s+of\s+financial\s+position",
    r"statements?\s+of\s+financial\s+position",
    r"financial\s+position",
]

CASH_FLOW_HEADINGS = [
    r"consolidated\s+statements?\s+of\s+cash\s+flows?",
    r"statements?\s+of\s+cash\s+flows?",
    r"statement\s+of\s+cash\s+flows?",
    r"consolidated\s+cash\s+flow\s+statements?",
    r"cash\s+flow\s+statements?",
]


# ============================================================
# STATEMENT-SPECIFIC ROW KEYWORDS
# ============================================================

INCOME_KEYWORDS = [
    "revenue",
    "net revenue",
    "net sales",
    "sales to customers",
    "sales",
    "cost of sales",
    "cost of products sold",
    "cost of revenues",
    "cost of revenue",
    "gross profit",
    "gross margin",
    "operating income",
    "operating profit",
    "income from operations",
    "income before income taxes",
    "income before taxes",
    "earnings before taxes",
    "provision for income taxes",
    "income tax expense",
    "net income",
    "net earnings",
    "net income attributable",
    "net earnings attributable",
    "earnings per share",
    "earnings per common share",
    "diluted",
    "basic",
]

BALANCE_KEYWORDS = [
    "assets",
    "current assets",
    "total current assets",
    "cash and cash equivalents",
    "accounts receivable",
    "inventories",
    "property, plant and equipment",
    "goodwill",
    "intangible assets",
    "total assets",
    "liabilities",
    "current liabilities",
    "total current liabilities",
    "accounts payable",
    "long-term debt",
    "total liabilities",
    "shareholders' equity",
    "stockholders' equity",
    "shareholders equity",
    "stockholders equity",
    "total equity",
    "total liabilities and equity",
]

CASH_FLOW_KEYWORDS = [
    "cash flows from operating activities",
    "cash flow from operating activities",
    "operating activities",
    "net cash provided by operating activities",
    "net cash provided by operations",
    "net cash flows from operating activities",
    "cash flows from investing activities",
    "investing activities",
    "cash flows from financing activities",
    "financing activities",
    "depreciation and amortization",
    "capital expenditures",
    "capital spending",
    "net cash used in investing activities",
    "net cash used in financing activities",
    "net increase in cash",
    "cash and cash equivalents at end",
]


# ============================================================
# YEAR DETECTION
# ============================================================

YEAR_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b"
)


def _count_years(text: str) -> int:
    """
    Count distinct years.

    Actual financial tables usually contain two or more
    reporting years.
    """

    years = set(
        YEAR_PATTERN.findall(text)
    )

    return len(years)


# ============================================================
# NUMBER DETECTION
# ============================================================

NUMBER_PATTERN = re.compile(
    r"""
    (?:
        \(?
        -?
        (?:
            \d{1,3}(?:,\d{3})+
            |
            \d+
        )
        (?:\.\d+)?
        %?
        \)?
    )
    """,
    re.VERBOSE,
)


def _count_numbers(text: str) -> int:
    return len(
        NUMBER_PATTERN.findall(text)
    )


# ============================================================
# FINANCIAL KEYWORD COUNT
# ============================================================

def _count_keywords(
    text: str,
    keywords: List[str],
) -> int:

    lowered = text.lower()

    score = 0

    for keyword in keywords:

        if keyword.lower() in lowered:
            score += 1

    return score


# ============================================================
# NARRATIVE PENALTIES
# ============================================================

NARRATIVE_MARKERS = [
    "management's discussion",
    "management’s discussion",
    "liquidity and capital resources",
    "critical accounting",
    "risk factors",
    "business overview",
    "legal proceedings",
    "restructuring",
    "the company expects",
    "we expect",
    "our strategy",
    "our business",
    "outlook",
    "competition",
    "market conditions",
    "this discussion",
]


def _narrative_penalty(text: str) -> int:

    lowered = text.lower()

    penalty = 0

    for marker in NARRATIVE_MARKERS:

        occurrences = lowered.count(
            marker.lower()
        )

        penalty += min(
            occurrences * 3,
            15,
        )

    return penalty


# ============================================================
# TABLE OF CONTENTS PENALTY
# ============================================================

def _toc_penalty(
    candidate: str,
) -> int:

    lowered = candidate.lower()

    penalty = 0

    # TOCs commonly contain ".... 44" or "44"
    # immediately following section names.

    if re.search(
        r"\.{2,}\s*\d{1,3}\b",
        candidate,
    ):
        penalty += 15

    if re.search(
        r"\btable\s+of\s+contents\b",
        lowered,
    ):
        penalty += 30

    # Very short heading-only candidates are usually TOC
    # references.
    if len(candidate.strip()) < 250:
        penalty += 10

    return penalty


# ============================================================
# TABLE STRUCTURE SCORE
# ============================================================

def _table_structure_score(
    text: str,
    statement_type: str,
) -> int:
    """
    Score evidence that the candidate is an actual financial
    statement table rather than narrative prose.
    """

    score = 0

    # --------------------------------------------------------
    # Multiple years
    # --------------------------------------------------------

    years = _count_years(text)

    if years >= 3:
        score += 25
    elif years == 2:
        score += 18
    elif years == 1:
        score += 5

    # --------------------------------------------------------
    # Number density
    # --------------------------------------------------------

    numbers = _count_numbers(text)

    if numbers >= 20:
        score += 20
    elif numbers >= 10:
        score += 12
    elif numbers >= 5:
        score += 5

    # --------------------------------------------------------
    # Statement-specific rows
    # --------------------------------------------------------

    if statement_type == "income":
        score += min(
            _count_keywords(
                text,
                INCOME_KEYWORDS,
            ) * 4,
            48,
        )

        # Strong indicators of actual income statement.
        if re.search(
            r"\bnet\s+(income|earnings)\b",
            text,
            re.IGNORECASE,
        ):
            score += 10

        if re.search(
            r"\b(?:diluted|basic)\b",
            text,
            re.IGNORECASE,
        ):
            score += 5

    elif statement_type == "balance":

        score += min(
            _count_keywords(
                text,
                BALANCE_KEYWORDS,
            ) * 4,
            52,
        )

        if re.search(
            r"\btotal\s+assets\b",
            text,
            re.IGNORECASE,
        ):
            score += 15

        if re.search(
            r"\btotal\s+liabilities\b",
            text,
            re.IGNORECASE,
        ):
            score += 15

    elif statement_type == "cash_flow":

        score += min(
            _count_keywords(
                text,
                CASH_FLOW_KEYWORDS,
            ) * 4,
            52,
        )

        if re.search(
            r"\boperating\s+activities\b",
            text,
            re.IGNORECASE,
        ):
            score += 10

        if re.search(
            r"\binvesting\s+activities\b",
            text,
            re.IGNORECASE,
        ):
            score += 10

        if re.search(
            r"\bfinancing\s+activities\b",
            text,
            re.IGNORECASE,
        ):
            score += 10

    return score


# ============================================================
# CANDIDATE EXTRACTION
# ============================================================

def _find_candidates(
    text: str,
    patterns: List[str],
    statement_type: str,
) -> List[Tuple[int, int, str, int]]:

    candidates = []

    for pattern_text in patterns:

        pattern = re.compile(
            pattern_text,
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):

            start = match.start()

            # =================================================
            # IMPORTANT
            #
            # Only the text immediately following the heading
            # is used for classification.
            #
            # This prevents narrative references such as:
            #
            # "consolidated statements of earnings were
            # immaterial..."
            #
            # from being mistaken for the actual statement.
            # =================================================

            immediate_end = min(
                len(text),
                start + 1600,
            )

            immediate = text[
                start:immediate_end
            ]

            lowered = immediate.lower()

            score = 0

            # =================================================
            # 1. YEARS MUST APPEAR CLOSE TO THE HEADING
            # =================================================

            first_900 = immediate[:900]

            years = set(
                YEAR_PATTERN.findall(
                    first_900
                )
            )

            if len(years) >= 3:
                score += 35

            elif len(years) == 2:
                score += 25

            elif len(years) == 1:
                score += 5

            else:
                score -= 30

            # =================================================
            # 2. FINANCIAL ROWS MUST APPEAR CLOSE TO HEADING
            # =================================================

            if statement_type == "income":

                row_groups = [
                    [
                        "revenue",
                        "net revenue",
                        "net sales",
                        "sales to customers",
                    ],
                    [
                        "cost of sales",
                        "cost of products sold",
                        "cost of revenues",
                        "cost of revenue",
                    ],
                    [
                        "gross profit",
                    ],
                    [
                        "operating income",
                        "operating profit",
                        "income from operations",
                    ],
                    [
                        "income before income taxes",
                        "income before taxes",
                        "earnings before taxes",
                    ],
                    [
                        "net income",
                        "net earnings",
                    ],
                    [
                        "earnings per share",
                        "earnings per common share",
                    ],
                ]

            elif statement_type == "balance":

                row_groups = [
                    [
                        "current assets",
                        "total current assets",
                    ],
                    [
                        "total assets",
                    ],
                    [
                        "current liabilities",
                        "total current liabilities",
                    ],
                    [
                        "total liabilities",
                    ],
                    [
                        "shareholders' equity",
                        "stockholders' equity",
                        "shareholders equity",
                        "stockholders equity",
                    ],
                    [
                        "total equity",
                        "total liabilities and equity",
                    ],
                ]

            else:

                row_groups = [
                    [
                        "cash flows from operating activities",
                        "cash flow from operating activities",
                        "operating activities",
                    ],
                    [
                        "net cash provided by operating activities",
                        "net cash flows from operating activities",
                        "net cash provided by operations",
                    ],
                    [
                        "investing activities",
                    ],
                    [
                        "financing activities",
                    ],
                    [
                        "depreciation and amortization",
                    ],
                    [
                        "capital expenditures",
                        "capital spending",
                    ],
                ]

            # Count groups rather than individual words.
            # This prevents repeated mentions of one term from
            # producing a false positive.

            matched_groups = 0

            for group in row_groups:

                if any(
                    term.lower() in lowered
                    for term in group
                ):
                    matched_groups += 1

            # Strong evidence of an actual table.
            score += matched_groups * 15

            # =================================================
            # 3. REQUIRE MULTIPLE ROWS
            # =================================================

            if matched_groups >= 5:
                score += 35

            elif matched_groups >= 4:
                score += 25

            elif matched_groups >= 3:
                score += 12

            elif matched_groups <= 1:
                score -= 35

            # =================================================
            # 4. NUMERICAL DENSITY
            # =================================================

            number_count = _count_numbers(
                first_900
            )

            if number_count >= 20:
                score += 30

            elif number_count >= 12:
                score += 20

            elif number_count >= 8:
                score += 10

            elif number_count < 5:
                score -= 25

            # =================================================
            # 5. TABLE-LIKE YEAR + NUMBER COMBINATION
            # =================================================

            if (
                len(years) >= 2
                and number_count >= 10
                and matched_groups >= 3
            ):
                score += 30

            # =================================================
            # 6. NARRATIVE PENALTY
            # =================================================

            narrative_words = [
                "were immaterial",
                "was immaterial",
                "the company",
                "the results of",
                "as a result",
                "management",
                "discussion",
                "liquidity",
                "separation costs",
                "reported as",
                "reflected as",
                "described above",
                "described below",
                "we believe",
                "we expect",
                "our business",
            ]

            narrative_hits = sum(
                1
                for word in narrative_words
                if word in lowered[:900]
            )

            score -= narrative_hits * 12

            # =================================================
            # 7. TABLE OF CONTENTS PENALTY
            # =================================================

            toc_text = immediate[:500]

            if re.search(
                r"\.{2,}\s*\d{1,3}\b",
                toc_text,
            ):
                score -= 50

            # Typical TOC pattern:
            #
            # statements of earnings 44
            # statements of cash flows 47
            #

            if re.search(
                r"""
                (?:statements?|sheets?)
                \s+of\s+
                [a-z\s]+
                \s+\d{1,3}
                """,
                toc_text,
                re.IGNORECASE | re.VERBOSE,
            ):
                score -= 45

            # =================================================
            # 8. A REAL TABLE USUALLY HAS A FINANCIAL UNIT
            # =================================================

            unit_patterns = [
                "dollars in millions",
                "dollars and shares in millions",
                "in millions",
                "in thousands",
                "except per share",
                "except per share amounts",
            ]

            unit_found = any(
                unit in lowered[:1000]
                for unit in unit_patterns
            )

            if unit_found:
                score += 15

            # =================================================
            # 9. REQUIRE A STRONG TABLE SIGNAL
            # =================================================

            strong_table_signal = (
                len(years) >= 2
                and matched_groups >= 3
                and number_count >= 8
            )

            if strong_table_signal:
                score += 25
            else:
                score -= 20

            # =================================================
            # 10. STORE LARGER REGION ONLY AFTER SCORING
            # =================================================

            region_end = min(
                len(text),
                start + 9000,
            )

            candidates.append(
                (
                    start,
                    region_end,
                    text[start:region_end],
                    score,
                )
            )

    return candidates

# ============================================================
# DEDUPLICATE CANDIDATES
# ============================================================

def _deduplicate_candidates(
    candidates: List[Tuple[int, int, str, int]],
) -> List[Tuple[int, int, str, int]]:

    if not candidates:
        return []

    candidates = sorted(
        candidates,
        key=lambda x: x[0],
    )

    result = []

    for candidate in candidates:

        start = candidate[0]

        duplicate = False

        for existing in result:

            existing_start = existing[0]

            if abs(
                start - existing_start
            ) < 100:

                duplicate = True
                break

        if not duplicate:
            result.append(
                candidate
            )

    return result


# ============================================================
# SELECT BEST CANDIDATE
# ============================================================

def _select_best_candidate(
    text: str,
    patterns: List[str],
    statement_type: str,
) -> Optional[Tuple[int, int, str, int]]:

    candidates = _find_candidates(
        text,
        patterns,
        statement_type,
    )

    candidates = _deduplicate_candidates(
        candidates
    )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[3],
        reverse=True,
    )

    return candidates[0]


# ============================================================
# FIND END OF FINANCIAL TABLE
# ============================================================

END_MARKERS = [
    r"see\s+accompanying\s+notes",
    r"see\s+notes\s+to\s+the\s+consolidated",
    r"the\s+accompanying\s+notes",
    r"notes\s+to\s+the\s+financial\s+statements",
    r"notes\s+to\s+consolidated\s+financial\s+statements",
]


def _find_statement_end(
    text: str,
    max_length: int = 9000,
) -> int:
    """
    Find a sensible end for the selected financial statement.

    The first strong note/reference marker is preferred.
    """

    search_text = text[
        :max_length
    ]

    positions = []

    for marker in END_MARKERS:

        match = re.search(
            marker,
            search_text,
            re.IGNORECASE,
        )

        if match:
            positions.append(
                match.start()
            )

    if positions:

        return min(
            positions
        )

    # Fallback.
    return min(
        len(text),
        max_length,
    )


# ============================================================
# TRIM STATEMENT
# ============================================================

def _trim_statement(
    text: str,
) -> str:

    text = text.strip()

    end = _find_statement_end(
        text
    )

    trimmed = text[
        :end
    ].strip()

    # Avoid returning microscopic sections.
    if len(trimmed) < 200:

        return text[
            :min(
                len(text),
                5000,
            )
        ].strip()

    return trimmed


# ============================================================
# FALLBACK BY STRONG ROWS
# ============================================================

def _fallback_from_rows(
    text: str,
    statement_type: str,
) -> str:
    """
    Last-resort fallback.

    This is intentionally generic and does not know company
    names.

    It searches for a strong financial row and captures a
    bounded region around it.
    """

    if statement_type == "income":

        anchors = [
            r"\bnet\s+revenue\b",
            r"\bnet\s+sales\b",
            r"\bsales\s+to\s+customers\b",
            r"\bnet\s+income\b",
            r"\bnet\s+earnings\b",
        ]

    elif statement_type == "balance":

        anchors = [
            r"\btotal\s+assets\b",
            r"\btotal\s+liabilities\b",
            r"\btotal\s+assets\s+and\s+liabilities\b",
        ]

    else:

        anchors = [
            r"\bnet\s+cash\s+(?:provided|generated|used)",
            r"\bcash\s+flows?\s+from\s+operating\s+activities\b",
        ]

    for anchor in anchors:

        match = re.search(
            anchor,
            text,
            re.IGNORECASE,
        )

        if match:

            start = max(
                0,
                match.start() - 1500,
            )

            end = min(
                len(text),
                match.start() + 5000,
            )

            candidate = text[
                start:end
            ]

            if _count_years(candidate) >= 1:

                return _trim_statement(
                    candidate
                )

    return ""


# ============================================================
# MAIN SECTION SELECTOR
# ============================================================

def _select_statement(
    text: str,
    patterns: List[str],
    statement_type: str,
) -> str:

    candidate = _select_best_candidate(
        text,
        patterns,
        statement_type,
    )

    if candidate:

        start = candidate[0]

        # -----------------------------------------------
        # Start at the heading.
        # -----------------------------------------------

        region = text[
            start:
        ]

        # -----------------------------------------------
        # Limit the region.
        # -----------------------------------------------

        region = region[
            :9000
        ]

        trimmed = _trim_statement(
            region
        )

        # -----------------------------------------------
        # Verify that the selected region actually has
        # reasonable financial evidence.
        # -----------------------------------------------

        if (
            _count_years(trimmed) >= 1
            and _count_numbers(trimmed) >= 5
        ):

            return trimmed

    # ----------------------------------------------------
    # Fallback
    # ----------------------------------------------------

    return _fallback_from_rows(
        text,
        statement_type,
    )


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def extract_financial_sections(
    document_text: str,
) -> Dict[str, str]:
    """
    Extract the three primary financial statements from an
    arbitrary annual report.

    Returns:

        {
            "income_statement": "...",
            "balance_sheet": "...",
            "cash_flow": "..."
        }

    The function is company-independent.
    """

    if not document_text:

        return {
            "income_statement": "",
            "balance_sheet": "",
            "cash_flow": "",
        }

    text = _normalize_text(
        document_text
    )

    income = _select_statement(
        text,
        INCOME_HEADINGS,
        "income",
    )

    balance = _select_statement(
        text,
        BALANCE_HEADINGS,
        "balance",
    )

    cash_flow = _select_statement(
        text,
        CASH_FLOW_HEADINGS,
        "cash_flow",
    )

    return {
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow": cash_flow,
    }


# ============================================================
# DEBUGGING HELPER
# ============================================================

def debug_financial_sections(
    document_text: str,
) -> Dict[str, Dict[str, object]]:
    """
    Optional debugging helper.

    Useful for understanding which candidate was selected.

    This does not affect normal extraction.
    """

    if not document_text:

        return {}

    text = _normalize_text(
        document_text
    )

    output = {}

    configs = {
        "income_statement": (
            INCOME_HEADINGS,
            "income",
        ),
        "balance_sheet": (
            BALANCE_HEADINGS,
            "balance",
        ),
        "cash_flow": (
            CASH_FLOW_HEADINGS,
            "cash_flow",
        ),
    }

    for name, (
        patterns,
        statement_type,
    ) in configs.items():

        candidates = _deduplicate_candidates(
            _find_candidates(
                text,
                patterns,
                statement_type,
            )
        )

        candidates.sort(
            key=lambda x: x[3],
            reverse=True,
        )

        output[name] = {
            "candidate_count": len(
                candidates
            ),
            "top_candidates": [
                {
                    "position": c[0],
                    "score": c[3],
                    "preview": c[2][:500],
                }
                for c in candidates[:5]
            ],
        }

    return output
def build_extraction_context(
    document_text: str,
) -> str:
    """
    Build a compact context containing only the selected
    financial statements.

    Ollama should NOT receive the entire annual report.
    """

    sections = extract_financial_sections(
        document_text
    )

    parts = []

    if sections.get("income_statement"):
        parts.append(
            "===== INCOME_STATEMENT =====\n"
            + sections["income_statement"]
        )

    if sections.get("balance_sheet"):
        parts.append(
            "===== BALANCE_SHEET =====\n"
            + sections["balance_sheet"]
        )

    if sections.get("cash_flow"):
        parts.append(
            "===== CASH_FLOW =====\n"
            + sections["cash_flow"]
        )

    return "\n\n".join(parts)