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

# FIX: bound the amount of text from any single source that gets pasted
# into the final Ollama prompt. Document chunks are already capped by
# DocumentService.CHUNK_SIZE (1000 chars) at index time, but web search
# results have no such limit -- a single scraped page's "content" field
# can run into the thousands of characters. Left unbounded, 3 web results
# plus 6 document chunks can push the assembled prompt well past a typical
# model context window, which was causing garbled/incoherent answers and
# long stalls on open-ended questions (summaries, predictions, etc.).
MAX_CHUNK_CHARS_IN_PROMPT = 1200
MAX_WEB_CONTENT_CHARS_IN_PROMPT = 800

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


def _truncate_for_prompt(text: str, max_chars: int) -> str:
    """Bound a single piece of context text before it enters the LLM prompt.

    This only affects what is shown to the LLM in the final grounded
    prompt (document_context / web_context). It does not touch retrieval,
    scoring, or any of the deterministic fast-path extraction, which
    continue to operate on the full, untruncated text.
    """
    if not text:
        return text

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + " ...[truncated]"


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


def _extract_report_fiscal_year(
    document: Any,
    document_id: str,
) -> int | None:
    """Resolve the primary fiscal year represented by the uploaded report.

    The report year is document metadata, not the current calendar year.
    Prefer an explicit fiscal-year statement from the indexed document, then
    fall back to filename/title metadata. This prevents a 2025 annual report
    from being answered with live 2026 figures when the user omits a year.
    """
    metadata_values: list[str] = []
    for field in (
        "company_name", "company", "issuer_name", "organization_name",
        "issuer", "name", "title", "filename", "file_name",
        "original_filename",
    ):
        value = getattr(document, field, None)
        if value:
            metadata_values.append(_clean(value))

    # First, use explicit fiscal-year wording from metadata/title when present.
    fiscal_patterns = (
        r"(?i)fiscal\s+year\s+ended[^0-9]{0,40}(20\d{2})",
        r"(?i)year\s+ended[^0-9]{0,40}(20\d{2})",
        r"(?i)(?:annual\s+report|10[- ]?k)[^0-9]{0,20}(20\d{2})",
    )
    for value in metadata_values:
        for pattern in fiscal_patterns:
            match = re.search(pattern, value)
            if match:
                return int(match.group(1))

    # The most authoritative fallback is the actual report text. Only inspect
    # the first portion of the document so this remains cheap.
    chunks = _get_all_document_chunks(document_id)
    for item in chunks[:60]:
        text = item.get("text", "") or ""
        if not text:
            continue
        for pattern in fiscal_patterns[:2]:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

    # Finally, filenames such as Amazon-2025-Annual-Report.pdf. Prefer a year
    # adjacent to annual-report/10-K rather than an arbitrary filing year.
    for value in metadata_values:
        match = re.search(
            r"(?i)(20\d{2})(?=[-_ ]*(?:annual[-_ ]?report|10[-_ ]?k|form[-_ ]?10[-_ ]?k))",
            value,
        )
        if match:
            return int(match.group(1))
        years = re.findall(r"\b20\d{2}\b", value)
        if years:
            return int(years[-1])

    return None


def _apply_report_year_defaults(
    question: str,
    report_year: int | None,
) -> str:
    """Apply the report fiscal year when a financial year is not specified.

    Explicit years always win. Explicit current-time requests such as
    'this year'/'current year' are also left untouched so they can use the
    current-information path. Generic financial questions default to the
    uploaded report's primary fiscal year.
    """
    if not question or not report_year or _extract_years(question):
        return question

    text = question.lower()

    current_markers = (
        "this year",
        "current year",
        "current fiscal year",
        "today",
        "today's",
        "right now",
    )
    if any(marker in text for marker in current_markers):
        return question

    # Relative next-year wording is intentional. Do not replace it with the
    # report year: "how can we increase revenue next year?" is a forward-looking
    # recommendation question, not a request for the report year's performance.
    next_markers = (
        "next year",
        "following year",
        "next fiscal year",
    )
    if any(marker in text for marker in next_markers):
        return question

    # If the user explicitly asks for a relative previous/prior/last year
    # without history, interpret it relative to the uploaded report year.
    previous_markers = (
        "previous year",
        "prior year",
        "last year",
        "preceding year",
        "previous fiscal year",
        "prior fiscal year",
        "last fiscal year",
    )
    if any(marker in text for marker in previous_markers):
        return f"{question} (use fiscal year {report_year - 1})"

    # Generic financial questions should stay tied to the uploaded report.
    return f"{question} (use fiscal year {report_year})"


def _apply_percentage_year_defaults(
    question: str,
    report_year: int | None,
) -> str:
    """Default an unqualified percentage-change question to report vs prior year."""
    if not question or not report_year or _extract_years(question):
        return question
    text = question.lower()
    if any(marker in text for marker in ("this year", "current year", "current fiscal year")):
        return question
    return f"{question} (calculate from fiscal year {report_year - 1} to fiscal year {report_year})"


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


def _is_context_dependent_question(question: str) -> bool:
    """Return True only when the current question genuinely needs prior context.

    A normal new question must stay isolated from earlier turns. This is
    especially important for questions such as "how can we increase revenue"
    where the previous turn may have been a revenue question but the current
    intent is recommendation/analysis rather than another fact lookup.
    """
    if not question:
        return False

    text = _clean(question).lower()

    explicit_context_phrases = (
        "what about",
        "how about",
        "and what about",
        "and how about",
        "what was that",
        "what was it",
        "why did it",
        "why was it",
        "why is it",
        "how did it",
        "how was it",
        "compare that",
        "compared with that",
        "the previous year",
        "the prior year",
        "the last year",
        "that year",
        "same metric",
        "same period",
    )

    if any(phrase in text for phrase in explicit_context_phrases):
        return True

    # Short elliptical follow-ups such as "and in 2024?" or "and next year?"
    # need history. Full standalone questions do not.
    if re.fullmatch(
        r"(?:and\s+)?(?:in\s+)?(?:20\d{2}|next year|following year|previous year|prior year|last year)\s*[?!.]*",
        text,
    ):
        return True

    if len(text.split()) <= 6 and text.startswith((
        "and ",
        "what about ",
        "how about ",
        "why ",
    )):
        return True

    return False


