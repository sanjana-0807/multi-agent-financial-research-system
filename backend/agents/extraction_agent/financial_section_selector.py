"""
Financial statement section selector.

Extracts:
    - income_statement
    - balance_sheet
    - cash_flow

The source document may contain several statements and repeated
headings. This selector keeps each statement isolated.
"""

import re
from typing import Dict


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Normalize dashes.
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Preserve newlines.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)

    return text.strip()


# ============================================================
# HEADINGS
# ============================================================

OPERATIONS_PATTERNS = [
    r"STATEMENT\s+OF\s+OPERATIONS",
    r"STATEMENTS?\s+OF\s+OPERATIONS",
    r"CONSOLIDATED\s+STATEMENT\s+OF\s+OPERATIONS",
    r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+OPERATIONS",
    r"INCOME\s+STATEMENT",
    r"STATEMENT\s+OF\s+INCOME",
    r"STATEMENTS?\s+OF\s+INCOME",
]

BALANCE_PATTERNS = [
    r"BALANCE\s+SHEET",
    r"BALANCE\s+SHEETS",
    r"CONSOLIDATED\s+BALANCE\s+SHEET",
    r"CONSOLIDATED\s+BALANCE\s+SHEETS",
    r"STATEMENT\s+OF\s+FINANCIAL\s+POSITION",
    r"STATEMENTS?\s+OF\s+FINANCIAL\s+POSITION",
]

CASH_PATTERNS = [
    r"STATEMENT\s+OF\s+CASH\s+FLOWS",
    r"STATEMENTS?\s+OF\s+CASH\s+FLOWS",
    r"CONSOLIDATED\s+STATEMENT\s+OF\s+CASH\s+FLOWS",
    r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+CASH\s+FLOWS",
]


# ============================================================
# HEADING SEARCH
# ============================================================

def _find_all(text: str, patterns: list[str]) -> list[int]:
    positions = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            positions.append(match.start())

    return sorted(set(positions))


def _first_after(
    text: str,
    patterns: list[str],
    start: int,
) -> int:

    positions = []

    for pattern in patterns:
        match = re.search(
            pattern,
            text[start:],
            flags=re.IGNORECASE,
        )

        if match:
            positions.append(
                start + match.start()
            )

    if not positions:
        return -1

    return min(positions)


# ============================================================
# MAIN SECTION EXTRACTION
# ============================================================

def extract_financial_sections(
    document_text: str,
) -> Dict[str, str]:

    empty = {
        "income_statement": "",
        "balance_sheet": "",
        "cash_flow": "",
    }

    if not document_text:
        return empty

    text = _normalize(document_text)

    # --------------------------------------------------------
    # Find first statement headings.
    # --------------------------------------------------------

    operations_positions = _find_all(
        text,
        OPERATIONS_PATTERNS,
    )

    balance_positions = _find_all(
        text,
        BALANCE_PATTERNS,
    )

    cash_positions = _find_all(
        text,
        CASH_PATTERNS,
    )

    operations_start = (
        operations_positions[0]
        if operations_positions
        else -1
    )

    balance_start = (
        balance_positions[0]
        if balance_positions
        else -1
    )

    cash_start = (
        cash_positions[0]
        if cash_positions
        else -1
    )

    # --------------------------------------------------------
    # Make sure boundaries are AFTER previous statement.
    # --------------------------------------------------------

    if operations_start >= 0:

        if balance_start <= operations_start:
            balance_start = _first_after(
                text,
                BALANCE_PATTERNS,
                operations_start + 1,
            )

        if cash_start <= operations_start:
            cash_start = _first_after(
                text,
                CASH_PATTERNS,
                operations_start + 1,
            )

    if balance_start >= 0:

        if cash_start <= balance_start:
            cash_start = _first_after(
                text,
                CASH_PATTERNS,
                balance_start + 1,
            )

    # --------------------------------------------------------
    # INCOME STATEMENT
    # --------------------------------------------------------

    income_statement = ""

    if operations_start >= 0:

        if balance_start > operations_start:

            income_statement = text[
                operations_start:
                balance_start
            ]

        elif cash_start > operations_start:

            income_statement = text[
                operations_start:
                cash_start
            ]

        else:

            income_statement = text[
                operations_start:
            ]

    # --------------------------------------------------------
    # BALANCE SHEET
    # --------------------------------------------------------

    balance_sheet = ""

    if balance_start >= 0:

        if cash_start > balance_start:

            balance_sheet = text[
                balance_start:
                cash_start
            ]

        else:

            balance_sheet = text[
                balance_start:
            ]

    # --------------------------------------------------------
    # CASH FLOW
    # --------------------------------------------------------

    cash_flow = ""

    if cash_start >= 0:

        cash_flow = text[
            cash_start:
        ]

    return {
        "income_statement": income_statement.strip(),
        "balance_sheet": balance_sheet.strip(),
        "cash_flow": cash_flow.strip(),
    }


# ============================================================
# OLLAMA CONTEXT
# ============================================================

def build_extraction_context(
    document_text: str,
) -> str:

    sections = extract_financial_sections(
        document_text
    )

    parts = []

    if sections["income_statement"]:
        parts.append(
            "=== STATEMENT OF OPERATIONS ===\n"
            + sections["income_statement"]
        )

    if sections["balance_sheet"]:
        parts.append(
            "=== BALANCE SHEET ===\n"
            + sections["balance_sheet"]
        )

    if sections["cash_flow"]:
        parts.append(
            "=== STATEMENT OF CASH FLOWS ===\n"
            + sections["cash_flow"]
        )

    return "\n\n".join(parts)