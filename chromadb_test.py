import chromadb

# Create a ChromaDB client
client = chromadb.PersistentClient(path="./chroma_storage")

# Create a collection
collection = client.get_or_create_collection(
    name="financial_documents"
)
# Add sample financial documents
collection.add(
    documents=[
        "Tesla revenue increased by 20 percent in 2024.",
        "Apple reported higher net profit this year.",
        "Microsoft invested heavily in artificial intelligence."
    ],
    ids=["doc1", "doc2", "doc3"]
)

print("Documents added successfully!")