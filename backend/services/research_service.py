from agents.research_agent.research_agent import answer_research_question


class ResearchService:

    @staticmethod
    def ask_question(
        question: str,
        document_id: str,
    ):
        """
        Answer a user's financial research question
        using the selected document.
        """

        return answer_research_question(
            question=question,
            document_id=document_id,
            top_k=5,
        )