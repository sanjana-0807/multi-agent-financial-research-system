import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_storage")

collection = client.get_or_create_collection(
    name="financial_documents"
)

def store_embedding(text, metadata, doc_id):
    embedding = model.encode(text).tolist()

    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )

    print("Embedding Stored Successfully")

def search_embedding(query):
    results = collection.query(
        query_texts=[query],
        n_results=1
    )

    return results