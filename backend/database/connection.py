from pymongo import MongoClient
from pymongo.database import Database

from config.settings import settings


class MongoDB:

    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URL)
        self.db: Database = self.client[settings.DATABASE_NAME]

    def get_collection(self, collection_name: str):
        return self.db[collection_name]


mongodb = MongoDB()