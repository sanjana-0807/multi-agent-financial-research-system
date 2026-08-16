from crewai import Crew, Process

from agents.red_flag_agent.agent import create_red_flag_agent
from agents.red_flag_agent.tasks import create_red_flag_task


def create_red_flag_crew():
    """
    Creates the CrewAI Red Flag Analysis Crew.
    """

    agent = create_red_flag_agent()

    task = create_red_flag_task(agent)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    return crew