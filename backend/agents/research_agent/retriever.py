import re

from typing import List, Dict, Optional

from vectorstore.chroma_client import collection

from .metrics import detect_metric, extract_year


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
    Calculate a relevance score for a retrieved chunk.

    Higher score = stronger evidence.
    """

    if not text:
        return -999

    text_lower = text.lower()

    score = 0.0

    # -----------------------------------------------------
    # 1. SEMANTIC DISTANCE
    # -----------------------------------------------------

    if distance is not None:

        try:
            distance_value = float(distance)

            # Lower Chroma distance is better.
            score += max(
                0,
                20 - (distance_value * 10)
            )

        except (ValueError, TypeError):
            pass

    # -----------------------------------------------------
    # 2. COMPANY NAME
    # -----------------------------------------------------

    question_lower = question.lower()

    if "walmart" in question_lower and "walmart" in text_lower:
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

        if f"ended january 31" in text_lower:
            score += 5

    # -----------------------------------------------------
    # 4. REQUESTED METRIC
    # -----------------------------------------------------

    metric_signals = _metric_terms(metric)

    for signal in metric_signals:

        if signal in text_lower:
            score += 25

            # Stronger if the exact metric occurs.
            if signal == metric:
                score += 5

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
    # 8. METRIC + YEAR COMBINATION
    # -----------------------------------------------------

    if year and year in text_lower:

        for signal in metric_signals:

            if signal in text_lower:
                score += 15
                break

    # -----------------------------------------------------
    # 9. METRIC + FINANCIAL NUMBER
    # -----------------------------------------------------

    if metric == "net_sales":

        if "net sales" in text_lower and "$" in text:
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

        if "revenue" in text_lower and "$" in text:
            score += 15

    elif metric == "operating_income":

        if (
            "operating income" in text_lower
            and "$" in text
        ):
            score += 15

    elif metric in {
        "net_income",
        "net_income_attributable",
    }:

        if "net income" in text_lower and "$" in text:
            score += 15

    # -----------------------------------------------------
    # 10. SEGMENT PENALTY
    # -----------------------------------------------------

    if _is_segment_chunk(text):

        # General company questions should prefer
        # consolidated company-level evidence.
        if _is_company_level_question(question):
            score -= 50
        else:
            score -= 10

    # -----------------------------------------------------
    # 11. CONSOLIDATED BONUS
    # -----------------------------------------------------

    if (
        _is_company_level_question(question)
        and _is_consolidated_statement(text)
    ):
        score += 30

    return score


# =========================================================
# RETRIEVE RELEVANT CHUNKS
# =========================================================

def retrieve_relevant_chunks(
    question: str,
    document_id: str,
    top_k: int = 5,
) -> List[Dict]:
    """
    Retrieve relevant chunks from ChromaDB and rerank them.

    Flow:

        Question
            ↓
        ChromaDB semantic search
            ↓
        Retrieve candidate chunks
            ↓
        Detect metric + year
            ↓
        Financial relevance scoring
            ↓
        Rerank
            ↓
        Return top_k chunks
    """

    # -----------------------------------------------------
    # VALIDATE QUESTION
    # -----------------------------------------------------

    if not question or not question.strip():
        return []

    # -----------------------------------------------------
    # VALIDATE DOCUMENT ID
    # -----------------------------------------------------

    if not document_id or not document_id.strip():
        return []

    # -----------------------------------------------------
    # VALIDATE TOP K
    # -----------------------------------------------------

    try:
        top_k = int(top_k)
    except (ValueError, TypeError):
        top_k = 5

    if top_k <= 0:
        top_k = 5

    # -----------------------------------------------------
    # DETECT QUESTION METRIC
    # -----------------------------------------------------

    metric = detect_metric(question)

    # -----------------------------------------------------
    # DETECT QUESTION YEAR
    # -----------------------------------------------------

    year = extract_year(question)

    # -----------------------------------------------------
    # DEBUG INFORMATION
    # -----------------------------------------------------

    print()
    print("================ RETRIEVAL ================")
    print(f"Question: {question}")
    print(f"Metric: {metric}")
    print(f"Year: {year}")
    print("-------------------------------------------")

    # -----------------------------------------------------
    # CHROMADB SEARCH
    # -----------------------------------------------------

    try:

        # Retrieve more candidates than requested.
        #
        # Example:
        # top_k = 5
        # retrieve 10
        # rerank 10
        # return best 5
        #
        n_results = max(
            top_k,
            10,
        )

        results = collection.query(
            query_texts=[question],
            n_results=n_results,
            where={
                "document_id": document_id
            },
        )

    except Exception as exc:

        print(
            f"ChromaDB retrieval error: {exc}"
        )

        return []

    # -----------------------------------------------------
    # EXTRACT CHROMADB RESULTS
    # -----------------------------------------------------

    documents = results.get(
        "documents",
        [[]],
    )

    metadatas = results.get(
        "metadatas",
        [[]],
    )

    distances = results.get(
        "distances",
        [[]],
    )

    documents = (
        documents[0]
        if documents
        else []
    )

    metadatas = (
        metadatas[0]
        if metadatas
        else []
    )

    distances = (
        distances[0]
        if distances
        else []
    )

    # -----------------------------------------------------
    # BUILD CHUNKS
    # -----------------------------------------------------

    retrieved_chunks = []

    for index, document in enumerate(documents):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            and metadatas[index]
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        chunk = {
            "text": document or "",

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
        }

        # -------------------------------------------------
        # CALCULATE RELEVANCE
        # -------------------------------------------------

        chunk["relevance_score"] = (
            _calculate_relevance_score(
                question=question,
                text=chunk["text"],
                distance=distance,
                metric=metric,
                year=year,
            )
        )

        retrieved_chunks.append(
            chunk
        )

    # -----------------------------------------------------
    # SORT BY RELEVANCE
    # -----------------------------------------------------

    retrieved_chunks.sort(
        key=lambda chunk: (
            -chunk.get(
                "relevance_score",
                -999,
            ),
            chunk.get(
                "distance",
                float("inf"),
            ),
        )
    )

    # -----------------------------------------------------
    # DEBUG OUTPUT
    # -----------------------------------------------------

    for index, chunk in enumerate(
        retrieved_chunks[:top_k],
        start=1,
    ):

        print(
            f"{index}. "
            f"Page={chunk.get('page')} "
            f"Score={chunk.get('relevance_score', 0):.3f} "
            f"Distance={chunk.get('distance')}"
        )

    print("===========================================")
    print()

    # -----------------------------------------------------
    # RETURN TOP K
    # -----------------------------------------------------

    return retrieved_chunks[:top_k]