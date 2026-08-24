from backend.vectorstore.chroma_client import collection


def fetch_document_text(document_id: str):
    """
    Pulls every chunk stored for a document and reassembles them in
    original reading order (by page, then chunk_index within the page).

    NOTE: for very large documents (see the earlier OCR/embedding work --
    a few hundred pages can produce 1000+ chunks), this reassembles the
    ENTIRE document into a single string that then gets embedded in one
    LLM prompt. That can hit the model's context window limit or become
    slow/expensive for very large filings. If this becomes a problem in
    practice, consider extracting per-section (e.g. only the financial
    statements pages) rather than the whole document, or summarizing
    chunks first.
    """
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