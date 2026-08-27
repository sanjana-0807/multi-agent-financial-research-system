from typing import List, Dict


def build_citations(
    retrieved_chunks: List[Dict]
) -> List[Dict]:
    """
    Convert retrieved chunks into clean, unique source citations.

    Citations are deduplicated by document + page.
    """

    citations = []
    seen = set()

    for chunk in retrieved_chunks:

        document_id = chunk.get("document_id")
        page = chunk.get("page")

        key = (
            document_id,
            page
        )

        if key in seen:
            continue

        seen.add(key)

        citations.append({
            "document_id": document_id,
            "filename": chunk.get("filename", "Unknown"),
            "page": page,
            "source": chunk.get("source", "Unknown")
        })

    return citations