from crewai import Crew

from agents.document_agent.agent import create_document_agent
from agents.document_agent.tasks import create_document_task


def create_document_crew():
    """
    Create the CrewAI crew responsible for document processing.
    """

    document_agent = create_document_agent()

    document_task = create_document_task(
        document_agent
    )

    crew = Crew(
        agents=[document_agent],
        tasks=[document_task],
        verbose=True,
    )

    return crew