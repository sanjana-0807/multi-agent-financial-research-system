from vectorstore.chroma_client import collection

document_id = "D26BBDD78"

result = collection.get(
    where={"document_id": document_id},
    include=["documents", "metadatas"]
)

print("Document ID:", document_id)
print("Chroma chunks:", len(result.get("ids", [])))

if result.get("metadatas"):
    print("First metadata:", result["metadatas"][0])
