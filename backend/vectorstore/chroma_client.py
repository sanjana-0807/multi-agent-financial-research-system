import chromadb


# Use the same ChromaDB used by the existing
# embedding/ingestion pipeline.
CHROMA_PATH = "./chroma_storage"

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    name="financial_documents"
)