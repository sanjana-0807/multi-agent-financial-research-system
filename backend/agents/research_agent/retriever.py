from typing import Any

from vectorstore.chroma_client import collection


def retrieve_relevant_chunks(
    query: str,
    document_id: str,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """
    Retrieve semantically relevant chunks from the
    uploaded document.

    Retrieval is restricted to the supplied document_id,
    making the Research Agent company-agnostic.

    Lower ChromaDB distance means stronger semantic
    similarity.
    """

    if not query or not query.strip():
        return []

    if not document_id:
        return []

    # Allow a wider semantic retrieval pool.
    top_k = max(
        1,
        min(top_k, 50),
    )

    result = collection.query(
        query_texts=[
            query.strip()
        ],
        n_results=top_k,
        where={
            "document_id": document_id
        },
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = result.get(
        "documents",
        [[]],
    )[0]

    metadatas = result.get(
        "metadatas",
        [[]],
    )[0]

    distances = result.get(
        "distances",
        [[]],
    )[0]

    chunks = []

    for index, document in enumerate(
        documents
    ):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        chunks.append(
            {
                "text": document,

                "document_id": metadata.get(
                    "document_id",
                    document_id,
                ),

                "filename": metadata.get(
                    "filename"
                ),

                "page": metadata.get(
                    "page"
                ),

                "chunk_index": metadata.get(
                    "chunk_index"
                ),

                "source": metadata.get(
                    "source"
                ),

                "distance": distance,
            }
        )

    return chunks