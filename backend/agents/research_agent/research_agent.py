from typing import Dict

from .retriever import retrieve_relevant_chunks
from .response_generator import generate_research_response
from .agent import llm


def answer_research_question(
    question: str,
    document_id: str,
    top_k: int = 5,
) -> Dict:
    """
    Run the complete Research Agent pipeline.
    """

    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please provide a research question.",
            "evidence": None,
            "citations": [],
            "retrieved_chunks": [],
        }

    if not document_id or not document_id.strip():
        return {
            "question": question,
            "answer": "A document ID is required.",
            "evidence": None,
            "citations": [],
            "retrieved_chunks": [],
        }

    try:
        top_k = int(top_k)
    except (ValueError, TypeError):
        top_k = 5

    if top_k <= 0:
        top_k = 5

    # -----------------------------------------------------
    # STEP 1: RETRIEVE
    # -----------------------------------------------------

    retrieved_chunks = retrieve_relevant_chunks(
        question=question,
        document_id=document_id,
        top_k=top_k,
    )

    # -----------------------------------------------------
    # STEP 2: GENERATE ANSWER
    # -----------------------------------------------------

    response = generate_research_response(
        question=question,
        retrieved_chunks=retrieved_chunks,
        llm=llm,
    )

    return response