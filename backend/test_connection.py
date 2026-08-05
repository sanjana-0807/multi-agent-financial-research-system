from database.connection import mongodb

print("Database Connected Successfully!")

print(
    mongodb.db.list_collection_names()
)