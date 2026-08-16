from crewai import Agent, LLM


llm = LLM(
    model="ollama/llama3.2:latest",
    base_url="http://localhost:11434",
)


def create_red_flag_agent():
    """
    Creates the CrewAI Red Flag Agent.

    Responsibilities:
    - Detect rising debt
    - Detect falling margins
    - Detect cash flow issues
    - Identify auditor remarks
    - Identify financial risks
    """

    return Agent(
        role="Financial Red Flag Detection Agent",

        goal=(
            "Analyze extracted financial information from company reports "
            "and identify significant financial red flags including rising "
            "debt, falling margins, cash flow issues, auditor remarks, and "
            "other financial risks. Every finding must be supported by "
            "evidence from the provided financial information."
        ),

        backstory=(
            "You are a financial risk analysis specialist working inside "
            "a multi-agent financial research system. You examine financial "
            "statements, extracted metrics, management commentary, auditor "
            "observations, and financial trends to identify potential "
            "warning signs. You never invent financial facts and you "
            "distinguish between confirmed risks and potential concerns."
        ),

        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )