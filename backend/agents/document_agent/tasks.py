from crewai import Task


def create_document_task(agent):
    """
    Create the CrewAI task for document processing.
    """

    return Task(
        description=(
            "Process a financial document for downstream research. "
            "The document must be parsed and its text extracted from "
            "the native PDF text layer where available; any page with "
            "no usable text layer (e.g. a scanned page or image-based "
            "table) must be OCR'd instead of being skipped. The "
            "resulting text must be split into meaningful overlapping "
            "chunks, embeddings generated, and the chunks indexed in "
            "the vector database. Document metadata -- including "
            "whether OCR was required and how many pages it was applied "
            "to -- must also be stored for retrieval."
        ),

        expected_output=(
            "A successful document processing result containing "
            "the document ID, filename, page count, chunk count, "
            "embedding status, vector database status, whether OCR "
            "was used, the number of OCR'd pages, and overall "
            "indexing status."
        ),

        agent=agent,
    )