from agents.research_agent.research import FinancialResearcher
from agents.research_agent.reasoning import ResearchReasoner
from agents.research_agent.citation import build_citations
from agents.research_agent.response_generator import ResponseGenerator


class FinancialRAGPipeline:

    def __init__(self):

        self.researcher = FinancialResearcher()
        self.reasoner = ResearchReasoner()
        self.response_generator = ResponseGenerator()

    def run(
        self,
        question: str,
        k: int = 5,
    ):

        if not question or not question.strip():

            return {
                "question": question,
                "answer": "Please provide a question.",
                "citations": [],
            }

        # -----------------------------------------
        # 1. Retrieve
        # -----------------------------------------

        results = self.researcher.research(
            question=question,
            k=k,
        )

        if not results:

            return {
                "question": question,
                "answer": (
                    "I could not find relevant information "
                    "in the available financial documents."
                ),
                "citations": [],
            }

        # -----------------------------------------
        # 2. Build context
        # -----------------------------------------

        context_parts = []

        for result in results:

            content = result.get(
                "content",
                "",
            )

            if content:
                context_parts.append(content)

        context = "\n\n".join(context_parts)

        # -----------------------------------------
        # 3. Reason over retrieved context
        # -----------------------------------------

        reasoning = self.reasoner.analyze(
            question=question,
            context=context,
        )

        # -----------------------------------------
        # 4. Build citations
        # -----------------------------------------

        citations = build_citations(
            results
        )

        # -----------------------------------------
        # 5. Generate final response
        # -----------------------------------------

        return self.response_generator.generate(
            question=question,
            reasoning=reasoning,
            citations=citations,
        )