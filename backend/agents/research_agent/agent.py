from crewai import Agent


def create_research_agent():
    """
    Creates the Research Agent definition.

    The actual response generation is handled through Ollama
    in crew.py so that the project can use Llama 3.2 locally.
    """

    return Agent(
        role="Financial Research Analyst",

        goal=(
            "Answer financial research questions accurately using "
            "the supplied document evidence, external web evidence "
            "when available, conversation context, and clearly "
            "identified model knowledge when required."
        ),

        backstory=(
            "You are a careful financial research analyst. "
            "You prioritize supplied financial-document evidence, "
            "never invent financial figures, distinguish external "
            "information from document information, and clearly "
            "identify information supplied by model knowledge."
        ),

        verbose=False,
        allow_delegation=False,
        max_iter=1,
    )