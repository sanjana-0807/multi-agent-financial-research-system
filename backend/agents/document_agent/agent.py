from crewai import Agent, LLM


# Use local Ollama model instead of OpenAI/Anthropic
llm = LLM(
    model="ollama/llama3.2:latest",
    base_url="http://localhost:11434",
)


def create_document_agent():
    """
    Create the Document Agent.

    Responsibilities:
    - Validate uploaded documents
    - Parse PDF documents
    - Extract text
    - OCR pages that have no extractable text layer
    - Chunk extracted text
    - Generate embeddings
    - Store vectors in ChromaDB
    - Store document metadata in MongoDB
    """

    return Agent(
        role="Document Processing Agent",

        goal=(
            "Process financial research documents by extracting their text, "
            "creating meaningful chunks, generating embeddings, and indexing "
            "the document content for downstream financial research agents."
        ),

        backstory=(
            "You are a document processing specialist for a financial "
            "research system. You prepare financial reports for downstream "
            "AI agents by converting uploaded documents into searchable "
            "vector representations while preserving page and document "
            "metadata. Many annual reports and filings include scanned "
            "pages, signature pages, or image-based tables with no "
            "underlying text layer, so you use OCR to recover their "
            "content rather than silently dropping those pages."
        ),

        llm=llm,
        verbose=True,
        allow_delegation=False,
    )