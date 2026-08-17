# agents/red_flag_agent/agent.py
import os
from crewai import Agent, LLM
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = LLM(
    model="ollama/llama3.2:latest",
    base_url=OLLAMA_BASE_URL,
)


def create_red_flag_agent():
    """
    CrewAI agent scoped ONLY to classifying auditor remarks and
    going-concern language from retrieved document text.

    Numeric red flags (rising debt, falling margins, cash flow issues,
    other financial risk) are handled deterministically by
    agents/red_flag_agent/rules.py -- this agent never sees numeric
    metrics and must not invent them. It only classifies text that
    was actually retrieved from the filing.
    """
    return Agent(
        role="Auditor Remarks Classification Specialist",
        goal=(
            "Read the provided excerpts from a company's audit report "
            "and related notes, and classify whether they contain a "
            "qualified opinion, going-concern language, a material "
            "weakness disclosure, or other significant audit "
            "observations. Base every finding strictly on the "
            "provided text -- never infer or invent findings not "
            "present in it."
        ),
        backstory=(
            "You are a specialist reviewer who reads auditor's "
            "reports and financial statement notes to identify audit "
            "qualifications and going-concern disclosures. You are "
            "conservative: if the text does not clearly support a "
            "finding, you report that no confirmed finding was "
            "identified rather than guessing."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )