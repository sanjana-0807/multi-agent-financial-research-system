import re
import uuid
from typing import Any

from fastapi import HTTPException

from models.document import DocumentModel
from models.chat import ChatMessage

from agents.research_agent.retriever import (
    retrieve_relevant_chunks,
)

from agents.research_agent.crew import (
    run_research,
)

from agents.research_agent.calculator import (
    extract_metric_value,
    calculate_percentage_change,
)

from integrations.web_search_client import (
    search_web,
)


# ============================================================
# CONFIGURATION
# ============================================================

NORMAL_TOP_K = 12
PROFILE_TOP_K = 20
PERCENTAGE_TOP_K = 30

MAX_EVIDENCE = 6
MAX_WEB_RESULTS = 3

# ChromaDB distance:
# Lower = stronger semantic similarity.
DOCUMENT_THRESHOLD = 0.70

# Profile questions are additionally validated by content.
PROFILE_THRESHOLD = 1.20


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _extract_years(question: str) -> list[int]:
    if not question:
        return []

    years = re.findall(
        r"\b20\d{2}\b",
        question,
    )

    return list(
        dict.fromkeys(
            int(year)
            for year in years
        )
    )


def _get_last_user_question(
    history: list[dict],
) -> str | None:

    for message in reversed(history):

        if message.get("role") != "user":
            continue

        content = _clean(
            message.get("content")
        )

        if content:
            return content

    return None


# ============================================================
# FOLLOW-UP QUESTION HANDLING
# ============================================================

def _resolve_follow_up_question(
    question: str,
    history: list[dict],
) -> str:

    if not history:
        return question

    previous = _get_last_user_question(
        history
    )

    if not previous:
        return question

    text = question.lower()

    # --------------------------------------------------------
    # Previous year
    # --------------------------------------------------------

    previous_year_phrases = (
        "previous year",
        "prior year",
        "last year",
        "preceding year",
        "previous fiscal year",
        "prior fiscal year",
        "last fiscal year",
    )

    if any(
        phrase in text
        for phrase in previous_year_phrases
    ):

        previous_years = _extract_years(
            previous
        )

        if previous_years:

            target_year = (
                previous_years[-1] - 1
            )

            matches = list(
                re.finditer(
                    r"\b20\d{2}\b",
                    previous,
                )
            )

            if matches:

                match = matches[-1]

                return (
                    previous[:match.start()]
                    + str(target_year)
                    + previous[match.end():]
                )

    # --------------------------------------------------------
    # Next year
    # --------------------------------------------------------

    next_year_phrases = (
        "next year",
        "following year",
        "next fiscal year",
    )

    if any(
        phrase in text
        for phrase in next_year_phrases
    ):

        previous_years = _extract_years(
            previous
        )

        if previous_years:

            target_year = (
                previous_years[-1] + 1
            )

            matches = list(
                re.finditer(
                    r"\b20\d{2}\b",
                    previous,
                )
            )

            if matches:

                match = matches[-1]

                return (
                    previous[:match.start()]
                    + str(target_year)
                    + previous[match.end():]
                )

    # --------------------------------------------------------
    # Generic contextual follow-up
    # --------------------------------------------------------

    return (
        "Previous user question:\n"
        f"{previous}\n\n"
        "Current user question:\n"
        f"{question}"
    )


# ============================================================
# QUESTION CLASSIFICATION
# ============================================================

def _is_percentage_question(
    question: str,
) -> bool:

    text = question.lower()

    return any(
        phrase in text
        for phrase in (
            "percentage change",
            "percentage difference",
            "percent change",
            "percent difference",
            "percentage increase",
            "percentage decrease",
            "percent increase",
            "percent decrease",
        )
    )


def _requires_current_information(
    question: str,
) -> bool:

    text = question.lower()

    return any(
        term in text
        for term in (
            "current",
            "currently",
            "latest",
            "today",
            "today's",
            "now",
            "recent",
            "recently",
            "as of",
        )
    )


def _is_profile_question(
    question: str,
) -> bool:

    text = question.lower()

    return any(
        term in text
        for term in (
            "ceo",
            "chief executive officer",
            "chief executive",
            "founder",
            "founders",
            "founded",
            "founding",
            "employee",
            "employees",
            "workforce",
            "headcount",
            "staff",
            "headquarters",
            "headquartered",
            "head office",
            "principal executive office",
            "management",
            "leadership",
            "executive",
            "executives",
            "business model",
            "what does the company do",
            "main business",
            "products",
            "services",
        )
    )


def _is_financial_question(
    question: str,
) -> bool:

    text = question.lower()

    return any(
        term in text
        for term in (
            "revenue",
            "revenues",
            "sales",
            "profit",
            "income",
            "earnings",
            "expense",
            "expenses",
            "assets",
            "liabilities",
            "cash flow",
            "gross profit",
            "operating income",
            "net income",
            "financial",
            "financial statement",
            "financial statements",
        )
    )


# ============================================================
# PROFILE RETRIEVAL QUERIES
# ============================================================

