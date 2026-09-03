import asyncio

from database.mongo_client import init_db
from models.document import DocumentModel


async def main():
    await init_db()

    documents = await DocumentModel.find_all().to_list()

    print("MongoDB documents:", len(documents))

    for document in documents:
        print(
            document.document_id,
            "|",
            document.filename,
            "|",
            document.status,
            "| chunks:",
            document.chunk_count
        )


if __name__ == "__main__":
    asyncio.run(main())