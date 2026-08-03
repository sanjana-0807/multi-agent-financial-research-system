import chromadb
client = chromadb.PersistentClient(path="./chroma_storage")
collection = client.get_collection("financial_documents")
results = collection.query(
    query_texts=[
        "Which company earned more profit?"
    ],
    n_results=1
)
print(results)