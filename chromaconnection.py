import chromadb

client = chromadb.PersistentClient(path="./chroma_storage")

collection = client.get_or_create_collection(
    name="financial_documents"
)

print("ChromaDB Connected Successfully!")