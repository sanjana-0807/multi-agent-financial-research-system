# agents/report_agent/agent.py

import os
from crewai import Agent, LLM


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)

llm = LLM(
    model="ollama/llama3.2:latest",
    base_url=OLLAMA_BASE_URL,
)


def create_report_agent():
    """
    Create the final Report Agent.

    The Report Agent receives already-collected evidence from the
    other agents and produces the final user-facing response.

    It does NOT independently retrieve documents or invent financial
    numbers.
    """

    return Agent(
        role="Financial Research Report Analyst",

        goal=(
            "Produce a concise, accurate final answer using the supplied "
            "evidence from the financial research agents and conversation "
            "context. Preserve document-derived facts, calculations, and "
            "source citations exactly. Clearly identify any information "
            "added from general AI/model knowledge."
        ),

        backstory=(
            "You are the final reviewer in a financial research system. "
            "Other specialized agents have already collected document "
            "evidence, extracted financial metrics, detected risks, and "
            "performed company comparisons. Your responsibility is to "
            "combine those results into one clear answer. You never "
            "invent financial values and never present model knowledge "
            "as information obtained from a company document."
        ),

        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )