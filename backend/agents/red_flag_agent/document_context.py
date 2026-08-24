# agents/red_flag_agent/document_context.py
"""
Lightweight keyword-based retrieval for the auditor-remarks LLM layer.

Rather than feeding an entire filing (which can run 60+ pages) into the
LLM, this pulls only the chunks that are plausibly relevant to auditor
opinions / going-concern language, plus one neighboring chunk on each
side for context. This keeps the LLM call fast and scoped -- the model
only ever sees text actually retrieved from the document, never
numbers it has to interpret itself.
"""
from backend.vectorstore.chroma_client import collection

AUDITOR_KEYWORDS = [
    "auditor", "audit opinion", "independent registered public accounting",
    "going concern", "qualified opinion", "adverse opinion",
    "material weakness", "material uncertainty",
    "internal control over financial reporting",
    "substantial doubt", "emphasis of matter",
]

MAX_CONTEXT_CHARS = 8000


def fetch_auditor_context(document_id: str) -> str | None:
    """
    Returns a bounded block of text containing only chunks likely to
    discuss auditor opinions/going-concern language, or None if no
    such chunks were found -- in which case the LLM should not be
    called at all, since there's nothing grounded to classify.
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

    matched_indices = set()
    for i, (text, _meta) in enumerate(paired):
        lowered = text.lower()
        if any(kw in lowered for kw in AUDITOR_KEYWORDS):
            matched_indices.add(i)
            if i > 0:
                matched_indices.add(i - 1)
            if i < len(paired) - 1:
                matched_indices.add(i + 1)

    if not matched_indices:
        return None

    selected = sorted(matched_indices)
    blocks = []
    total_len = 0
    for i in selected:
        text, meta = paired[i]
        block = f"[Page {meta.get('page')}]\n{text}"
        if total_len + len(block) > MAX_CONTEXT_CHARS:
            break
        blocks.append(block)
        total_len += len(block)

    return "\n\n---\n\n".join(blocks) if blocks else None