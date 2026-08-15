from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))

db = client[os.getenv("DATABASE_NAME")]

documents = db["documents"]
chunks = db["chunks"]


# ==============================
# SAVE DOCUMENT
# ==============================

def save_document(data):

    document_id = data.get("document_id")

    if not document_id:
        raise ValueError("document_id is required")

    result = documents.update_one(
        {"document_id": document_id},
        {"$set": data},
        upsert=True
    )

    if result.upserted_id:
        print("Document inserted successfully")
    else:
        print("Document already exists - updated successfully")


# ==============================
# SAVE CHUNK
# ==============================

def save_chunk(data):

    document_id = data.get("document_id")
    chunk_id = data.get("chunk_id")

    if not document_id:
        raise ValueError("document_id is required")

    if not chunk_id:
        raise ValueError("chunk_id is required")

    result = chunks.update_one(
        {
            "document_id": document_id,
            "chunk_id": chunk_id
        },
        {"$set": data},
        upsert=True
    )

    if result.upserted_id:
        print("Chunk inserted successfully")
    else:
        print("Chunk already exists - updated successfully")