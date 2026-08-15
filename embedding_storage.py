import chromadb
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# 1. Load embedding model
# ---------------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------
# 2. Connect to persistent ChromaDB
# ---------------------------------------------------------

client = chromadb.PersistentClient(
    path="./chroma_test_storage"
)


# ---------------------------------------------------------
# 3. Create/Get collection
# ---------------------------------------------------------

collection = client.get_or_create_collection(
    name="financial_documents",
    configuration={
        "hnsw": {
            "space": "cosine"
        }
    }
)


# ---------------------------------------------------------
# 4. Sample document chunks
# ---------------------------------------------------------
# In the final application these chunks should come
# from the document parsing/chunking pipeline.
# ---------------------------------------------------------

chunks = [
    {
        "chunk_id": "C001",
        "text": "Tesla reported a revenue increase of 15% in 2025.",
        "page_number": 1
    },
    {
        "chunk_id": "C002",
        "text": "Tesla's net profit also increased significantly in 2025.",
        "page_number": 1
    },
    {
        "chunk_id": "C003",
        "text": "Tesla reported changes in its assets and liabilities.",
        "page_number": 2
    }
]


document_id = "D001"


# ---------------------------------------------------------
# 5. Extract text from chunks
# ---------------------------------------------------------

texts = [
    chunk["text"]
    for chunk in chunks
]


# ---------------------------------------------------------
# 6. Generate embeddings
# ---------------------------------------------------------
# normalize_embeddings=True makes cosine similarity
# retrieval more consistent.
# ---------------------------------------------------------

embeddings = model.encode(
    texts,
    normalize_embeddings=True
).tolist()


# ---------------------------------------------------------
# 7. Prepare ChromaDB IDs
# ---------------------------------------------------------

ids = [
    f"{document_id}_{chunk['chunk_id']}"
    for chunk in chunks
]


# ---------------------------------------------------------
# 8. Prepare metadata
# ---------------------------------------------------------

metadatas = [
    {
        "document_id": document_id,
        "page_number": chunk["page_number"],
        "chunk_id": chunk["chunk_id"]
    }
    for chunk in chunks
]


# ---------------------------------------------------------
# 9. Store chunks + embeddings in ChromaDB
# ---------------------------------------------------------

collection.upsert(
    ids=ids,
    documents=texts,
    embeddings=embeddings,
    metadatas=metadatas
)


print("Embeddings stored successfully!")


# ---------------------------------------------------------
# 10. Display collection information
# ---------------------------------------------------------

print("Collection name:", collection.name)
print("Number of stored chunks:", collection.count())


# ---------------------------------------------------------
# 11. Test semantic/vector retrieval
# ---------------------------------------------------------

query = "What was Tesla's revenue increase?"


query_embedding = model.encode(
    query,
    normalize_embeddings=True
).tolist()


results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2,
    include=[
        "documents",
        "metadatas",
        "distances"
    ]
)


# ---------------------------------------------------------
# 12. Display retrieval results
# ---------------------------------------------------------

print("\nSearch Query:")
print(query)

print("\nRetrieved Results:")

for i, document in enumerate(results["documents"][0]):

    print("\nResult", i + 1)
    print("Document:", document)
    print("Metadata:", results["metadatas"][0][i])
    print("Distance:", results["distances"][0][i])