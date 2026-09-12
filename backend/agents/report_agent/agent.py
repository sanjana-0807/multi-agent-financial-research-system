# agents/report_agent/agent.py
import os
from crewai import Agent, LLM

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = LLM(
    model="ollama/llama3.2:latest",
    base_url=OLLAMA_BASE_URL,
)


def create_report_agent():
    """
    CrewAI agent scoped ONLY to narrating already-computed report data
    into an Executive Summary and Outlook.

    It never sees the raw document, and never sees numbers it could
    get wrong -- it is handed the finished Key Financials, Red Flags,
    and Company Comparison sections (already computed deterministically
    or by other agents) and writes prose around them. This mirrors the
    same principle agents/comparison_agent/crew.py uses for its
    narrative step.
    """
    return Agent(
        role="Financial Report Writer",
        goal=(
            "Write a concise, professional Executive Summary and a "
            "forward-looking Outlook section for a financial research "
            "report, based strictly on the financial metrics, red "
            "flags, and comparison data provided. Never invent a "
            "number, ratio, ranking, or finding that is not present "
            "in the provided data."
        ),
        backstory=(
            "You are a financial analyst who writes the narrative "
            "sections of institutional research reports. You write "
            "in clear, neutral, professional language suitable for "
            "investors and executives. You highlight what the data "
            "actually shows -- strengths, risks, and open questions "
            "-- without exaggeration or speculation beyond what the "
            "figures and flags support. If a section's underlying "
            "data was not available, you say so plainly rather than "
            "filling the gap with a guess."
        ),
        llm=llm,
        # CrewAI's internal JSON-repair/converter step (triggered when
        # the LLM's raw output isn't cleanly parseable JSON on the
        # first try) uses its own default LLM unless explicitly told
        # otherwise, and defaults to OpenAI even when the agent's own
        # `llm` is Ollama. Pointing it at the same Ollama model
        # prevents that internal fallback from ever reaching for a
        # real OpenAI connection. (Also set OPENAI_API_KEY/API_BASE
        # env vars to Ollama's OpenAI-compatible endpoint as a second
        # layer of defense -- see backend/.env.)
        function_calling_llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )