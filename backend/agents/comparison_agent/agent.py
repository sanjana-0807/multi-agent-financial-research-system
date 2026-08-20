# agents/comparison_agent/agent.py
import os
from crewai import Agent, LLM

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = LLM(
    model="ollama/llama3.2:latest",
    base_url=OLLAMA_BASE_URL,
)


def create_comparison_agent():
    """
    CrewAI agent scoped ONLY to narrating an already-computed numeric
    comparison table (see agents/comparison_agent/benchmarking.py).

    It never receives raw document text and never computes a number
    itself -- benchmarking.py does that deterministically in Python.
    This agent's only job is to explain, in plain analyst language,
    what the numbers mean and which company is stronger on which
    dimension, citing the exact metric and ticker for every claim.
    """
    return Agent(
        role="Company Comparison Analyst",
        goal=(
            "Explain an already-computed cross-company financial "
            "comparison table in clear analyst language, highlighting "
            "the most meaningful differences and citing the exact "
            "metric and ticker behind every claim. Never invent a "
            "number that is not present in the supplied table."
        ),
        backstory=(
            "You are a financial analyst who specializes in peer "
            "benchmarking. You are handed a table of metrics that has "
            "already been calculated for each company, and your job is "
            "to turn it into a short, readable narrative -- not to do "
            "any arithmetic yourself."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )