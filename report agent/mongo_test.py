from pymongo import MongoClient
from getpass import getpass

username = input("MongoDB username: ")
password = getpass("MongoDB password: ")

client = MongoClient(
    "mongodb+srv://cluster0.nqpnmoc.mongodb.net/",
    username=username,
    password=password,
    authSource="admin"
)

db = client["financial_research"]

print("MongoDB Connected Successfully!")
print("Collections:")
print(db.list_collection_names())