# ============================================================
# FOLLOW-UP QUESTION HANDLING
# ============================================================

def _resolve_follow_up_question(
    question: str,
    history: list[dict],
) -> str:

    if not history:
        return question

    # IMPORTANT: Only resolve relative years when the current question is
    # genuinely dependent on the previous turn. A standalone question such as
    # "how can we increase revenue by next year?" must never be rewritten
    # from the previous question because doing so changes its intent.
    if not _is_context_dependent_question(question):
        return question

    previous = _get_last_user_question(history)

    if not previous:
        return question

    text = question.lower()

    previous_year_phrases = (
        "previous year",
        "prior year",
        "last year",
        "preceding year",
        "previous fiscal year",
        "prior fiscal year",
        "last fiscal year",
    )

    if any(phrase in text for phrase in previous_year_phrases):
        previous_years = _extract_years(previous)

        if previous_years:
            target_year = previous_years[-1] - 1
            return re.sub(
                r"\b20\d{2}\b",
                str(target_year),
                previous,
                count=1,
            )

    next_year_phrases = (
        "next year",
        "following year",
        "next fiscal year",
    )

    if any(phrase in text for phrase in next_year_phrases):
        previous_years = _extract_years(previous)

        if previous_years:
            target_year = previous_years[-1] + 1
            return re.sub(
                r"\b20\d{2}\b",
                str(target_year),
                previous,
                count=1,
            )

    # Generic follow-ups remain unchanged. The previous conversation is made
    # available separately to the final prompt only when this helper classified
    # the current question as context-dependent.
    return question


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

