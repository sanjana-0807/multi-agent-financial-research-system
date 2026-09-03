import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    print("Collections:", await db.list_collection_names())
    print("Documents count:", await db.documents.count_documents({}))

    document = await db.documents.find_one(
        {"document_id": "D6C7EF349"}
    )

    print("D6C7EF349 exists:", document is not None)

    if document:
        print("Filename:", document.get("filename"))
        print("Company ID:", document.get("company_id"))
        print("Status:", document.get("status"))

    await client.close()

asyncio.run(main())
