from typing import Any
import re


class ResearchReasoner:
    """
    Performs reasoning over retrieved financial-document context.
    """

    def analyze(
        self,
        question: str,
        context: str,
    ) -> dict[str, Any]:

        if not question.strip() or not context.strip():
            return {
                "question": question,
                "analysis": "",
                "conclusion": "",
                "insufficient_context": True,
            }

        question_lower = question.lower()

        # Revenue questions
        if "revenue" in question_lower:
            match = re.search(
                r"Revenue\s*:\s*\$?\s*([\d,.]+)\s*(Million|Billion|Thousand)?",
                context,
                re.IGNORECASE,
            )

            if match:
                amount = match.group(1)
                unit = match.group(2)

                if unit:
                    answer = f"The company's revenue was ${amount} {unit}."
                else:
                    answer = f"The company's revenue was ${amount}."

                return {
                    "question": question,
                    "analysis": (
                        "The retrieved annual report states "
                        f"Revenue: ${amount}"
                        f"{' ' + unit if unit else ''}."
                    ),
                    "conclusion": answer,
                    "insufficient_context": False,
                }

        # Net profit questions
        if "net profit" in question_lower or "profit" in question_lower:
            match = re.search(
                r"Net\s+Profit\s*:\s*\$?\s*([\d,.]+)\s*(Million|Billion|Thousand)?",
                context,
                re.IGNORECASE,
            )

            if match:
                amount = match.group(1)
                unit = match.group(2)

                if unit:
                    answer = f"The company's net profit was ${amount} {unit}."
                else:
                    answer = f"The company's net profit was ${amount}."

                return {
                    "question": question,
                    "analysis": (
                        "The retrieved annual report contains "
                        f"Net Profit: ${amount}"
                        f"{' ' + unit if unit else ''}."
                    ),
                    "conclusion": answer,
                    "insufficient_context": False,
                }

        # Operating margin questions
        if "operating margin" in question_lower:
            match = re.search(
                r"Operating\s+Margin\s*:\s*([\d,.]+)\s*%",
                context,
                re.IGNORECASE,
            )

            if match:
                value = match.group(1)

                return {
                    "question": question,
                    "analysis": (
                        f"The retrieved annual report states "
                        f"an operating margin of {value}%."
                    ),
                    "conclusion": (
                        f"The company's operating margin was {value}%."
                    ),
                    "insufficient_context": False,
                }

        # Generic fallback
        return {
            "question": question,
            "analysis": context,
            "conclusion": (
                "The retrieved financial document contains "
                "information relevant to the question, but I could "
                "not extract a specific numerical answer."
            ),
            "insufficient_context": False,
        }