def _company_identity_candidates(document: Any, document_id: str) -> list[str]:
    """Collect company identifiers, preferring legal issuer identity over filenames."""
    candidates: list[str] = []

    # Explicit metadata has highest priority.
    for field in (
        "company_name",
        "issuer_name",
        "organization_name",
        "company",
        "issuer",
    ):
        value = getattr(document, field, None)
        if value:
            candidates.append(_clean(value))

    # Inspect the beginning of the indexed report for the legal registrant.
    chunks = _get_all_document_chunks(document_id)
    for item in chunks[:60]:
        text = item.get("text", "") or ""
        if not text:
            continue
        patterns = (
            r"(?i)exact\s+name\s+of\s+registrant[^\n:]*[:\-]\s*([^\n]+)",
            r"(?i)registrant\s+name[^\n:]*[:\-]\s*([^\n]+)",
            r"(?im)^\s*([A-Z][A-Z0-9.&' -]{2,80}?(?:,?\s+(?:INC\.?|CORP\.?|CORPORATION|PLC|LTD\.?|LIMITED)))\s*$",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidates.append(re.sub(r"\s+", " ", match.group(1)).strip(" .,:;-_"))

    # Filename/title is a lower-priority fallback.
    for field in ("name", "title", "filename", "file_name", "original_filename"):
        value = getattr(document, field, None)
        if value:
            candidates.append(_clean(value))
    if document_id:
        candidates.append(_clean(document_id))

    cleaned: list[str] = []
    for value in candidates:
        value = re.sub(r"\.(pdf|txt|docx?|xlsx?)$", "", value, flags=re.I)
        # Strip upload prefixes/IDs and report descriptors.
        value = re.sub(r"^[A-Fa-f0-9]{8,}[-_ ]+", "", value)
        value = re.sub(
            r"[-_ ]?(?:19|20)\d{2}[-_ ]?(?:annual[-_ ]?report|10[-_ ]?k|form[-_ ]?10[-_ ]?k).*?$",
            "", value, flags=re.I,
        )
        value = re.sub(r"[-_]+", " ", value)
        value = re.sub(r"\s+", " ", value).strip(" -_")
        if value:
            cleaned.append(value)

    # Normalize obvious legal forms and prefer a short issuer name.
    normalized: list[str] = []
    for value in cleaned:
        value = re.sub(r"\s+", " ", value).strip()
        if value.lower() in {"document", "annual report", "10 k", "form 10 k"}:
            continue
        normalized.append(value)

    return list(dict.fromkeys(normalized))


def _extract_company_name_from_document(
    document: Any,
    document_id: str,
) -> str | None:
    """Resolve the active company from the uploaded document, not generic web popularity."""
    candidates = _company_identity_candidates(document, document_id)

    # Strong known issuer patterns.
    for candidate in candidates:
        normalized = candidate.lower()
        if "amazon.com" in normalized or normalized.startswith("amazon"):
            return "Amazon"
        if "alphabet" in normalized or normalized.startswith("google"):
            return "Google"
        if "apple" in normalized:
            return "Apple"
        if "microsoft" in normalized:
            return "Microsoft"
        if "meta platforms" in normalized or normalized.startswith("meta"):
            return "Meta"
        if "tesla" in normalized:
            return "Tesla"
        if "nvidia" in normalized:
            return "NVIDIA"

    # Legal issuer line is usually already a usable company name.
    for candidate in candidates:
        if re.search(r"(?i)\b(?:inc|inc\.|corp|corporation|plc|ltd|limited)\b", candidate):
            return candidate

    # Filename fallback, e.g. Amazon-2025-Annual-Report.
    for candidate in candidates:
        if len(candidate.split()) <= 8 and not re.fullmatch(r"[A-Fa-f0-9]{8,}", candidate):
            return candidate

    return None

def _company_search_query(
    question: str,
    company_name: str | None,
) -> str:
    """Make profile web searches explicitly company-scoped."""
    if not company_name:
        return question

    text = question.strip()
    # Replace vague references so the search engine cannot choose another
    # company merely because it is more prominent for the wording.
    text = re.sub(
        r"\b(the company|this company|the organization|this organization)\b",
        company_name,
        text,
        flags=re.I,
    )

    if company_name.lower() not in text.lower():
        return f"{company_name}: {text}"
    return text


def _web_result_matches_company(
    result: dict,
    company_name: str | None,
) -> bool:
    """Reject external results that are clearly about another company."""
    if not company_name:
        return False

    target = re.sub(r"[^a-z0-9]+", " ", company_name.lower()).strip()
    target_tokens = [
        token for token in target.split()
        if token not in {
            "inc", "incorporated", "corp", "corporation", "plc",
            "ltd", "limited", "company", "com", "the",
        }
    ]
    if not target_tokens:
        return False

    haystack = " ".join(
        str(result.get(key, "") or "")
        for key in ("title", "content", "url")
    ).lower()
    haystack = re.sub(r"[^a-z0-9]+", " ", haystack)

    # Common legal/brand aliases. This is deliberately conservative: a result
    # must contain the active company's meaningful brand token.
    aliases = {
        "amazon": ("amazon", "amazon com"),
        "google": ("google", "alphabet"),
        "alphabet": ("alphabet", "google"),
        "meta": ("meta", "facebook", "meta platforms"),
        "microsoft": ("microsoft",),
        "apple": ("apple",),
        "tesla": ("tesla",),
        "nvidia": ("nvidia",),
    }

    meaningful = target_tokens[0]
    if meaningful in aliases:
        return any(alias in haystack for alias in aliases[meaningful])

    # Unknown multi-word companies must match every meaningful token.
    return all(token in haystack for token in target_tokens)

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

    if (
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

    if (
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

    if (
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

def _fast_extract_employee_fact(
    document_id: str,
    requested_year: int | None = None,
    report_year: int | None = None,
) -> tuple[int | None, dict | None, int | None]:
    """Extract the reported employee headcount from the uploaded document.

    This deliberately prefers an exact human-capital disclosure over semantic
    matches or current web numbers.  If no year is requested, the report's
    fiscal year is used.  A different year is returned only when that year is
    explicitly present in the document text.
    """
    target_year = requested_year or report_year
    if not target_year:
        return None, None, None

    chunks = _get_all_document_chunks(document_id)
    candidates = []
    for item in chunks:
        text = item.get("text", "") or ""
        if not text or not re.search(r"(?i)\b(?:employees|workforce|personnel)\b", text):
            continue

        patterns = [
            # Amazon-style: As of December 31, 2025, we employed approximately 1,576,000...
            rf"(?is)as\s+of\s+(?:december|january|february|march|april|may|june|july|august|september|october|november)\s+\d{{1,2}},?\s+{target_year}\D{{0,100}}?(?:employed|employees|workforce)\D{{0,80}}?(\d{{1,3}}(?:,\d{{3}})+|\d+)\b",
            # Generic: approximately 1,576,000 full-time and part-time employees as of ... 2025
            rf"(?is)(\d{{1,3}}(?:,\d{{3}})+|\d+)\s+(?:full[- ]time\s+and\s+part[- ]time\s+)?employees\D{{0,100}}?{target_year}\b",
            # Generic year-near-headcount disclosure.
            rf"(?is){target_year}\D{{0,80}}?(\d{{1,3}}(?:,\d{{3}})+|\d+)\s+employees\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            raw = match.group(1).replace(",", "")
            try:
                value = int(raw)
            except ValueError:
                continue
            # Reject implausibly small values and dates.
            if value < 1000 or value > 10000000:
                continue
            source = dict(item)
            source["text"] = text
            candidates.append((value, source))
            break

    if not candidates:
        return None, None, target_year

    # Prefer exact report-year disclosure and human-capital language.
    value, source = candidates[0]
    return value, source, target_year


def _fast_extract_founder_fact(
    document_id: str,
    company_name: str | None = None,
) -> tuple[str | None, dict | None]:
    """Extract founder names from explicit founding statements in the report."""
    chunks = _get_all_document_chunks(document_id)
    company = re.escape(company_name or "")
    patterns = []
    if company:
        patterns.extend([
            rf"(?is)([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){{1,4}})\s+(?:and\s+([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){{1,4}})\s+)?(?:co-)?founded\s+(?:{company}|the\s+company)",
            rf"(?is)([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){{1,4}})\.[\s\S]{{0,80}}?(?:Mr\.|Ms\.)?\s*[A-Z][A-Za-z.]+\s+founded\s+(?:{company}|the\s+company)",
        ])
    patterns.append(r"(?is)([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){1,4})\s+(?:and\s+([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){1,4})\s+)?(?:co-)?founded\s+(?:the\s+company|the\s+organization)")

    for item in chunks:
        text = item.get("text", "") or ""
        if not re.search(r"(?i)\bfound(?:ed|er|ers|ing)\b", text):
            continue
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            names = [g.strip(" .") for g in match.groups() if g and len(g.strip()) > 2]
            if names:
                return " and ".join(dict.fromkeys(names)), dict(item)
    return None, None


def _profile_content_matches(
    question: str,
    text: str,
) -> bool:
    if not text:
        return False

    normalized = re.sub(r"\s+", " ", text.lower())
    question_text = question.lower()

    checks = []
    if any(x in question_text for x in ("headquarters", "headquartered", "head office", "principal executive office")):
        checks.append(("headquarters", ("headquartered", "headquarters", "head office", "principal executive office", "principal office", "corporate headquarters")))
    if any(x in question_text for x in ("founder", "founded", "founding")):
        checks.append(("founder", ("founded", "founder", "founders", "co-founded", "cofounder", "established", "formed", "incorporated")))
    if any(x in question_text for x in ("ceo", "chief executive")):
        checks.append(("ceo", ("chief executive officer", "chief executive", "ceo")))
    if any(x in question_text for x in ("employee", "workforce", "headcount", "staff")):
        checks.append(("employees", ("employees", "employee", "workforce", "headcount", "personnel", "people employed")))
    if any(x in question_text for x in ("management", "leadership", "executive")):
        checks.append(("management", ("management", "executive officer", "executive officers", "leadership", "senior management")))
    if any(x in question_text for x in ("business", "business model", "what does the company do")):
        checks.append(("business", ("our business", "the company's business", "principal business", "business operations", "business activities", "products and services")))

    return any(any(pattern in normalized for pattern in patterns) for _, patterns in checks)


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
# HISTORICAL DOWNTURN / CHALLENGE QUESTION DETECTION
# ============================================================

def _is_downturn_question(question: str) -> bool:
    """Detect broad historical questions asking for negative performance or challenges."""
    text = re.sub(r"\s+", " ", (question or "").lower()).strip()

    terms = (
        "downfall",
        "downturn",
        "decline",
        "declined",
        "decrease",
        "decreased",
        "drop",
        "dropped",
        "fall",
        "fell",
        "negative performance",
        "poor performance",
        "challenges",
        "challenge",
        "difficulties",
        "difficulty",
        "setbacks",
        "setback",
        "problems faced",
        "issues faced",
        "adverse",
        "headwinds",
        "weakness",
        "weaknesses",
        "risks faced",
        "risks in",
        "what went wrong",
        "what went poorly",
    )

    return any(term in text for term in terms)


def _build_downturn_queries(
    question: str,
    report_year: int | None,
) -> list[str]:
    """Build a few report-oriented semantic queries for broad negative-performance questions."""
    year_text = str(report_year) if report_year else "2025"

    queries = [
        f"{year_text} financial performance decline decreases compared with prior year",
        f"{year_text} management discussion challenges risks uncertainties adverse factors",
        f"{year_text} revenue profit deliveries sales gross margin decreases and reasons",
    ]

    # Keep the user's wording as one query too, because it may contain a
    # company-specific term that is more useful than our generic expansions.
    if question and question.strip():
        queries.insert(0, question.strip())

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(queries))[:4]


# ============================================================
# FINANCIAL METRIC
# ============================================================

def _get_metric(
    question: str,
) -> str | None:

    text = question.lower()

    # EPS is checked before generic "earnings" so phrases such as
    # "earnings per share" are never classified as net income.
    if (
        "diluted eps" in text
        or "diluted earnings per share" in text
    ):
        return "Diluted EPS"

    if (
        "basic eps" in text
        or "basic earnings per share" in text
    ):
        return "Basic EPS"

    # Revenue / sales aliases.  "Annual income" is a common business
    # wording for annual/top-line income; it is treated as revenue only
    # when it is not explicitly qualified as net/profit income.
    if (
        "total revenue" in text
        or "total revenues" in text
        or "revenue" in text
        or "revenues" in text
        or "net sales" in text
        or "annual sales" in text
        or "yearly sales" in text
        or "sales revenue" in text
        or "annual income" in text
        or "yearly income" in text
        or "annual turnover" in text
        or "turnover" in text
        or "top line" in text
    ):
        return "Total revenues"

    if (
        "net income" in text
        or "net profit" in text
        or "net earnings" in text
        or re.search(r"\bearnings\b", text)
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

    if (
        "total assets" in text
        or "assets" in text and "total" in text
    ):
        return "Total assets"

    if (
        "total liabilities" in text
        or "liabilities" in text and "total" in text
    ):
        return "Total liabilities"

    if (
        "cash and cash equivalents" in text
        or "cash & cash equivalents" in text
        or "cash equivalents" in text
    ):
        return "Cash and cash equivalents"

    if (
        "operating cash flow" in text
        or "cash flow from operations" in text
        or "net cash provided by operating activities" in text
    ):
        return "Operating cash flow"

    if (
        "free cash flow" in text
    ):
        return "Free cash flow"

    if "operating expenses" in text or "operating expense" in text:
        return "Operating expenses"

    if "cost of revenue" in text or "cost of sales" in text:
        return "Cost of revenue"

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
# FAST DOCUMENT-LOCAL FINANCIAL EXTRACTION
# ============================================================

_FINANCIAL_STATEMENT_HINTS = {
    "Total revenues": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated income statement",
        "year ended",
        "net sales",
        "total revenues",
        "sales revenue",
        "turnover",
    ),
    "Net income": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "net income",
        "net earnings",
    ),
    "Gross profit": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "gross profit",
    ),
    "Income from operations": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "income from operations",
        "operating income",
    ),
    "Total assets": (
        "consolidated balance sheets",
        "consolidated balance sheet",
        "total assets",
    ),
    "Total liabilities": (
        "consolidated balance sheets",
        "consolidated balance sheet",
        "total liabilities",
    ),
    "Cash and cash equivalents": (
        "consolidated balance sheets",
        "consolidated balance sheet",
        "cash and cash equivalents",
    ),
    "Operating cash flow": (
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "cash flows from operating activities",
        "operating activities",
    ),
    "Diluted EPS": (
        "consolidated statements of income",
        "consolidated statement of income",
        "earnings per share",
        "diluted earnings per share",
    ),
    "Basic EPS": (
        "consolidated statements of income",
        "consolidated statement of income",
        "earnings per share",
        "basic earnings per share",
    ),
    "Operating expenses": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "operating expenses",
    ),
    "Cost of revenue": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "cost of sales",
        "cost of revenue",
    ),
}