def _build_profile_queries(
    question: str,
) -> list[str]:

    text = question.lower()

    queries = [
        question,
    ]

    # --------------------------------------------------------
    # Founder
    # --------------------------------------------------------

    if (
        "founder" in text
        or "founded" in text
        or "founding" in text
    ):

        queries.extend(
            [
                "Who founded the company?",
                "Who were the founders of the company?",
                "Who established the company?",
                "Who started the company?",
                "Who created the company?",
                "Who were the original founders?",
                "Company founding history",
                "History of the company's founding",
                "Formation of the company",
                "Incorporation and founding of the company",
                "People who established the company",
            ]
        )

    # --------------------------------------------------------
    # CEO
    # --------------------------------------------------------

    elif (
        "ceo" in text
        or "chief executive" in text
    ):

        queries.extend(
            [
                "Who is the company's CEO?",
                "Who is the Chief Executive Officer?",
                "Who serves as Chief Executive Officer?",
                "Who is the company's chief executive?",
                "Who holds the CEO position?",
                "Company Chief Executive Officer",
            ]
        )

    # --------------------------------------------------------
    # Employees
    # --------------------------------------------------------

    elif (
        "employee" in text
        or "workforce" in text
        or "headcount" in text
        or "staff" in text
    ):

        queries.extend(
            [
                "How many employees does the company have?",
                "What is the company's employee headcount?",
                "How large is the company's workforce?",
                "How many people work for the company?",
                "Number of employees",
                "Total workforce",
            ]
        )

    # --------------------------------------------------------
    # Headquarters
    # --------------------------------------------------------

    elif (
        "headquarters" in text
        or "headquartered" in text
        or "head office" in text
    ):

        queries.extend(
            [
                "Where is the company's headquarters?",
                "Where is the company headquartered?",
                "What is the company's principal executive office?",
                "Where is the company's main office?",
                "Location of company headquarters",
                "Company headquarters address",
            ]
        )

    # --------------------------------------------------------
    # Management
    # --------------------------------------------------------

    elif (
        "management" in text
        or "leadership" in text
        or "executive" in text
    ):

        queries.extend(
            [
                "Who are the company's senior executives?",
                "Who are the company's executive officers?",
                "Who is part of senior management?",
                "Who are the company's key leaders?",
                "Company management and leadership",
            ]
        )

    # --------------------------------------------------------
    # Business
    # --------------------------------------------------------

    elif (
        "business" in text
        or "business model" in text
        or "what does the company do" in text
    ):

        queries.extend(
            [
                "What does the company do?",
                "What are the company's principal business activities?",
                "What are the company's main business operations?",
                "Description of the company's business",
            ]
        )

    return list(
        dict.fromkeys(
            query.strip()
            for query in queries
            if query and query.strip()
        )
    )


# ============================================================
# PROFILE CONTENT VALIDATION
# ============================================================

