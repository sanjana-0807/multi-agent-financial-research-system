from vectorstore.chroma_client import collection


def retrieve_relevant_chunks(
    question: str,
    document_id: str,
    top_k: int = 5,
):
    """
    Retrieve the most relevant chunks for a user question
    from the existing financial document collection.
    """

    results = collection.query(
        query_texts=[question],
        n_results=top_k,
        where={
            "document_id": document_id
        },
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved_chunks = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        retrieved_chunks.append(
            {
                "text": document,
                "document_id": metadata.get("document_id"),
                "filename": metadata.get("filename"),
                "page": metadata.get("page"),
                "chunk_index": metadata.get("chunk_index"),
                "source": metadata.get("source"),
                "distance": distance,
            }
        )

    return retrieved_chunks