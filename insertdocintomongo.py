from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect using values from .env
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]

documents = db["documents"]

documents.insert_one({
    "document_id": "D100",
    "company": "Tesla",
    "pages": 120
})

print("Document Inserted Successfully!")