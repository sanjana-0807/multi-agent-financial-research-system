import chromadb
from sentence_transformers import SentenceTransformer
# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")
# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_storage")
# Create collection
collection = client.get_or_create_collection(
    name="financial_documents"
)
# Sample text
text = """
Tesla reported a revenue increase of 15% in 2025.
The company's net profit also increased significantly.
"""
# Generate embedding
embedding = model.encode(text).tolist()
# Store in ChromaDB
collection.add(
    ids=["doc1"],
    documents=[text],
    embeddings=[embedding],
    metadatas=[
        {
            "document_id": "D001",
            "page_number": 1,
            "chunk_id": "C001"
        }
    ]
)
print("Embedding stored successfully!")