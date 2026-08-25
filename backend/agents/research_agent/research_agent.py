from agents.research_agent.research import FinancialResearcher


researcher = FinancialResearcher()


def answer_question(question: str, k: int = 5):
    """
    Retrieve relevant document chunks and generate a simple
    deterministic financial answer without requiring an LLM.
    """

    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please provide a question.",
            "sources": [],
        }

    results = researcher.research(
        question=question,
        k=k,
    )

    if not results:
        return {
            "question": question,
            "answer": "No relevant information was found in the documents.",
            "sources": [],
        }

    sources = []

    for result in results:
        metadata = result.get("metadata", {})

        sources.append(
            {
                "document_id": metadata.get("document_id"),
                "source": metadata.get("source"),
                "page": metadata.get("page"),
            }
        )

    # -----------------------------------------
    # Simple financial extraction
    # -----------------------------------------

    question_lower = question.lower()

    if "revenue" in question_lower:
        for result in results:
            content = result.get("content", "")

            for line in content.splitlines():
                if "revenue:" in line.lower():
                    revenue = line.split(":", 1)[1].strip()

                    metadata = result.get("metadata", {})

                    answer = (
                        f"The company's revenue in 2025 was {revenue}. "
                        f"Source: {metadata.get('source')}, "
                        f"page {metadata.get('page')}."
                    )

                    return {
                        "question": question,
                        "answer": answer,
                        "sources": sources,
                    }

    # -----------------------------------------
    # Fallback
    # -----------------------------------------

    return {
        "question": question,
        "answer": (
            "The retrieved documents contain relevant information, "
            "but a concise answer could not be extracted automatically."
        ),
        "sources": sources,
    }