def _profile_content_matches(
    question: str,
    text: str,
) -> bool:

    if not text:
        return False

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower(),
    )

    question_text = question.lower()

    # --------------------------------------------------------
    # Headquarters
    # --------------------------------------------------------

    if (
        "headquarters" in question_text
        or "headquartered" in question_text
        or "head office" in question_text
        or "principal executive office" in question_text
    ):

        patterns = (
            "headquartered",
            "headquarters",
            "head office",
            "principal executive office",
            "principal office",
            "corporate headquarters",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    # --------------------------------------------------------
    # Founder
    # --------------------------------------------------------

    if (
        "founder" in question_text
        or "founded" in question_text
        or "founding" in question_text
    ):

        patterns = (
            "founded",
            "founder",
            "founders",
            "co-founded",
            "cofounder",
            "established",
            "formed",
            "incorporated",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    # --------------------------------------------------------
    # CEO
    # --------------------------------------------------------

    if (
        "ceo" in question_text
        or "chief executive" in question_text
    ):

        patterns = (
            "chief executive officer",
            "chief executive",
            "ceo",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    # --------------------------------------------------------
    # Employees
    # --------------------------------------------------------

    if (
        "employee" in question_text
        or "workforce" in question_text
        or "headcount" in question_text
        or "staff" in question_text
    ):

        patterns = (
            "employees",
            "employee",
            "workforce",
            "headcount",
            "personnel",
            "people employed",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    # --------------------------------------------------------
    # Management
    # --------------------------------------------------------

    if (
        "management" in question_text
        or "leadership" in question_text
        or "executive" in question_text
    ):

        patterns = (
            "management",
            "executive officer",
            "executive officers",
            "leadership",
            "senior management",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    # --------------------------------------------------------
    # Business
    # --------------------------------------------------------

    if (
        "business" in question_text
        or "business model" in question_text
        or "what does the company do" in question_text
    ):

        patterns = (
            "our business",
            "the company's business",
            "principal business",
            "business operations",
            "business activities",
            "products and services",
        )

        return any(
            pattern in normalized
            for pattern in patterns
        )

    return False


def _select_profile_evidence(
    question: str,
    evidence: list[dict],
) -> list[dict]:

    validated = []

    for item in evidence:

        text = item.get(
            "text",
            "",
        )

        content_match = (
            _profile_content_matches(
                question,
                text,
            )
        )

        try:
            distance = float(
                item.get("distance")
            )
        except (
            TypeError,
            ValueError,
        ):
            distance = 999999.0

        if (
            content_match
            and distance <= PROFILE_THRESHOLD
        ):
            validated.append(
                item
            )

    return _sort_evidence(
        validated
    )


# ============================================================
# FINANCIAL METRIC
# ============================================================

def _get_metric(
    question: str,
) -> str | None:

    text = question.lower()

    if (
        "total revenue" in text
        or "total revenues" in text
        or "revenue" in text
        or "revenues" in text
        or "net sales" in text
    ):
        return "Total revenues"

    if (
        "net income" in text
        or "net profit" in text
    ):
        return "Net income"

    if "gross profit" in text:
        return "Gross profit"

    if (
        "operating income" in text
        or "operating profit" in text
        or "income from operations" in text
    ):
        return "Income from operations"

    return None


# ============================================================
# FINANCIAL EXTRACTION
# ============================================================

def _extract_financial_value(
    question: str,
    evidence: list[dict],
):

    years = _extract_years(
        question
    )

    metric = _get_metric(
        question
    )

    if not years or not metric:
        return (
            None,
            None,
            None,
            None,
        )

    year = years[-1]

    candidates = []

    for item in evidence:

        text = item.get(
            "text",
            "",
        )

        if not text:
            continue

        # IMPORTANT:
        # Do not check for the literal metric name.
        # The calculator supports aliases such as:
        # Revenue, Revenues, Total revenue, Net sales, etc.

        try:
            value = extract_metric_value(
                text=text,
                metric=metric,
                year=year,
            )
        except Exception:
            continue

        if value is None:
            continue

        try:
            distance = float(
                item.get("distance")
            )
        except (
            TypeError,
            ValueError,
        ):
            distance = 999999.0

        candidates.append(
            (
                distance,
                item,
                value,
            )
        )

    if not candidates:
        return (
            None,
            None,
            year,
            metric,
        )

    candidates.sort(
        key=lambda item: item[0]
    )

    (
        _,
        source,
        value,
    ) = candidates[0]

    return (
        value,
        source,
        year,
        metric,
    )


# ============================================================
# TARGETED PERCENTAGE RETRIEVAL
# ============================================================

def _get_all_document_chunks(document_id: str) -> list[dict]:
    """Load all indexed chunks for exactly one document from Chroma."""
    try:
        from vectorstore.chroma_client import collection

        result = collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        print("Full document chunk load failed:", repr(exc))
        return []

    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    items = []

    for index, text in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        metadata = metadata or {}
        try:
            chunk_index = int(metadata.get("chunk_index"))
        except (TypeError, ValueError):
            chunk_index = index
        items.append({
            "text": text or "",
            "document_id": metadata.get("document_id", document_id),
            "filename": metadata.get("filename"),
            "page": metadata.get("page"),
            "chunk_index": chunk_index,
            "source": metadata.get("source"),
            "distance": None,
        })

    items.sort(key=lambda item: (item.get("chunk_index", 0), item.get("page") or 0))
    return items


def _percentage_statement_windows(document_id: str) -> list[dict]:
    """Build small document-order windows around consolidated income statements."""
    chunks = _get_all_document_chunks(document_id)
    if not chunks:
        return []

    windows = []
    # Annual reports use different names for the primary income statement:
    # Statements of Income, Statements of Operations, Statements of
    # Earnings, Profit and Loss, etc.  Match the statement concept rather
    # than one company-specific heading.
    marker_re = re.compile(
        r"consolidated\s+(?:statements?|income\s+statements?|"
        r"statements?\s+of\s+(?:income|operations?|earnings?|profit\s+and\s+loss)|"
        r"income\s+statements?|operations?\s+statements?|"
        r"earnings?\s+statements?|profit\s+and\s+loss\s+statements?)",
        re.IGNORECASE,
    )

    marker_indexes = []
    for i, item in enumerate(chunks):
        if marker_re.search(item.get("text", "")):
            marker_indexes.append(i)

    # If the heading is not in the same chunk as the row, a ±4 chunk window
    # is enough for normal annual-report chunking while keeping prompts small.
    for center in marker_indexes:
        start = max(0, center - 4)
        end = min(len(chunks), center + 5)
        selected = chunks[start:end]
        text = "\n".join(item.get("text", "") for item in selected)
        pages = [item.get("page") for item in selected if item.get("page") is not None]
        chunk_indices = [item.get("chunk_index") for item in selected]
        windows.append({
            "text": text,
            "source": selected[0] if selected else {},
            "pages": pages,
            "chunk_indices": chunk_indices,
        })

    # Some extractors omit the exact heading text. Also create semantic
    # candidates for chunks that contain the annual income-statement row.
    if not windows:
        for center, item in enumerate(chunks):
            text = item.get("text", "")
            lower = text.lower()
            has_revenue = re.search(
                r"\b(?:total\s+revenues?|revenue|revenues|net\s+sales)\b",
                lower,
            )
            has_financial_header = (
                "year ended" in lower
                or re.search(r"\b20\d{2}\b.*\b20\d{2}\b", lower)
            )
            if has_financial_header and has_revenue:
                start = max(0, center - 3)
                end = min(len(chunks), center + 4)
                selected = chunks[start:end]
                windows.append({
                    "text": "\n".join(x.get("text", "") for x in selected),
                    "source": selected[0],
                    "pages": [x.get("page") for x in selected if x.get("page") is not None],
                    "chunk_indices": [x.get("chunk_index") for x in selected],
                })

    # Deduplicate identical windows.
    seen = set()
    result = []
    for window in windows:
        key = (tuple(window["chunk_indices"]), window["text"][:500])
        if key in seen:
            continue
        seen.add(key)
        result.append(window)
    return result


def _parse_statement_number(value: str) -> float | None:
    if not value:
        return None
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    cleaned = value.replace("$", "").replace(",", "").replace("(", "").replace(")", "").strip()
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return -number if negative else number


def _number_matches(text: str) -> list[tuple[int, int, float]]:
    pattern = re.compile(
        r"(?<![\w])(?:\(\s*)?\$?\s*\d[\d,]*(?:\.\d+)?\s*\)?(?![\w])"
    )
    result = []
    for match in pattern.finditer(text):
        value = _parse_statement_number(match.group(0))
        if value is not None:
            result.append((match.start(), match.end(), value))
    return result


def _extract_table_years(text: str) -> list[int]:
    """Extract annual column years from financial-statement text.

    Prefer clean consecutive fiscal-year sequences. PDF extraction can place
    unrelated "year ended" phrases in the same window, so this helper avoids
    blindly taking the first matching occurrence.
    """
    if not text:
        return []

    candidates: list[tuple[int, list[int]]] = []

    # Explicit statement headers are preferred.
    for match in re.finditer(
        r"(?i)\b(?:for\s+the\s+)?years?\s+ended\b|\byears?\b",
        text,
    ):
        header = text[match.start():min(len(text), match.start() + 500)]
        date_years = re.findall(
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
            r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
            r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+"
            r"\d{1,2}(?:,\s*|\s+)(20\d{2})",
            header,
            re.IGNORECASE,
        )
        years = list(dict.fromkeys(int(y) for y in date_years))
        if len(years) >= 2:
            candidates.append((len(years), years[:5]))
            continue

        plain_years = list(dict.fromkeys(
            int(y) for y in re.findall(r"\b20\d{2}\b", header)
        ))
        if len(plain_years) >= 2:
            candidates.append((len(plain_years), plain_years[:5]))

    all_years = [int(y) for y in re.findall(r"\b20\d{2}\b", text)]
    for i in range(len(all_years) - 2):
        seq = all_years[i:i + 3]
        if len(set(seq)) != 3:
            continue
        if (
            seq[1] == seq[0] + 1 and seq[2] == seq[1] + 1
        ) or (
            seq[1] == seq[0] - 1 and seq[2] == seq[1] - 1
        ):
            candidates.append((3, seq))

    if candidates:
        candidates.sort(
            key=lambda item: (item[0], max(item[1]) if item[1] else 0),
            reverse=True,
        )
        return candidates[0][1]

    unique_years = list(dict.fromkeys(all_years[:5]))
    return unique_years if len(unique_years) >= 2 else []


def _extract_row_years(text: str, row_position: int) -> list[int]:
    """Extract the fiscal-year column order nearest to a financial row.

    This row-local lookup is important for flattened PDFs: a narrative phrase
    such as "recognized as revenue during the year ended 2025" must not be
    mistaken for the column header of the consolidated revenue table.
    """
    if not text:
        return []

    start = max(0, row_position - 1600)
    context = text[start:row_position]

    header_matches = list(re.finditer(
        r"(?i)\b(?:for\s+the\s+)?years?\s+ended\b|\byears?\b",
        context,
    ))

    regions = []
    if header_matches:
        # Try the closest header first.
        regions.append(context[header_matches[-1].start():])
    regions.append(context[-800:])
    regions.append(context)

    candidates: list[tuple[int, list[int]]] = []

    for region in regions:
        year_matches = list(re.finditer(r"\b20\d{2}\b", region))
        years = [int(m.group(0)) for m in year_matches]

        for i in range(len(years) - 2):
            seq = years[i:i + 3]
            if len(set(seq)) != 3:
                continue
            if (
                seq[1] == seq[0] + 1 and seq[2] == seq[1] + 1
            ) or (
                seq[1] == seq[0] - 1 and seq[2] == seq[1] - 1
            ):
                candidates.append((3, seq))

        unique = list(dict.fromkeys(years))
        if len(unique) >= 2:
            candidates.append((len(unique), unique[:5]))

    if candidates:
        candidates.sort(
            key=lambda item: (item[0], max(item[1]) if item[1] else 0),
            reverse=True,
        )
        return candidates[0][1]

    return []


def _extract_revenue_rows(text: str) -> list[dict]:
    """Find revenue/net-sales rows and the numbers immediately following them."""
    if not text:
        return []

    label_re = re.compile(
        r"(?im)(?<![\w])(?:total\s+net\s+sales|total\s+revenues?|net\s+sales|revenue)(?![\w])"
    )
    stop_re = re.compile(
        r"(?im)\b(?:cost\s+of\s+revenue|gross\s+profit|operating\s+expenses|"
        r"operating\s+income|income\s+before|income\s+tax|net\s+income)\b"
    )

    rows = []
    for match in label_re.finditer(text):
        value_start = match.end()
        value_end = min(len(text), value_start + 500)
        following = text[value_start:value_end]

        stop = stop_re.search(following)
        if stop:
            following = following[:stop.start()]

        nums = _number_matches(following)
        if len(nums) < 2:
            continue

        values = [value for _, _, value in nums[:5]]
        rows.append({
            "label": match.group(0).strip(),
            "position": match.start(),
            "values": values,
            "years": _extract_row_years(text, match.start()),
        })

    return rows


def _find_best_revenue_table(
    document_id: str,
    old_year: int,
    new_year: int,
) -> dict | None:
    """Find one consolidated revenue row containing both requested years."""
    windows = _percentage_statement_windows(document_id)
    print("Statement windows:", len(windows))

    candidates = []
    all_chunks = _get_all_document_chunks(document_id)
    by_index = {item.get("chunk_index"): item for item in all_chunks}

    for window in windows:
        text = window.get("text", "")
        if not text:
            continue

        lower = text.lower()
        is_income_statement = any(
            phrase in lower
            for phrase in (
                "consolidated statements of income",
                "consolidated statement of income",
                "consolidated income statements",
                "consolidated income statement",
                "consolidated statements of operations",
                "consolidated statement of operations",
            )
        )
        if not is_income_statement:
            continue

        fallback_years = _extract_table_years(text)

        for row in _extract_revenue_rows(text):
            values = row.get("values", [])
            row_years = row.get("years") or fallback_years

            if old_year not in row_years or new_year not in row_years:
                continue

            old_index = row_years.index(old_year)
            new_index = row_years.index(new_year)
            if old_index >= len(values) or new_index >= len(values):
                continue

            label = row.get("label", "").lower().strip()
            score = 0
            if label == "total net sales":
                score += 1200
            elif label in ("total revenue", "total revenues"):
                score += 1100
            elif label == "net sales":
                score += 900
            elif label == "revenue":
                score += 200

            if "consolidated statements of operations" in lower:
                score += 600
            if "consolidated statement of operations" in lower:
                score += 600
            if "consolidated statements of income" in lower:
                score += 600
            if "consolidated statement of income" in lower:
                score += 600
            if "year ended" in lower:
                score += 100
            if len(values) >= 3:
                score += 100
            if len(values) == len(row_years):
                score += 150
            if "cost of sales" in lower or "cost of revenue" in lower:
                score += 50
            if "gross profit" in lower:
                score += 50

            source = dict(window.get("source") or {})
            row_label = row.get("label", "").strip()
            for chunk_index in window.get("chunk_indices", []):
                chunk = by_index.get(chunk_index)
                if not chunk:
                    continue
                chunk_text = chunk.get("text", "")
                if re.search(
                    rf"(?i)(?<![\w]){re.escape(row_label)}(?![\w])",
                    chunk_text,
                ):
                    source = dict(chunk)
                    break

            candidates.append({
                "score": score,
                "old_value": values[old_index],
                "new_value": values[new_index],
                "old_year": old_year,
                "new_year": new_year,
                "source": source,
                "years": row_years,
                "values": values,
                "label": row.get("label", ""),
            })

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["score"], reverse=True)
    best = candidates[0]

    print("Selected revenue row:", best["label"])
    print("Selected years:", best["years"])
    print("Selected values:", best["values"])
    print("Selected page:", best["source"].get("page"))

    return best


def _calculate_percentage(
    document_id: str,
    question: str,
):
    """Calculate percentage change using one document-local financial table row."""
    years = _extract_years(question)
    if len(years) < 2:
        return None

    old_year = years[-2]
    new_year = years[-1]

    print()
    print("=" * 70)
    print("DOCUMENT-LOCAL FINANCIAL TABLE CALCULATION")
    print("=" * 70)
    print("Old year:", old_year)
    print("New year:", new_year)

    table = _find_best_revenue_table(
        document_id=document_id,
        old_year=old_year,
        new_year=new_year,
    )

    if not table:
        print("No single reliable financial-statement row found.")
        return None

    percentage = calculate_percentage_change(
        old_value=table["old_value"],
        new_value=table["new_value"],
    )

    return {
        "old_year": old_year,
        "new_year": new_year,
        "old_value": table["old_value"],
        "new_value": table["new_value"],
        "percentage": percentage,
        "old_source": table["source"],
        "new_source": table["source"],
    }


def _find_best_single_revenue_table(
    document_id: str,
    year: int,
) -> dict | None:
    """Find the consolidated total-revenue value for one fiscal year."""
    windows = _percentage_statement_windows(document_id)
    print("Single-year statement windows:", len(windows))

    candidates = []
    all_chunks = _get_all_document_chunks(document_id)
    by_index = {item.get("chunk_index"): item for item in all_chunks}

    for window in windows:
        text = window.get("text", "")
        if not text:
            continue

        lower = text.lower()
        is_income_statement = any(
            phrase in lower
            for phrase in (
                "consolidated statements of income",
                "consolidated statement of income",
                "consolidated income statements",
                "consolidated income statement",
                "consolidated statements of operations",
                "consolidated statement of operations",
            )
        )
        if not is_income_statement:
            continue

        fallback_years = _extract_table_years(text)

        for row in _extract_revenue_rows(text):
            values = row.get("values", [])
            row_years = row.get("years") or fallback_years

            if year not in row_years:
                continue

            year_index = row_years.index(year)
            if year_index >= len(values):
                continue

            label = row.get("label", "").lower().strip()
            score = 0
            if label == "total net sales":
                score += 1500
            elif label in ("total revenue", "total revenues"):
                score += 1400
            elif label == "net sales":
                score += 1100
            elif label == "revenue":
                score += 200

            if "consolidated statements of operations" in lower:
                score += 700
            if "consolidated statement of operations" in lower:
                score += 700
            if "consolidated statements of income" in lower:
                score += 700
            if "consolidated statement of income" in lower:
                score += 700
            if "year ended" in lower:
                score += 100
            if len(values) >= 3:
                score += 100
            if len(values) == len(row_years):
                score += 200
            if "cost of sales" in lower or "cost of revenue" in lower:
                score += 50
            if "gross profit" in lower:
                score += 50

            source = dict(window.get("source") or {})
            row_label = row.get("label", "").strip()
            row_values = row.get("values", [])[:3]

            for chunk_index in window.get("chunk_indices", []):
                chunk = by_index.get(chunk_index)
                if not chunk:
                    continue

                chunk_text = chunk.get("text", "")
                if not re.search(
                    rf"(?i)(?<![\w]){re.escape(row_label)}(?![\w])",
                    chunk_text,
                ):
                    continue

                if any(
                    f"{value:,.0f}" in chunk_text
                    or str(int(value)) in chunk_text
                    for value in row_values
                    if isinstance(value, (int, float))
                ):
                    source = dict(chunk)
                    break

                source = dict(chunk)

            candidates.append({
                "score": score,
                "value": values[year_index],
                "year": year,
                "source": source,
                "years": row_years,
                "values": values,
                "label": row.get("label", ""),
            })

    if not candidates:
        return None

    candidates.sort(key=lambda item: item["score"], reverse=True)
    best = candidates[0]

    print("Selected single-year revenue row:", best["label"])
    print("Selected year:", best["year"])
    print("Selected value:", best["value"])
    print("Selected page:", best["source"].get("page"))

    return best


# ============================================================
# EVIDENCE HELPERS
# ============================================================

def _deduplicate_evidence(
    evidence: list[dict],
) -> list[dict]:

    seen = set()
    result = []

    for item in evidence:

        key = (
            item.get("document_id"),
            item.get("page"),
            item.get("chunk_index"),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def _sort_evidence(
    evidence: list[dict],
) -> list[dict]:

    def distance(item):

        try:
            return float(
                item.get("distance")
            )
        except (
            TypeError,
            ValueError,
        ):
            return 999999.0

    return sorted(
        evidence,
        key=distance,
    )


def _has_relevant_evidence(
    evidence: list[dict],
    threshold: float,
) -> bool:

    for item in evidence:

        try:
            distance = float(
                item.get("distance")
            )

            if distance <= threshold:
                return True

        except (
            TypeError,
            ValueError,
        ):
            continue

    return False


# ============================================================
# SOURCE BUILDERS
# ============================================================

def _document_sources(
    evidence: list[dict],
) -> list[dict]:

    sources = []
    seen = set()

    for item in evidence:

        key = (
            item.get("filename"),
            item.get("page"),
            item.get("chunk_index"),
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "filename": item.get(
                    "filename"
                ),
                "page": item.get(
                    "page"
                ),
                "chunk_index": item.get(
                    "chunk_index"
                ),
                "source": item.get(
                    "source"
                ),
            }
        )

    return sources


def _web_sources(
    evidence: list[dict],
) -> list[dict]:

    sources = []
    seen = set()

    for item in evidence:

        url = item.get(
            "url"
        )

        if not url or url in seen:
            continue

        seen.add(url)

        sources.append(
            {
                "filename": item.get(
                    "title"
                ),
                "page": None,
                "chunk_index": None,
                "source": url,
            }
        )

    return sources


# ============================================================
# CHAT STORAGE
# ============================================================

async def _save_chat_message(
    conversation_id: str,
    document_id: str,
    role: str,
    content: str,
):

    await ChatMessage(
        conversation_id=conversation_id,
        document_id=document_id,
        role=role,
        content=content,
    ).insert()


# ============================================================
# RESEARCH SERVICE
# ============================================================

class ResearchService:

    @staticmethod
    async def ask(
        document_id: str,
        question: str,
        conversation_id: str | None = None,
        chat_history: list[dict] | None = None,
    ):

        # ====================================================
        # 1. VALIDATION
        # ====================================================

        document_id = _clean(
            document_id
        )

        question = _clean(
            question
        )

        if not document_id:

            raise HTTPException(
                status_code=400,
                detail="Document ID is required.",
            )

        if not question:

            raise HTTPException(
                status_code=400,
                detail="Research question is required.",
            )

        # ====================================================
        # 2. DOCUMENT
        # ====================================================

        document = await DocumentModel.find_one(
            DocumentModel.document_id == document_id
        )

        if document is None:

            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        if document.status != "indexed":

            raise HTTPException(
                status_code=422,
                detail="Document is not indexed yet.",
            )

        # ====================================================
        # 3. CONVERSATION
        # ====================================================

        if not conversation_id:

            conversation_id = str(
                uuid.uuid4()
            )

        # ====================================================
        # 4. LOAD CHAT HISTORY
        # ====================================================

        stored_messages = await ChatMessage.find(
            {
                "conversation_id": conversation_id,
                "document_id": document_id,
            }
        ).sort(
            "+created_at"
        ).to_list()

        history = []

        for message in stored_messages:

            history.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        if (
            not history
            and chat_history
        ):

            history = chat_history

        # ====================================================
        # 5. RESOLVE FOLLOW-UP
        # ====================================================

        has_explicit_year = bool(
            re.search(r"\b20\d{2}\b", question)
        )

        if has_explicit_year:
            resolved_question = question
        else:
            resolved_question = (
                _resolve_follow_up_question(
                    question,
                    history,
                )
            )

        print()
        print("=" * 70)
        print("RESEARCH AGENT")
        print("=" * 70)

        print(
            "Document ID:",
            document_id,
        )

        print(
            "Original question:",
            question,
        )

        print(
            "Resolved question:",
            resolved_question,
        )

        # ====================================================
        # 6. CLASSIFY
        # ====================================================

        percentage_question = (
            _is_percentage_question(
                resolved_question
            )
        )

        profile_question = (
            _is_profile_question(
                resolved_question
            )
        )

        financial_question = (
            _is_financial_question(
                resolved_question
            )
        )

        current_question = (
            _requires_current_information(
                resolved_question
            )
        )

        # ====================================================
        # 7. PERCENTAGE QUESTIONS
        # ====================================================

        if percentage_question:

            calculation = _calculate_percentage(
                document_id=document_id,
                question=resolved_question,
            )

            if calculation:

                percentage = calculation[
                    "percentage"
                ]

                old_year = calculation[
                    "old_year"
                ]

                new_year = calculation[
                    "new_year"
                ]

                old_source = calculation[
                    "old_source"
                ]

                new_source = calculation[
                    "new_source"
                ]

                if percentage > 0:

                    answer = (
                        f"The company's total revenue "
                        f"increased by "
                        f"{percentage:.2f}% from "
                        f"{old_year} to {new_year}."
                    )

                elif percentage < 0:

                    answer = (
                        f"The company's total revenue "
                        f"decreased by "
                        f"{abs(percentage):.2f}% from "
                        f"{old_year} to {new_year}."
                    )

                else:

                    answer = (
                        f"The company's total revenue "
                        f"showed no percentage change "
                        f"from {old_year} to {new_year}."
                    )

                old_page = old_source.get(
                    "page"
                )

                new_page = new_source.get(
                    "page"
                )

                if (
                    old_page is not None
                    and new_page is not None
                ):

                    if old_page == new_page:

                        answer += (
                            f" [Page {old_page}]"
                        )

                    else:

                        answer += (
                            f" [Pages {old_page} and "
                            f"{new_page}]"
                        )

                elif old_page is not None:

                    answer += (
                        f" [Page {old_page}]"
                    )

                elif new_page is not None:

                    answer += (
                        f" [Page {new_page}]"
                    )

                # Save chat.
                await _save_chat_message(
                    conversation_id,
                    document_id,
                    "user",
                    question,
                )

                await _save_chat_message(
                    conversation_id,
                    document_id,
                    "assistant",
                    answer,
                )

                return {
                    "document_id": document_id,
                    "question": question,
                    "answer": answer,
                    "conversation_id": conversation_id,
                    "sources": _document_sources(
                        [
                            old_source,
                            new_source,
                        ]
                    ),
                }

            # ------------------------------------------------
            # Percentage calculation failed.
            # ------------------------------------------------

            answer = (
                "I could not find reliable financial "
                "figures for both requested years in "
                "the uploaded document, so I cannot "
                "calculate the percentage change reliably."
            )

            await _save_chat_message(
                conversation_id,
                document_id,
                "user",
                question,
            )

            await _save_chat_message(
                conversation_id,
                document_id,
                "assistant",
                answer,
            )

            return {
                "document_id": document_id,
                "question": question,
                "answer": answer,
                "conversation_id": conversation_id,
                "sources": [],
            }

        # ====================================================
        # 8. PROFILE RETRIEVAL
        # ====================================================

        raw_evidence = []

        if profile_question:

            profile_queries = (
                _build_profile_queries(
                    resolved_question
                )
            )

            print()
            print(
                "Profile retrieval queries:"
            )

            for query in profile_queries:

                print(
                    " -",
                    query,
                )

                try:

                    chunks = (
                        retrieve_relevant_chunks(
                            query=query,
                            document_id=document_id,
                            top_k=PROFILE_TOP_K,
                        )
                    )

                    raw_evidence.extend(
                        chunks
                    )

                except Exception as exc:

                    print(
                        "Profile retrieval failed:",
                        repr(exc),
                    )

            raw_evidence = (
                _deduplicate_evidence(
                    raw_evidence
                )
            )

            raw_evidence = (
                _sort_evidence(
                    raw_evidence
                )
            )

            answer_evidence = (
                _select_profile_evidence(
                    resolved_question,
                    raw_evidence,
                )
            )

            answer_evidence = (
                answer_evidence[
                    :MAX_EVIDENCE
                ]
            )

            relevant = bool(
                answer_evidence
            )

        # ====================================================
        # 9. NORMAL / FINANCIAL RETRIEVAL
        # ====================================================

        else:

            try:

                chunks = (
                    retrieve_relevant_chunks(
                        query=resolved_question,
                        document_id=document_id,
                        top_k=NORMAL_TOP_K,
                    )
                )

                raw_evidence.extend(
                    chunks
                )

            except Exception as exc:

                print(
                    "Document retrieval failed:",
                    repr(exc),
                )

            raw_evidence = (
                _deduplicate_evidence(
                    raw_evidence
                )
            )

            raw_evidence = (
                _sort_evidence(
                    raw_evidence
                )
            )

            # ------------------------------------------------
            # Financial question:
            # try deterministic extraction first.
            # ------------------------------------------------

            if financial_question:

                direct_value = None
                direct_source = None
                direct_year = None
                direct_metric = _get_metric(resolved_question)
                requested_years = _extract_years(resolved_question)

                # For revenue questions, inspect the exact document's
                # consolidated income statement before trusting semantic top-k.
                if direct_metric == "Total revenues" and requested_years:
                    direct_year = requested_years[-1]
                    table = _find_best_single_revenue_table(
                        document_id=document_id,
                        year=direct_year,
                    )
                    if table:
                        direct_value = table["value"]
                        direct_source = table["source"]

                # Existing deterministic extractor remains the fallback for
                # other financial metrics.
                if direct_value is None or direct_source is None:
                    (
                        fallback_value,
                        fallback_source,
                        fallback_year,
                        fallback_metric,
                    ) = _extract_financial_value(
                        resolved_question,
                        raw_evidence,
                    )
                    if direct_value is None:
                        direct_value = fallback_value
                    if direct_source is None:
                        direct_source = fallback_source
                    if direct_year is None:
                        direct_year = fallback_year
                    if direct_metric is None:
                        direct_metric = fallback_metric

                if (
                    direct_value is not None
                    and direct_source is not None
                ):

                    if direct_metric == "Total revenues":

                        answer = (
                            f"The company's total revenue "
                            f"in {direct_year} was "
                            f"${direct_value:,.0f} million "
                            f"(${direct_value / 1000:,.3f} billion)."
                        )

                    else:

                        answer = (
                            f"The company's "
                            f"{direct_metric.lower()} in "
                            f"{direct_year} was "
                            f"${direct_value:,.0f} million."
                        )

                    page = direct_source.get(
                        "page"
                    )

                    if page is not None:

                        answer += (
                            f" [Page {page}]"
                        )

                    await _save_chat_message(
                        conversation_id,
                        document_id,
                        "user",
                        question,
                    )

                    await _save_chat_message(
                        conversation_id,
                        document_id,
                        "assistant",
                        answer,
                    )

                    return {
                        "document_id": document_id,
                        "question": question,
                        "answer": answer,
                        "conversation_id": conversation_id,
                        "sources": _document_sources(
                            [direct_source]
                        ),
                    }

            answer_evidence = (
                raw_evidence[
                    :MAX_EVIDENCE
                ]
            )

            relevant = (
                _has_relevant_evidence(
                    answer_evidence,
                    DOCUMENT_THRESHOLD,
                )
            )

        # ====================================================
        # 10. DEBUG
        # ====================================================

        print()
        print(
            "Raw evidence count:",
            len(raw_evidence),
        )

        print(
            "Validated evidence count:",
            len(answer_evidence),
        )

        print(
            "Relevant:",
            relevant,
        )

        for index, item in enumerate(
            answer_evidence,
            start=1,
        ):

            print()
            print(
                f"Evidence {index}"
            )

            print(
                "Page:",
                item.get("page"),
            )

            print(
                "Distance:",
                item.get("distance"),
            )

            print(
                "Text:",
                item.get(
                    "text",
                    "",
                )[:800],
            )

        # ====================================================
        # 11. PROFILE QUESTION WITH NO DOCUMENT EVIDENCE
        # ====================================================

        if (
            profile_question
            and not relevant
            and not current_question
        ):

            answer = (
                "I could not find reliable information "
                "about this in the uploaded financial document."
            )

            await _save_chat_message(
                conversation_id,
                document_id,
                "user",
                question,
            )

            await _save_chat_message(
                conversation_id,
                document_id,
                "assistant",
                answer,
            )

            return {
                "document_id": document_id,
                "question": question,
                "answer": answer,
                "conversation_id": conversation_id,
                "sources": [],
            }

        # ====================================================
        # 12. WEB SEARCH
        # ====================================================

        web_evidence = []

        should_search_web = (
            current_question
            or (
                not relevant
                and not profile_question
            )
        )

        if should_search_web:

            try:

                web_results = await search_web(
                    query=resolved_question,
                    max_results=MAX_WEB_RESULTS,
                )

                for result in web_results:

                    content = result.get(
                        "content"
                    )

                    if not content:
                        continue

                    web_evidence.append(
                        {
                            "title": result.get(
                                "title"
                            ),
                            "url": result.get(
                                "url"
                            ),
                            "content": content,
                        }
                    )

            except Exception as exc:

                print(
                    "Web search failed:",
                    repr(exc),
                )

        # ====================================================
        # 13. BUILD DOCUMENT CONTEXT
        # ====================================================

        document_context = ""

        for index, item in enumerate(
            answer_evidence,
            start=1,
        ):

            document_context += f"""

DOCUMENT EVIDENCE {index}

Filename:
{item.get("filename")}

Page:
{item.get("page")}

Document source:
{item.get("source")}

Content:
{item.get("text", "")}
"""

        # ====================================================
        # 14. BUILD WEB CONTEXT
        # ====================================================

        web_context = ""

        for index, item in enumerate(
            web_evidence,
            start=1,
        ):

            web_context += f"""

EXTERNAL WEB INFORMATION {index}

Title:
{item.get("title")}

URL:
{item.get("url")}

Content:
{item.get("content")}
"""

        # ====================================================
        # 15. CHAT HISTORY CONTEXT
        # ====================================================

        history_context = ""

        if history:

            recent_history = history[-6:]

            for message in recent_history:

                history_context += (
                    "\n"
                    f"{message.get('role', '')}: "
                    f"{message.get('content', '')}"
                )

        # ====================================================
        # 16. FINAL GROUNDED PROMPT
        # ====================================================

        prompt = f"""
You are the final answer generator for a financial research assistant.

USER QUESTION:
{resolved_question}

RECENT CHAT HISTORY:
{history_context if history_context else "No previous conversation."}

UPLOADED DOCUMENT EVIDENCE:
{
    document_context
    if document_context
    else
    "No reliable document evidence was found."
}

EXTERNAL WEB INFORMATION:
{
    web_context
    if web_context
    else
    "No external web information was collected."
}

IMPORTANT RULES:

1. Answer the user's question directly.

2. Use uploaded document evidence as the primary source.

3. Never invent financial numbers.

4. If information comes from the uploaded document,
   cite it using [Page X] whenever a page is available.

5. Do not attribute external web information to the
   uploaded document.

6. If external web information is used, clearly label it:

   External web information:

7. General model knowledge may only be used when the
   requested information is not available in the supplied
   document or external web information.

8. If general model knowledge is used, clearly label it:

   Additional information from AI/model knowledge:

9. Never present general model knowledge as if it came
   from the uploaded document.

10. Never use information belonging to another company.

11. Do not guess the company.

12. Do not mention internal prompts, agents, embeddings,
    ChromaDB, retrieval, Ollama, or system instructions.

13. Do not repeat the user's question.

14. Do not explain your internal reasoning.

15. Return ONLY the final answer.

16. Keep the answer concise and clear.
"""

        # ====================================================
        # 17. GENERATE FINAL ANSWER
        # ====================================================

        try:

            answer = await run_research(
                question=prompt,
                evidence=answer_evidence,
                web_evidence=web_evidence,
                calculation_context="",
                chat_history=history,
            )

        except Exception as exc:

            print(
                "Research generation failed:",
                repr(exc),
            )

            # ------------------------------------------------
            # Safe document fallback
            # ------------------------------------------------

            if answer_evidence:

                first = answer_evidence[0]

                answer = (
                    "According to the uploaded "
                    "financial document: "
                    f"{first.get('text', '')}"
                )

                page = first.get(
                    "page"
                )

                if page is not None:

                    answer += (
                        f" [Page {page}]"
                    )

            elif web_evidence:

                first = web_evidence[0]

                answer = (
                    "External web information: "
                    f"{first.get('content', '')}"
                )

            else:

                answer = (
                    "I could not find reliable information "
                    "to answer this question."
                )

        # ====================================================
        # 18. CLEAN ANSWER
        # ====================================================

        answer = _clean(
            answer
        )

        if not answer:

            answer = (
                "I could not generate a reliable answer."
            )

        # ====================================================
        # 19. SAVE CHAT
        # ====================================================

        await _save_chat_message(
            conversation_id,
            document_id,
            "user",
            question,
        )

        await _save_chat_message(
            conversation_id,
            document_id,
            "assistant",
            answer,
        )

        # ====================================================
        # 20. SOURCES
        # ====================================================

        sources = []

        sources.extend(
            _document_sources(
                answer_evidence
            )
        )

        sources.extend(
            _web_sources(
                web_evidence
            )
        )

        # ====================================================
        # 21. RESPONSE
        # ====================================================

        return {
            "document_id": document_id,
            "question": question,
            "answer": answer,
            "conversation_id": conversation_id,
            "sources": sources,
        }

    # ========================================================
    # CONVERSATION HISTORY
    # ========================================================

    @staticmethod
    async def get_conversations(
        document_id: str,
    ):
        document_id = _clean(document_id)

        if not document_id:
            raise HTTPException(
                status_code=400,
                detail="Document ID is required.",
            )

        messages = await ChatMessage.find(
            ChatMessage.document_id == document_id
        ).sort(
            "+created_at"
        ).to_list()

        conversations = {}

        for message in messages:
            conversation_id = message.conversation_id

            if conversation_id not in conversations:
                conversations[conversation_id] = {
                    "conversation_id": conversation_id,
                    "document_id": document_id,
                    "messages": [],
                    "created_at": message.created_at,
                    "updated_at": message.created_at,
                }

            conversation = conversations[conversation_id]

            conversation["messages"].append({
                "role": message.role,
                "content": message.content,
                "sources": getattr(message, "sources", []) or [],
                "created_at": message.created_at,
            })

            conversation["updated_at"] = message.created_at

        result = []

        for conversation in conversations.values():
            title = "New Chat"

            for message in conversation["messages"]:
                if message["role"] == "user":
                    title = message["content"].strip()
                    if len(title) > 60:
                        title = title[:60].rstrip() + "..."
                    break

            result.append({
                "conversation_id": conversation["conversation_id"],
                "document_id": conversation["document_id"],
                "title": title,
                "created_at": conversation["created_at"],
                "updated_at": conversation["updated_at"],
            })

        result.sort(
            key=lambda item: item["updated_at"],
            reverse=True,
        )

        return {
            "document_id": document_id,
            "conversations": result,
        }

    @staticmethod
    async def get_conversation_messages(
        conversation_id: str,
        document_id: str,
    ):
        conversation_id = _clean(conversation_id)
        document_id = _clean(document_id)

        if not conversation_id:
            raise HTTPException(
                status_code=400,
                detail="Conversation ID is required.",
            )

        if not document_id:
            raise HTTPException(
                status_code=400,
                detail="Document ID is required.",
            )

        messages = await ChatMessage.find(
            {
                "conversation_id": conversation_id,
                "document_id": document_id,
            }
        ).sort(
            "+created_at"
        ).to_list()

        return {
            "conversation_id": conversation_id,
            "document_id": document_id,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "sources": getattr(message, "sources", []) or [],
                    "created_at": message.created_at,
                }
                for message in messages
            ],
        }

    # ========================================================
    # LEGACY ENDPOINTS
    # ========================================================

    @staticmethod
    def extract(
        document_id: str,
    ):

        raise HTTPException(
            status_code=410,
            detail=(
                "Extraction is handled by the "
                "Extraction Agent."
            ),
        )

    @staticmethod
    def red_flags(
        document_id: str,
    ):

        raise HTTPException(
            status_code=410,
            detail=(
                "Red flag analysis is handled by the "
                "Red Flag Agent."
            ),
        )