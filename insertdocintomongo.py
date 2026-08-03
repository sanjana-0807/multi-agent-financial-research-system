from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["financial_research"]

documents = db["documents"]

documents.insert_one({
    "document_id":"D100",
    "company":"Tesla",
    "pages":120
})

print("Document Inserted Successfully!")