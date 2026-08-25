from agents.research_agent.retrieval import FinancialRetriever


class FinancialResearcher:

    def __init__(self):
        self.retriever = FinancialRetriever()

    def research(
        self,
        question: str,
        k: int = 5,
    ):

        if not question or not question.strip():
            return []

        documents = self.retriever.search(
            query=question,
            k=k,
        )

        results = []

        for document in documents:

            results.append(
                {
                    "content": document.page_content,
                    "metadata": document.metadata,
                }
            )

        return results