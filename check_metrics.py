import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()


async def main():

    client = AsyncIOMotorClient(
        os.getenv("MONGO_URI")
    )

    db = client[os.getenv("DATABASE_NAME")]

    collection = db["extracted_metrics"]

    documents = await collection.find().to_list(length=20)

    print("\nExtracted Metrics in MongoDB:")
    print("--------------------------------")

    if not documents:
        print("No extracted metrics found.")

    for document in documents:
        print(document)

    client.close()


asyncio.run(main())