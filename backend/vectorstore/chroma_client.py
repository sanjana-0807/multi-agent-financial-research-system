import chromadb


CHROMA_PATH = "vectorstore/chroma_data"

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    name="financial_documents"
)