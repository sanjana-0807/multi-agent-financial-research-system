from crewai import Task


def create_document_task(agent):
    """
    Create the CrewAI task for document processing.
    """

    return Task(
        description=(
            "Process a financial document for downstream research. "
            "The document must be parsed, its text extracted, "
            "split into meaningful overlapping chunks, embeddings "
            "generated, and the chunks indexed in the vector database. "
            "Document metadata must also be stored for retrieval."
        ),

        expected_output=(
            "A successful document processing result containing "
            "the document ID, filename, page count, chunk count, "
            "embedding status, vector database status, and "
            "overall indexing status."
        ),

        agent=agent,
    )