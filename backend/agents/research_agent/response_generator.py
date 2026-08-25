from typing import Any


class ResponseGenerator:
    """
    Generates the final research response from reasoning output
    and supporting citations.
    """

    def generate(
        self,
        question: str,
        reasoning: dict[str, Any],
        citations: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if reasoning.get("insufficient_context"):
            answer = (
                "I could not find sufficient supporting information "
                "in the available financial documents."
            )
        else:
            answer = reasoning.get("conclusion", "").strip()

            if not answer:
                answer = (
                    "The available financial documents contain relevant "
                    "information, but no specific conclusion was extracted."
                )

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
        }