def _is_direct_financial_fact(question: str) -> bool:
    """True for questions that can be answered from one document fact."""
    if not question or not _get_metric(question):
        return False

    # By the time this helper runs, unqualified financial questions have been
    # resolved to the uploaded report fiscal year. Explicit years are already
    # present too. Current-time questions intentionally remain on the live/web
    # path instead of being forced into the report.
    lower = question.lower()
    if not _extract_years(question):
        return False
    complex_markers = (
        "why ", "why did", "explain", "reason", "trend", "compare",
        "comparison", "increase by", "decrease by", "growth", "margin",
        "ratio", "forecast", "predict", "outlook", "how did",
    )
    return not any(marker in lower for marker in complex_markers)


def _financial_metric_aliases(metric: str) -> tuple[str, ...]:
    return {
        "Total revenues": (
            "total revenue", "total revenues", "revenue", "revenues",
            "net sales", "annual sales", "sales revenue", "turnover",
        ),
        "Net income": ("net income", "net profit", "net earnings", "earnings"),
        "Gross profit": ("gross profit",),
        "Income from operations": ("income from operations", "operating income", "operating profit"),
        "Total assets": ("total assets",),
        "Total liabilities": ("total liabilities",),
        "Cash and cash equivalents": ("cash and cash equivalents", "cash equivalents"),
        "Operating cash flow": ("cash flows from operating activities", "operating cash flow", "net cash provided by operating activities"),
        "Free cash flow": ("free cash flow",),
        "Diluted EPS": ("diluted earnings per share", "diluted eps"),
        "Basic EPS": ("basic earnings per share", "basic eps"),
        "Operating expenses": ("operating expenses", "operating expense"),
        "Cost of revenue": ("cost of sales", "cost of revenue"),
    }.get(metric, (metric.lower(),))



# ============================================================
# ROBUST BALANCE-SHEET ROW / DERIVED METRIC EXTRACTION
# ============================================================

