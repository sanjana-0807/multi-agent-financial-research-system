from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["financial_research"]

documents = db["documents"]
chunks = db["chunks"]

def save_document(data):
    documents.insert_one(data)
    print("Document Saved Successfully")

def save_chunk(data):
    chunks.insert_one(data)
    print("Chunk Saved Successfully")