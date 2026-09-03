import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    print("Walmart-related documents:")

    cursor = db.documents.find(
        {
            "$or": [
                {"filename": {"$regex": "walmart", "$options": "i"}},
                {"company_id": "6a97e6ecfca92c8772070594"}
            ]
        },
        {
            "_id": 0,
            "document_id": 1,
            "filename": 1,
            "company_id": 1,
            "status": 1,
            "page_count": 1,
            "chunk_count": 1
        }
    )

    found = False

    async for document in cursor:
        found = True
        print(document)

    if not found:
        print("No Walmart document found in MongoDB.")

    client.close()

asyncio.run(main())
