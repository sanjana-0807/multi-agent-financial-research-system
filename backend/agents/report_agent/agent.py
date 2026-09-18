# agents/report_agent/agent.py

import os

from crewai import Agent, LLM


# ============================================================
# Ollama Configuration
# ============================================================

# Ollama server
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).strip()


# Model name from environment, if provided.
# Example accepted values:
#
#   llama3.2:latest
#   ollama/llama3.2:latest
#
OLLAMA_MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:latest",
).strip()


# ============================================================
# IMPORTANT:
# CrewAI needs the "ollama/" provider prefix.
#
# If .env contains:
#     OLLAMA_MODEL=llama3.2:latest
#
# convert it to:
#     ollama/llama3.2:latest
#
# If .env already contains:
#     OLLAMA_MODEL=ollama/llama3.2:latest
#
# leave it unchanged.
# ============================================================

if OLLAMA_MODEL_NAME.lower().startswith("ollama/"):
    OLLAMA_MODEL = OLLAMA_MODEL_NAME
else:
    OLLAMA_MODEL = f"ollama/{OLLAMA_MODEL_NAME}"


# ============================================================
# Ollama LLM
# ============================================================

llm = LLM(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,

    # Low temperature gives consistent financial narratives.
    temperature=0.1,

    # Keep the generated report narrative concise.
    max_tokens=350,
)


# ============================================================
# Startup Diagnostics
# ============================================================

print(
    f"[Report Agent] LLM configured: "
    f"model={OLLAMA_MODEL}, "
    f"base_url={OLLAMA_BASE_URL}, "
    f"provider=Ollama"
)


# ============================================================
# Report Agent
# ============================================================

def create_report_agent():
    """
    Create the Report Agent.

    The Report Agent is responsible ONLY for writing:

        1. Executive Summary
        2. Outlook

    It does NOT:

        - read PDFs
        - query ChromaDB
        - perform web searches
        - retrieve financial information
        - calculate financial metrics
        - call other agents
        - use external tools

    All financial data is supplied by the existing
    financial extraction, red flag, and comparison
    processes.
    """

    return Agent(

        # ----------------------------------------------------
        # Role
        # ----------------------------------------------------

        role="Financial Report Writer",

        # ----------------------------------------------------
        # Goal
        # ----------------------------------------------------

        goal=(
            "Create a concise and professional financial-report "
            "narrative using ONLY the supplied report data. "
            "Write an Executive Summary and an Outlook section. "
            "Do not calculate, modify, estimate, rank, or invent "
            "financial values."
        ),

        # ----------------------------------------------------
        # Backstory
        # ----------------------------------------------------

        backstory=(
            "You are a financial research report writer. "
            "Other components of the system have already performed "
            "document retrieval, financial extraction, risk analysis, "
            "and company comparison. "
            "\n\n"
            "Your job is ONLY to convert those verified results "
            "into clear, concise and professional narrative. "
            "\n\n"
            "Use only information explicitly provided in the task "
            "input. Never introduce outside facts. "
            "\n\n"
            "Never invent revenue, profit, assets, liabilities, "
            "growth rates, employee counts, rankings, risks, "
            "forecasts, or other financial information. "
            "\n\n"
            "If information is unavailable, clearly state that "
            "the information was not available."
        ),

        # ----------------------------------------------------
        # Ollama LLM
        # ----------------------------------------------------

        llm=llm,

        # ----------------------------------------------------
        # Agent configuration
        # ----------------------------------------------------

        verbose=False,

        allow_delegation=False,

        # The Report Agent should complete its task in one pass.
        max_iter=1,

        # No tools are required.
        tools=[],
    )