_BALANCE_SHEET_ROW_ALIASES = {
    "Total assets": (
        "total assets",
    ),
    "Total stockholders equity": (
        "total stockholders’ equity",
        "total stockholders' equity",
        "total shareholders’ equity",
        "total shareholders' equity",
        "total equity",
    ),
    "Total current liabilities": (
        "total current liabilities",
    ),
    "Long-term lease liabilities": (
        "long-term lease liabilities",
    ),
    "Long-term debt": (
        "long-term debt",
    ),
    "Other long-term liabilities": (
        "other long-term liabilities",
    ),
}


def _normalize_statement_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\u00a0", " ")).strip()


def _year_order_near_position(text: str, position: int) -> list[int]:
    """Find the nearest plausible annual column ordering before a row."""
    before = text[max(0, position - 1800):position]
    years = [int(y) for y in re.findall(r"\b20\d{2}\b", before)]
    # Prefer the last consecutive 2/3-year sequence.
    for size in (3, 2):
        for i in range(len(years) - size, -1, -1):
            seq = years[i:i + size]
            if len(set(seq)) != size:
                continue
            if all(abs(seq[j + 1] - seq[j]) == 1 for j in range(size - 1)):
                return seq
    unique = list(dict.fromkeys(years))
    return unique[-3:]


def _extract_labeled_balance_sheet_value(
    chunks: list[dict],
    label_aliases: tuple[str, ...],
    year: int,
) -> tuple[float | None, dict | None]:
    """Extract a value from an exact balance-sheet row.

    Unlike the generic calculator, this requires the requested label itself to
    be adjacent to the candidate numbers. This prevents narrative values such
    as Amazon's $87.339B long-term lease liability from being mistaken for
    total liabilities.
    """
    candidates = []

    label_pattern = "|".join(re.escape(x) for x in label_aliases)
    label_re = re.compile(
        rf"(?i)(?<![\w])(?:{label_pattern})(?![\w])"
    )

    for item in chunks:
        raw = item.get("text", "") or ""
        if not raw:
            continue
        text = _normalize_statement_text(raw)
        lower = text.lower()

        # Only consider actual balance-sheet contexts.
        if not any(
            marker in lower
            for marker in (
                "consolidated balance sheets",
                "consolidated balance sheet",
                "liabilities and stockholders",
                "assets",
            )
        ):
            continue

        for match in label_re.finditer(text):
            # Numbers immediately following the row label are the safest
            # representation after PDF/table flattening.
            tail = text[match.end():match.end() + 220]
            numbers = _number_matches(tail)
            if not numbers:
                continue

            values = [value for _, _, value in numbers[:5]]
            year_order = _year_order_near_position(text, match.start())

            # Most annual balance sheets contain exactly two year columns.
            # If the header order is known, map by that order; otherwise use
            # the common left-to-right ordering of the extracted row.
            value = None
            if year in year_order:
                idx = year_order.index(year)
                if idx < len(values):
                    value = values[idx]
            if value is None and len(values) >= 2:
                # For two-column statements, requested latest year normally
                # corresponds to the final value; older year to the first.
                if year_order and year_order[-1] == year:
                    value = values[-1]
                elif year_order and year_order[0] == year:
                    value = values[0]

            if value is None:
                continue

            score = 0
            if re.search(r"(?i)consolidated\s+balance\s+sheets?", text):
                score += 500
            if "liabilities and stockholders" in lower:
                score += 200
            if year in year_order:
                score += 300
            if len(values) >= 2:
                score += 100
            # Penalize obvious narrative prose after a label.
            if any(token in tail.lower() for token in ("million", "billion")):
                score += 10

            candidates.append((score, item, value))

    if not candidates:
        return None, None

    candidates.sort(
        key=lambda x: (x[0], -(x[1].get("page") or 10**9)),
        reverse=True,
    )
    _, source, value = candidates[0]
    return float(value), source


def _fast_extract_total_liabilities(
    chunks: list[dict],
    year: int,
) -> tuple[float | None, dict | None]:
    """Extract total liabilities without trusting unrelated liability values.

    Many issuers do not print a literal `Total liabilities` row. In that case,
    total liabilities can be derived from the balance sheet identity:

        Total liabilities = Total assets - Total stockholders' equity

    A component-sum fallback is used when equity is not available.
    """
    assets, asset_source = _extract_labeled_balance_sheet_value(
        chunks,
        _BALANCE_SHEET_ROW_ALIASES["Total assets"],
        year,
    )
    equity, equity_source = _extract_labeled_balance_sheet_value(
        chunks,
        _BALANCE_SHEET_ROW_ALIASES["Total stockholders equity"],
        year,
    )

    if assets is not None and equity is not None:
        # Use the stronger source when available, but retain the balance-sheet
        # source for citation. The value itself is independently derived.
        source = asset_source or equity_source
        derived = assets - equity
        if derived >= 0:
            return derived, source

    # Fallback for statements that omit total equity but list liability rows.
    current, current_source = _extract_labeled_balance_sheet_value(
        chunks,
        _BALANCE_SHEET_ROW_ALIASES["Total current liabilities"],
        year,
    )
    lease, lease_source = _extract_labeled_balance_sheet_value(
        chunks,
        _BALANCE_SHEET_ROW_ALIASES["Long-term lease liabilities"],
        year,
    )
    debt, debt_source = _extract_labeled_balance_sheet_value(
        chunks,
        _BALANCE_SHEET_ROW_ALIASES["Long-term debt"],
        year,
    )
    other, other_source = _extract_labeled_balance_sheet_value(
        chunks,
        _BALANCE_SHEET_ROW_ALIASES["Other long-term liabilities"],
        year,
    )

    components = [x for x in (current, lease, debt, other) if x is not None]
    if len(components) >= 2:
        sources = [x for x in (current_source, lease_source, debt_source, other_source) if x]
        return sum(components), (sources[0] if sources else None)

    return None, None


