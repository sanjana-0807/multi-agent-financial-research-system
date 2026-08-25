from typing import Any


def build_citations(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    citations = []
    seen = set()

    for chunk in chunks:

        metadata = chunk.get(
            "metadata",
            {},
        )

        document_id = metadata.get(
            "document_id"
        )

        page = metadata.get(
            "page"
        )

        source = metadata.get(
            "source"
        )

        key = (
            document_id,
            page,
            source,
        )

        if key in seen:
            continue

        seen.add(key)

        citations.append(
            {
                "document_id": document_id,
                "page": page,
                "source": source,
            }
        )

    return citations