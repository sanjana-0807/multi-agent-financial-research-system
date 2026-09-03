from crewai import Agent


def create_financial_research_agent():
    return Agent(
        role="Financial Research Analyst",
        goal="Analyze financial reports and extract meaningful insights.",
        backstory=(
            "You are an expert financial analyst specialized in reading "
            "annual reports, balance sheets, income statements, and cash "
            "flow statements to generate useful insights."
        ),
        verbose=True,
    )


def create_red_flag_agent():
    return Agent(
        role="Financial Risk Analyst",
        goal="Identify financial red flags and potential risks.",
        backstory=(
            "You are responsible for detecting accounting anomalies, "
            "financial inconsistencies, and possible risk indicators."
        ),
        verbose=True,
    )


def create_comparison_agent():
    return Agent(
        role="Company Comparison Analyst",
        goal="Compare multiple companies using extracted financial metrics.",
        backstory=(
            "You compare financial performance across companies using "
            "ratios, profitability, liquidity, and growth metrics."
        ),
        verbose=True,
    )