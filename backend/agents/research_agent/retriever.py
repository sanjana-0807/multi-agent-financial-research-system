import re
from typing import List, Dict, Optional

from vectorstore.chroma_client import collection

from .metrics import detect_metric, extract_year, extract_years


# =========================================================
# HELPERS
# =========================================================

def _is_segment_chunk(text: str) -> bool:
    """
    Detect whether a retrieved chunk contains
    segment-level financial information.
    """

    if not text:
        return False

    text_lower = text.lower()

    segment_signals = [
        "walmart u.s.",
        "walmart us",
        "walmart international",
        "sam's club",
        "sam’s club",
        "segment net sales",
        "segment operating income",
        "segment results",
        "business segment",
        "international segment",
        "u.s. segment",
    ]

    return any(
        signal in text_lower
        for signal in segment_signals
    )


def _is_consolidated_statement(text: str) -> bool:
    """
    Detect company-level consolidated financial statements.
    """

    if not text:
        return False

    text_lower = text.lower()

    signals = [
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated income statement",
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "consolidated balance sheets",
        "consolidated balance sheet",
    ]

    return any(
        signal in text_lower
        for signal in signals
    )


def _is_company_level_question(question: str) -> bool:
    """
    Determine whether the question asks about
    the company as a whole rather than a segment.
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
# METRIC SIGNALS
# =========================================================

def _metric_terms(metric: Optional[str]) -> List[str]:
    """
    Return text signals for the requested metric.
    """

    terms = {
        "net_sales": [
            "net sales",
        ],

        "total_revenue": [
            "total revenue",
            "total revenues",
        ],

        "revenue": [
            "revenue",
            "revenues",
        ],

        "operating_income": [
            "operating income",
            "operating profit",
        ],

        "net_income": [
            "net income",
            "consolidated net income",
        ],

        "net_income_attributable": [
            "net income attributable to walmart",
            "consolidated net income attributable to walmart",
            "net income attributable to wal-mart",
            "consolidated net income attributable to wal-mart",
        ],

        "operating_cash_flow": [
            "operating cash flow",
            "operating cash flows",
            "cash flow from operating activities",
            "cash flows from operating activities",
            "cash provided by operating activities",
            "net cash provided by operating activities",
            "cash generated from operations",
        ],

        "diluted_eps": [
            "diluted earnings per share",
            "diluted eps",
            "diluted net income per common share",
        ],

        "eps": [
            "earnings per share",
            "eps",
            "diluted net income per common share",
        ],

        "gross_profit": [
            "gross profit",
        ],

        "gross_margin": [
            "gross margin",
            "percentage of net sales",
        ],
    }

    return terms.get(metric, [])


# =========================================================
# EVIDENCE SCORING
# =========================================================

def _calculate_relevance_score(
    question: str,
    text: str,
    distance,
    metric: Optional[str],
    year: Optional[str],
) -> float:
    """
    Calculate a financial-aware relevance score.

    Higher score = stronger evidence.
    """

    if not text:
        return -999

    text_lower = text.lower()
    question_lower = question.lower()

    score = 0.0

    # -----------------------------------------------------
    # 1. CHROMA DISTANCE
    # -----------------------------------------------------

    if distance is not None:
        try:
            distance_value = float(distance)

            # Lower distance = better semantic match.
            score += max(
                0,
                20 - (distance_value * 10),
            )

        except (ValueError, TypeError):
            pass

    # -----------------------------------------------------
    # 2. COMPANY NAME
    # -----------------------------------------------------

    if (
        "walmart" in question_lower
        and "walmart" in text_lower
    ):
        score += 5

    # -----------------------------------------------------
    # 3. REQUESTED YEAR
    # -----------------------------------------------------

    if year:
        if year in text_lower:
            score += 20

        if f"fiscal {year}" in text_lower:
            score += 10

        if f"fy {year}" in text_lower:
            score += 10

        if "ended january 31" in text_lower:
            score += 5

    # -----------------------------------------------------
    # 4. REQUESTED METRIC
    # -----------------------------------------------------

    metric_signals = _metric_terms(metric)

    for signal in metric_signals:
        if signal in text_lower:
            score += 25
            break

    # -----------------------------------------------------
    # 5. CONSOLIDATED STATEMENT
    # -----------------------------------------------------

    if _is_consolidated_statement(text):
        score += 40

    # -----------------------------------------------------
    # 6. FINANCIAL TABLE SIGNALS
    # -----------------------------------------------------

    if "fiscal years ended january 31" in text_lower:
        score += 20

    if "amounts in millions" in text_lower:
        score += 10

    if "amounts in billions" in text_lower:
        score += 10

    # -----------------------------------------------------
    # 7. NUMERICAL EVIDENCE
    # -----------------------------------------------------

    if "$" in text:
        score += 5

    if re.search(
        r"\b\d[\d,]*(?:\.\d+)?\b",
        text,
    ):
        score += 3

    # -----------------------------------------------------
    # 8. METRIC + YEAR
    # -----------------------------------------------------

    if year and year in text_lower:
        if any(
            signal in text_lower
            for signal in metric_signals
        ):
            score += 15

    # -----------------------------------------------------
    # 9. METRIC-SPECIFIC FINANCIAL EVIDENCE
    # -----------------------------------------------------

    if metric == "net_sales":

        if (
            "net sales" in text_lower
            and "$" in text
        ):
            score += 15

        if (
            "net sales" in text_lower
            and (
                "million" in text_lower
                or "billion" in text_lower
            )
        ):
            score += 10

    elif metric == "total_revenue":

        if (
            (
                "total revenue" in text_lower
                or "total revenues" in text_lower
            )
            and "$" in text
        ):
            score += 15

    elif metric == "revenue":

        if (
            "revenue" in text_lower
            and "$" in text
        ):
            score += 15

    elif metric == "operating_income":

        if (
            "operating income" in text_lower
            and "$" in text
        ):
            score += 15

    elif metric == "operating_cash_flow":

        if (
            (
                "operating cash flow" in text_lower
                or "cash provided by operating activities"
                in text_lower
                or "net cash provided by operating activities"
                in text_lower
            )
            and (
                "$" in text
                or "million" in text_lower
                or "billion" in text_lower
            )
        ):
            score += 20

    elif metric in {
        "net_income",
        "net_income_attributable",
    }:

        if (
            "net income" in text_lower
            and "$" in text
        ):
            score += 15

    # -----------------------------------------------------
    # 10. SEGMENT PENALTY
    # -----------------------------------------------------

    if _is_segment_chunk(text):

        if _is_company_level_question(question):
            score -= 50
        else:
            score -= 10

    # -----------------------------------------------------
    # 11. COMPANY-LEVEL CONSOLIDATED BONUS
    # -----------------------------------------------------

    if (
        _is_company_level_question(question)
        and _is_consolidated_statement(text)
    ):
        score += 30

    return score


# =========================================================
# MULTI-YEAR EVIDENCE CHECK
# =========================================================

def _has_strong_multi_year_evidence(
    text: str,
    metric: Optional[str],
    years: List[str],
    company_level: bool = True,
) -> bool:
    """
    Determine whether a chunk contains strong evidence
    for all requested years.
    """

    if not text or len(years) < 2:
        return False

    text_lower = text.lower()

    # -----------------------------------------------------
    # REJECT SEGMENT DATA FOR COMPANY QUESTIONS
    # -----------------------------------------------------

    if (
        company_level
        and _is_segment_chunk(text)
    ):
        return False

    # -----------------------------------------------------
    # METRIC CHECK
    # -----------------------------------------------------

    metric_signals = _metric_terms(metric)

    if not any(
        signal in text_lower
        for signal in metric_signals
    ):
        return False

    # -----------------------------------------------------
    # YEAR CHECK
    # -----------------------------------------------------

    for year in years:

        if not re.search(
            rf"\b{re.escape(year)}\b",
            text_lower,
        ):
            return False

    # -----------------------------------------------------
    # FINANCIAL EVIDENCE CHECK
    # -----------------------------------------------------

    financial_signals = [
        "fiscal years ended",
        "amounts in millions",
        "amounts in billions",
        "financial highlights",
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "results of operations",
        "net sales",
        "total revenues",
    ]

    if not any(
        signal in text_lower
        for signal in financial_signals
    ):
        return False

    # -----------------------------------------------------
    # COMPANY-LEVEL QUESTIONS REQUIRE CONSOLIDATED DATA
    # -----------------------------------------------------

    if (
        company_level
        and not _is_consolidated_statement(text)
    ):
        return False

    return True


# =========================================================
# RETRIEVE RELEVANT CHUNKS
# =========================================================

def retrieve_relevant_chunks(
    question: str,
    document_id: str,
    top_k: int = 5,
) -> List[Dict]:
    """
    Retrieve relevant financial chunks from the selected document.

    Priorities:
    1. Correct document
    2. Requested metric
    3. Requested years
    4. Consolidated/company-level evidence
    5. Financial tables
    6. Semantic relevance
    """

    if not question or not question.strip():
        return []

    if not document_id or not document_id.strip():
        return []

    try:
        top_k = int(top_k)
    except (ValueError, TypeError):
        top_k = 5

    if top_k <= 0:
        top_k = 5

    # -----------------------------------------------------
    # DETECT QUESTION INFORMATION
    # -----------------------------------------------------

    metric = detect_metric(question)
    year = extract_year(question)
    years = extract_years(question)

    company_level = _is_company_level_question(question)

    print()
    print("================ RETRIEVAL ================")
    print(f"Question: {question}")
    print(f"Metric: {metric}")
    print(f"Year: {year}")
    print(f"Years: {years}")
    print(f"Company level: {company_level}")
    print("-------------------------------------------")

    # -----------------------------------------------------
    # CHROMA SEARCH
    # -----------------------------------------------------

    try:
        results = collection.query(
            query_texts=[question],
            n_results=max(50, top_k),
            where={
                "document_id": document_id
            },
        )

    except Exception as exc:
        print(f"ChromaDB retrieval error: {exc}")
        return []

    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])

    documents = documents[0] if documents else []
    metadatas = metadatas[0] if metadatas else []
    distances = distances[0] if distances else []

    # -----------------------------------------------------
    # BUILD CHUNKS
    # -----------------------------------------------------

    chunks = []

    for index, document in enumerate(documents):

        if not document:
            continue

        metadata = (
            metadatas[index]
            if index < len(metadatas) and metadatas[index]
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        score = _calculate_relevance_score(
            question=question,
            text=document,
            distance=distance,
            metric=metric,
            year=year,
        )

        text_lower = document.lower()

        # -------------------------------------------------
        # EXTRA FINANCIAL PRIORITY
        # -------------------------------------------------

        # Company-level consolidated statements are extremely
        # important for company-wide questions.
        if company_level and _is_consolidated_statement(document):
            score += 100

        # Requested metric.
        metric_signals = _metric_terms(metric)

        if any(
            signal in text_lower
            for signal in metric_signals
        ):
            score += 50

        # Requested years.
        matched_years = 0

        for requested_year in years:
            if re.search(
                rf"\b{re.escape(requested_year)}\b",
                text_lower,
            ):
                matched_years += 1

        score += matched_years * 40

        # Strong multi-year evidence gets a large bonus.
        if len(years) >= 2:

            if _has_strong_multi_year_evidence(
                text=document,
                metric=metric,
                years=years,
                company_level=company_level,
            ):
                score += 150

        # Segment data should never beat consolidated data
        # for a company-level question.
        if (
            company_level
            and _is_segment_chunk(document)
        ):
            score -= 150

        chunk = {
            "text": document,
            "document_id": metadata.get(
                "document_id",
                document_id,
            ),
            "filename": metadata.get(
                "filename",
            ),
            "page": metadata.get(
                "page",
            ),
            "chunk_index": metadata.get(
                "chunk_index",
            ),
            "source": metadata.get(
                "source",
            ),
            "distance": distance,
            "relevance_score": score,
        }

        chunks.append(chunk)

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    chunks.sort(
        key=lambda chunk: (
            -chunk.get("relevance_score", -999),
            chunk.get("distance", float("inf")),
        )
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # For multi-year questions, make sure we return chunks
    # containing the requested years rather than allowing
    # unrelated semantic chunks to occupy all top_k slots.
    # -----------------------------------------------------

    if len(years) >= 2:

        strong_chunks = []

        for chunk in chunks:

            text = chunk.get("text", "")

            if _has_strong_multi_year_evidence(
                text=text,
                metric=metric,
                years=years,
                company_level=company_level,
            ):
                strong_chunks.append(chunk)

        if strong_chunks:

            print(
                f"Strong multi-year evidence: "
                f"{len(strong_chunks)} chunk(s)"
            )

            # Put the strongest multi-year evidence first.
            remaining = [
                chunk
                for chunk in chunks
                if chunk not in strong_chunks
            ]

            chunks = strong_chunks + remaining

    # -----------------------------------------------------
    # FINAL RESULTS
    # -----------------------------------------------------

    final_chunks = chunks[:top_k]

    print()
    print("--------------- FINAL RESULTS --------------")

    for index, chunk in enumerate(
        final_chunks,
        start=1,
    ):
        print(
            f"{index}. "
            f"Page={chunk.get('page')} "
            f"Score={chunk.get('relevance_score', 0):.3f} "
            f"Distance={chunk.get('distance')}"
        )

    print(
        "==========================================="
    )
    print()

    return final_chunks