from vectorstore.chroma_client import collection

DOCUMENT_ID = "DC4FB216A"

result = collection.get(
    where={"document_id": DOCUMENT_ID},
    include=["documents", "metadatas"],
)

for document, metadata in zip(
    result["documents"],
    result["metadatas"]
):
    if "revenue" in document.lower():
        print("=" * 80)
        print("PAGE:", metadata.get("page"))
        print("DOCUMENT:", metadata.get("document_id"))
        print()
        print(document)
        print()