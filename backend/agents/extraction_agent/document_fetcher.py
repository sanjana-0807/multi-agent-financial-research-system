from vectorstore.chroma_client import collection


def fetch_document_text(document_id: str):
    result = collection.get(
        where={"document_id": document_id},
        include=["documents", "metadatas"],
    )

    ids = result.get("ids", [])
    if not ids:
        return None

    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])

    paired = list(zip(documents, metadatas))
    paired.sort(key=lambda item: (item[1]["page"], item[1]["chunk_index"]))

    return "\n\n".join(text for text, _ in paired)