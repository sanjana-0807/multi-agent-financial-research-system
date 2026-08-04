from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to MongoDB Atlas using .env
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]

documents = db["documents"]
chunks = db["chunks"]

def save_document(data):
    documents.insert_one(data)
    print("Document Saved Successfully")

def save_chunk(data):
    chunks.insert_one(data)
    print("Chunk Saved Successfully")