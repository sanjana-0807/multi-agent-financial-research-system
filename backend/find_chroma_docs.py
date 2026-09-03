from vectorstore.chroma_client import collection

result = collection.get(
    include=["metadatas"]
)

ids = result.get("ids", [])
metadatas = result.get("metadatas", [])

print("Total Chroma chunks:", len(ids))

document_ids = {}

for metadata in metadatas:
    if metadata and metadata.get("document_id"):
        doc_id = metadata["document_id"]
        document_ids[doc_id] = document_ids.get(doc_id, 0) + 1

print("\nWalmart-related Chroma documents:")

for doc_id, count in document_ids.items():
    if doc_id.startswith("D"):
        print(doc_id, "->", count, "chunks")
