import os

from crewai import Agent, LLM


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)


llm = LLM(
    model="ollama/llama3.2:latest",
    base_url=OLLAMA_BASE_URL,
)


def create_research_agent():
    """
    Create the Research Agent.

    Responsibilities:
    - Understand the user's financial research question
    - Retrieve relevant document evidence
    - Reason over the retrieved evidence
    - Generate a grounded answer
    - Provide source information
    """

    return Agent(
        role="Financial Research Agent",

        goal=(
            "Answer financial research questions accurately using "
            "evidence retrieved from the selected financial document."
        ),

        backstory=(
            "You are a financial research specialist. You analyze "
            "financial reports and answer user questions using only "
            "the evidence available in the provided documents. "
            "You never invent financial information and clearly "
            "identify the source pages supporting your conclusions."
        ),

        llm=llm,
        verbose=True,
        allow_delegation=False,
    )