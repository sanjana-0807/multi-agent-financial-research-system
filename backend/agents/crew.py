from crewai import Crew

from agents.agent_config import (
    create_financial_research_agent,
    create_red_flag_agent,
    create_comparison_agent,
)


def build_financial_research_crew():

    financial_agent = create_financial_research_agent()
    red_flag_agent = create_red_flag_agent()
    comparison_agent = create_comparison_agent()

    crew = Crew(
        agents=[
            financial_agent,
            red_flag_agent,
            comparison_agent,
        ],
        tasks=[],
        verbose=True,
    )

    return crew