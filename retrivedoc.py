from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["financial_research"]

documents = db["documents"]

result = documents.find_one({"document_id":"D100"})

print(result)