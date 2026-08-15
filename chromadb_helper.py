import chromadb
from sentence_transformers import SentenceTransformer


# =========================================================
# 1. Load embedding model
# =========================================================

model = SentenceTransformer("all-MiniLM-L6-v2")


# =========================================================
# 2. Connect to persistent ChromaDB
# =========================================================

client = chromadb.PersistentClient(
    path="./chroma_storage"
)


# =========================================================
# 3. Create optimized collection
# =========================================================

collection = client.get_or_create_collection(
    name="financial_documents",
    configuration={
        "hnsw": {
            "space": "cosine"
        }
    }
)


# =========================================================
# 4. Store embedding
# =========================================================

def store_embedding(text, metadata, doc_id):

    embedding = model.encode(
        text,
        normalize_embeddings=True
    ).tolist()

    # Use a stable ID so the same chunk is not duplicated
    chunk_id = metadata.get("chunk_id")

    if chunk_id:
        embedding_id = f"{doc_id}_{chunk_id}"
    else:
        embedding_id = doc_id

    collection.upsert(
        ids=[embedding_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )

    print("Embedding Stored Successfully")


# =========================================================
# 5. Search embeddings
# =========================================================

def search_embedding(
    query,
    document_id=None,
    n_results=3
):

    # Generate normalized query embedding
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    # -----------------------------------------------------
    # Filter by document when document_id is provided
    # -----------------------------------------------------

    where_filter = None

    if document_id:
        where_filter = {
            "document_id": document_id
        }

    # -----------------------------------------------------
    # Vector search
    # -----------------------------------------------------

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    return results