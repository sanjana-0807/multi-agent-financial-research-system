from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))

# Access the database
db = client[os.getenv("DATABASE_NAME")]

# Check connection
print("Connected Successfully!")

# Display all collections in the database
print("\nCollections in financial_research database:")
collections = db.list_collection_names()

for collection in collections:
    print("-", collection)