from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]
documents = db["documents"]


def fetch_document_text(document_id):
    result = documents.find_one({"document_id": document_id})
    if result is None:
        return None

    # NOTE: not confirmed with member 5 yet which field actually holds
    # the text - assuming "text" for now, change if hers is different
    return result.get("text")