def _fast_extract_financial_fact(
    question: str,
    document_id: str,
) -> tuple[float | None, dict | None, int | None, str | None]:
    """Extract a single financial fact directly from the document.

    This deliberately bypasses semantic top-k retrieval for simple fact questions.
    It avoids the failure mode where a nearby but unrelated number wins semantic
    ranking (for example an $11M figure being returned for Amazon revenue).
    """
    metric = _get_metric(question)
    years = _extract_years(question)
    if not metric or not years:
        return None, None, None, None

    year = years[-1]
    chunks = _get_all_document_chunks(document_id)

    # Total liabilities is often NOT printed as a literal row. For example,
    # Amazon's balance sheet lists total current liabilities and long-term
    # liability components, then total stockholders' equity. Derive total
    # liabilities from the balance-sheet identity instead of allowing a
    # nearby liability number to be selected.
    if metric == "Total liabilities" and chunks:
        value, source = _fast_extract_total_liabilities(chunks, year)
        if value is not None and source is not None:
            return value, source, year, metric
    if not chunks:
        return None, None, year, metric

    aliases = _financial_metric_aliases(metric)
    hints = _FINANCIAL_STATEMENT_HINTS.get(metric, ())
    candidates = []

    for item in chunks:
        text = item.get("text", "") or ""
        lower = text.lower()
        if not text or not any(alias in lower for alias in aliases):
            continue

        try:
            value = extract_metric_value(text=text, metric=metric, year=year)
        except Exception:
            continue
        if value is None:
            continue

        score = 0
        for alias in aliases:
            if re.search(rf"(?<![\\w]){re.escape(alias)}(?![\\w])", lower):
                score += 80 if alias in ("total revenue", "total revenues", "net income", "total assets", "total liabilities") else 45
                break
        for hint in hints:
            if hint in lower:
                score += 70
        if "year ended" in lower:
            score += 40
        if re.search(rf"\\b{year}\\b", text):
            score += 40

        # Prefer chunks where the metric and statement context occur together.
        if any(hint in lower for hint in hints):
            score += 100

        candidates.append((score, item, float(value)))

    if not candidates:
        return None, None, year, metric

    candidates.sort(
        key=lambda candidate: (
            candidate[0],
            -(candidate[1].get("page") or 10**9),
        ),
        reverse=True,
    )
    _, source, value = candidates[0]
    return value, source, year, metric


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

        context_dependent_question = (
            _is_context_dependent_question(question)
        )

        if has_explicit_year or not context_dependent_question:
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

        # Resolve the uploaded report's fiscal year before classification.
        # Generic financial questions must use the report year, not the live
        # calendar year. Explicit years remain untouched.
        report_year = _extract_report_fiscal_year(
            document,
            document_id,
        )

        if report_year:
            print("Detected report fiscal year:", report_year)

        company_name = _extract_company_name_from_document(document, document_id)
        print("Detected active company:", company_name)

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

        # Unqualified financial questions are anchored to the uploaded report's
        # primary fiscal year. Percentage questions default to report year vs
        # prior fiscal year.
        if percentage_question and report_year and not _extract_years(resolved_question):
            resolved_question = _apply_percentage_year_defaults(
                resolved_question,
                report_year,
            )
            print("Report-year percentage resolution:", resolved_question)
        elif (
            financial_question
            and report_year
            and not _extract_years(resolved_question)
            and not any(
                marker in resolved_question.lower()
                for marker in (
                    "next year",
                    "following year",
                    "next fiscal year",
                )
            )
        ):
            resolved_question = _apply_report_year_defaults(
                resolved_question,
                report_year,
            )
            print("Report-year financial resolution:", resolved_question)

        # Recompute classifications after the resolution text is enriched.
        percentage_question = _is_percentage_question(resolved_question)
        financial_question = _is_financial_question(resolved_question)
        current_question = _requires_current_information(resolved_question)

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
        founder_value = None
        founder_source = None
        employee_value = None
        employee_source = None
        employee_fact_year = None

        if profile_question:
            profile_text = resolved_question.lower()
            employee_requested_years = _extract_years(resolved_question)
            employee_year = employee_requested_years[-1] if employee_requested_years else report_year

            if any(term in profile_text for term in ("employee", "workforce", "headcount", "staff")):
                employee_value, employee_source, employee_fact_year = _fast_extract_employee_fact(
                    document_id=document_id,
                    requested_year=employee_year,
                    report_year=report_year,
                )
                if employee_source is not None:
                    employee_source = dict(employee_source)
                    employee_source["distance"] = 0.0
                    raw_evidence.append(employee_source)

            if any(term in profile_text for term in ("founder", "founded", "founding")):
                founder_value, founder_source = _fast_extract_founder_fact(
                    document_id=document_id,
                    company_name=company_name,
                )
                if founder_source is not None:
                    founder_source = dict(founder_source)
                    founder_source["distance"] = 0.0
                    raw_evidence.append(founder_source)

            # Fast profile path: if the uploaded report already contains every
            # requested founder/employee fact, answer directly. This avoids
            # dozens of semantic retrieval calls, web search, and an LLM call
            # for simple factual questions.
            asks_founder = any(
                term in profile_text
                for term in ("founder", "founded", "founding")
            )
            asks_employee = any(
                term in profile_text
                for term in ("employee", "workforce", "headcount", "staff")
            )
            asks_other_profile = any(
                term in profile_text
                for term in (
                    "ceo",
                    "chief executive",
                    "headquarters",
                    "head office",
                    "management",
                    "leadership",
                )
            )

            requested_profile_facts_available = (
                (not asks_founder or founder_value)
                and (not asks_employee or employee_value is not None)
                and not asks_other_profile
            )

            if requested_profile_facts_available and (asks_founder or asks_employee):
                parts = []

                if founder_value:
                    parts.append(
                        f"{founder_value} is the founder of "
                        f"{company_name or 'the company'}."
                    )

                if employee_value is not None:
                    employee_part = (
                        f"The company had approximately {employee_value:,} "
                        f"full-time and part-time employees"
                    )
                    if employee_fact_year:
                        employee_part += f" in {employee_fact_year}"
                    employee_part += "."
                    parts.append(employee_part)

                answer = " ".join(parts)

                pages = []
                for source in (founder_source, employee_source):
                    if source and source.get("page") is not None:
                        pages.append(source.get("page"))

                pages = list(dict.fromkeys(pages))
                if pages:
                    if len(pages) == 1:
                        answer += f" [Page {pages[0]}]"
                    else:
                        answer += (
                            " [Pages "
                            + " and ".join(str(page) for page in pages)
                            + "]"
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
                        [source for source in (founder_source, employee_source) if source]
                    ),
                }

            # A direct employee-only question can be answered immediately from
            # the report, avoiding stale/current web data and an unnecessary LLM call.
            if (
                employee_value is not None
                and not asks_founder
                and not asks_other_profile
            ):
                answer = (
                    f"The company had approximately {employee_value:,} full-time and part-time employees"
                    f" in {employee_fact_year}."
                )
                page = employee_source.get("page") if employee_source else None
                if page is not None:
                    answer += f" [Page {page}]"
                await _save_chat_message(conversation_id, document_id, "user", question)
                await _save_chat_message(conversation_id, document_id, "assistant", answer)
                return {
                    "document_id": document_id,
                    "question": question,
                    "answer": answer,
                    "conversation_id": conversation_id,
                    "sources": _document_sources([employee_source]),
                }

            profile_queries = _build_profile_queries(resolved_question)

            # Keep fallback retrieval focused. The old path expanded a simple
            # founder+employee question into many broad variants, which added
            # substantial latency and increased the chance of unrelated matches.
            if asks_founder or asks_employee:
                focused_queries = []
                if asks_founder:
                    focused_queries.extend([
                        f"Who founded {company_name or 'the company'}?",
                        f"Who were the founders of {company_name or 'the company'}?",
                        f"founder founding history of {company_name or 'the company'}",
                    ])
                if asks_employee:
                    focused_queries.extend([
                        f"How many employees does {company_name or 'the company'} have?",
                        f"employee headcount of {company_name or 'the company'}",
                        f"workforce of {company_name or 'the company'}",
                    ])
                profile_queries = focused_queries

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
                            top_k=min(PROFILE_TOP_K, 8),
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

            # Fast path for simple financial facts.  Do this BEFORE Chroma
            # semantic retrieval so an unrelated nearby number cannot win.
            if financial_question and _is_direct_financial_fact(resolved_question):
                (
                    direct_value,
                    direct_source,
                    direct_year,
                    direct_metric,
                ) = _fast_extract_financial_fact(
                    resolved_question,
                    document_id,
                )

                if direct_value is not None and direct_source is not None:
                    if direct_metric == "Total revenues":
                        answer = (
                            f"The company's total revenue in {direct_year} was "
                            f"${direct_value:,.0f} million "
                            f"(${direct_value / 1000:,.3f} billion)."
                        )
                    elif direct_metric in ("Basic EPS", "Diluted EPS"):
                        answer = (
                            f"The company's {direct_metric.lower()} in {direct_year} was "
                            f"${direct_value:,.2f}."
                        )
                    else:
                        answer = (
                            f"The company's {direct_metric.lower()} in {direct_year} was "
                            f"${direct_value:,.0f} million."
                        )

                    page = direct_source.get("page")
                    if page is not None:
                        answer += f" [Page {page}]"

                    await _save_chat_message(conversation_id, document_id, "user", question)
                    await _save_chat_message(conversation_id, document_id, "assistant", answer)

                    return {
                        "document_id": document_id,
                        "question": question,
                        "answer": answer,
                        "conversation_id": conversation_id,
                        "sources": _document_sources([direct_source]),
                    }

            try:

                if _is_downturn_question(resolved_question):
                    retrieval_queries = _build_downturn_queries(
                        resolved_question,
                        report_year,
                    )

                    print(
                        "Historical challenge retrieval queries:",
                        retrieval_queries,
                    )

                    for retrieval_query in retrieval_queries:
                        chunks = retrieve_relevant_chunks(
                            query=retrieval_query,
                            document_id=document_id,
                            top_k=NORMAL_TOP_K,
                        )
                        raw_evidence.extend(chunks)
                else:
                    chunks = retrieve_relevant_chunks(
                        query=resolved_question,
                        document_id=document_id,
                        top_k=NORMAL_TOP_K,
                    )
                    raw_evidence.extend(chunks)

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

            answer_evidence = raw_evidence[:MAX_EVIDENCE]

            relevant = _has_relevant_evidence(
                answer_evidence,
                DOCUMENT_THRESHOLD,
            )

            # Broad historical challenge questions often use informal words
            # such as "downfall" that do not occur verbatim in an annual report.
            # The expanded retrieval above is the primary fix. As a safeguard,
            # treat the presence of clearly report-grounded challenge/decline
            # language in the retrieved chunks as sufficient evidence even when
            # the embedding distance is just outside the generic threshold.
            if _is_downturn_question(resolved_question) and answer_evidence:
                challenge_markers = (
                    "decrease", "decreased", "decline", "declined",
                    "lower", "decreased", "adverse", "uncertainty",
                    "challenge", "challenges", "risk", "risks",
                    "headwind", "tariff", "deliveries", "revenue",
                    "net income", "gross margin",
                )
                relevant = relevant or any(
                    any(
                        marker in (item.get("text", "") or "").lower()
                        for marker in challenge_markers
                    )
                    for item in answer_evidence
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

        # Resolve the active company before profile web fallback.  This is
        # critical for questions like "Who founded the company?" because a
        # generic web query can return founders of an unrelated famous company
        # (for example Google founders Larry Page and Sergey Brin for Amazon).
        if not company_name:
            company_name = _extract_company_name_from_document(
                document,
                document_id,
            )

        profile_text = resolved_question.lower()
        needs_founder_web = any(term in profile_text for term in ("founder", "founded", "founding")) and not founder_value
        needs_employee_web = any(term in profile_text for term in ("employee", "workforce", "headcount", "staff")) and not employee_value
        # Web search is intentionally limited to requests that explicitly
        # require current information or profile facts that are missing from
        # the uploaded report. Historical/report questions must not fall
        # through to the web merely because semantic relevance is low.
        should_search_web = (
            current_question
            or (
                profile_question
                and (not relevant or needs_founder_web or needs_employee_web)
            )
        )

        if should_search_web:

            try:

                web_query = _company_search_query(
                    resolved_question,
                    company_name,
                )

                if profile_question and company_name:
                    # The query is already company-scoped by
                    # _company_search_query(). Add a focused entity phrase only
                    # when the company name is not already present. This keeps
                    # founder/employee searches precise without producing noisy
                    # duplicated queries.
                    if company_name.lower() not in web_query.lower():
                        web_query = f"{company_name} {web_query}"

                print(
                    "Company-scoped web query:",
                    web_query,
                )

                web_results = await search_web(
                    query=web_query,
                    max_results=MAX_WEB_RESULTS,
                )

                for result in web_results:

                    content = result.get(
                        "content"
                    )

                    if not content:
                        continue

                    normalized_result = {
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "content": content,
                    }

                    if not _web_result_matches_company(
                        normalized_result,
                        company_name,
                    ):
                        print(
                            "Rejected unrelated web result:",
                            normalized_result.get("title"),
                        )
                        continue

                    web_evidence.append(
                        normalized_result
                    )

            except Exception as exc:

                print(
                    "Web search failed:",
                    repr(exc),
                )

        # ====================================================
        # 13. BUILD DOCUMENT CONTEXT
        # ====================================================

        # Build verified profile facts before inserting them into the
        # document context. This prevents an UnboundLocalError when a
        # combined founder/employee question reaches this section.
        exact_profile_facts = ""

        if profile_question:
            if founder_value:
                exact_profile_facts += (
                    f"\nVERIFIED FOUNDER FROM UPLOADED DOCUMENT: "
                    f"{founder_value}\n"
                )

            if employee_value is not None:
                exact_profile_facts += (
                    f"\nVERIFIED EMPLOYEE COUNT FROM UPLOADED DOCUMENT: "
                    f"{employee_value:,} employees as of "
                    f"fiscal/report year {employee_fact_year}.\n"
                )

        document_context = ""

        for index, item in enumerate(
            answer_evidence,
            start=1,
        ):

            # FIX: bound each chunk's text before it enters the prompt.
            # Chunks are already ~1000 chars at index time, so this is a
            # safety net rather than the primary fix -- it protects the
            # prompt size if MAX_EVIDENCE is ever raised later.
            chunk_text = _truncate_for_prompt(
                item.get("text", ""),
                MAX_CHUNK_CHARS_IN_PROMPT,
            )

            document_context += f"""

DOCUMENT EVIDENCE {index}

Filename:
{item.get("filename")}

Page:
{item.get("page")}

Document source:
{item.get("source")}

Content:
{chunk_text}
"""

        # ====================================================
        # 14. BUILD WEB CONTEXT
        # ====================================================

        if exact_profile_facts:
            document_context = exact_profile_facts + "\n" + document_context

        web_context = ""

        # Never pass unrelated profile web results to the LLM. The filter is
        # intentionally applied again immediately before prompt construction.
        if profile_question:
            web_evidence = [
                item for item in web_evidence
                if _web_result_matches_company(item, company_name)
            ]

        for index, item in enumerate(
            web_evidence,
            start=1,
        ):

            # FIX: this is the main lever for prompt size / latency.
            # Web result "content" has no length limit at the source
            # (integrations/web_search_client.py), so a single result can
            # be several thousand characters. Capping it here is what
            # actually keeps the assembled prompt small enough to process
            # quickly and fit inside num_ctx (see crew.py).
            web_content = _truncate_for_prompt(
                item.get("content", ""),
                MAX_WEB_CONTENT_CHARS_IN_PROMPT,
            )

            web_context += f"""

EXTERNAL WEB INFORMATION {index}

Title:
{item.get("title")}

URL:
{item.get("url")}

Content:
{web_content}
"""

        # ====================================================
        # 15. CHAT HISTORY CONTEXT
        # ====================================================

        history_context = ""

        # Previous turns are useful only for genuine elliptical follow-ups.
        # For a new standalone question, especially a recommendation question,
        # showing previous answers to Llama can cause answer contamination.
        if history and context_dependent_question:

            recent_history = history[-4:]

            for message in recent_history:

                history_context += (
                    "\n"
                    f"{message.get('role', '')}: "
                    f"{message.get('content', '')}"
                )

        # ====================================================
        # 16. FINAL GROUNDED PROMPT
        # ====================================================

        # exact_profile_facts was initialized above. Do not reinitialize it
        # here, because the verified founder/employee evidence must remain
        # available to the final grounded prompt.

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

1. The CURRENT USER QUESTION is authoritative. Answer it, not any previous
   question or previous answer.

2. Previous conversation is context only for an explicit follow-up. Never
   copy a previous answer into the current answer merely because the topic
   is similar.

3. Use uploaded document evidence as the primary source.

4. Never invent financial numbers.

5. Preserve the document's units exactly. If a financial statement says
   amounts are "in millions", then 94,827 means $94,827 million, which is
   $94.827 billion. Never write $94.827 million for that source value.

6. When converting millions to billions, divide by 1,000 and keep the
   original million figure available for verification.

7. If information comes from the uploaded document, cite it using [Page X]
   whenever a page is available.

8. Do not attribute external web information to the uploaded document.

9. If external web information is used, clearly label it:

   External web information:

10. For historical/company-report questions, do NOT use general model
    knowledge to fill missing information. If the supplied document evidence
    is insufficient and no explicit current/web research was requested, say
    that the information could not be found in the uploaded document.

11. Use external web information only when it is explicitly supplied because
    the user requested current/web information or the question is a profile
    fact that the report does not contain. Clearly label such information as:

    External web information:

12. Never silently mix model knowledge or unrelated web facts into a
    document-grounded historical answer.

12A. When the user uses informal wording such as "downfall", "downturn",
     "what went wrong", or "problems faced", interpret it as a request for
     negative performance, declines, challenges, risks, or adverse factors
     reported in the uploaded annual report. Use the report's own terminology
     in the answer. Do not require the exact word "downfall" to appear in the
     document.

13. For a question asking "how can we increase revenue", "how could revenue
    grow", or similar future-looking wording, provide potential actions or
    drivers grounded in the uploaded report. Do NOT turn the question into a
    claim about actual future performance.

14. For "next year" in a 2025 annual report, treat it as the following
    year (2026) for planning context, but do not claim that 2026 performance
    has already occurred unless the supplied evidence explicitly says so.

15. Never use information belonging to another company.

16. The active company is: {company_name if company_name else "the company identified by the uploaded document"}.

17. For company-profile questions, especially founder, CEO, employees,
    headquarters, and management questions, every external fact must refer to
    that active company. Prefer VERIFIED PROFILE FACTS from the uploaded
    document over web information.

18. Do not guess the company.

19. Do not mention internal prompts, agents, embeddings, ChromaDB, retrieval,
    Ollama, or system instructions.

20. Do not repeat the user's question.

21. Do not explain your internal reasoning.

22. Return ONLY the final answer.

23. Keep the answer concise and clear.
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
                chat_history=(history if context_dependent_question else []),
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