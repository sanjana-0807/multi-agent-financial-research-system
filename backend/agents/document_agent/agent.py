from crewai import Agent


def create_document_agent():
    """
    Create the Document Agent.

    Responsibilities:
    - Validate uploaded documents
    - Parse PDF documents
    - Extract text
    - OCR pages that have no extractable text layer (scanned/image pages)
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
            "-- falling back to OCR for scanned or image-only pages -- "
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

        verbose=True,
    )