from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Access the database
db = client["financial_research"]

# Check connection
print("Connected Successfully!")

# Display all collections in the database
print("\nCollections in financial_research database:")
collections = db.list_collection_names()

for collection in collections:
    print("-", collection)