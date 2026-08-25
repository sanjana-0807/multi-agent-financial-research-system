import asyncio

from database.connection import init_db
from models.document import DocumentModel


async def main():
    await init_db()

    documents = [
        {
            "document_id": "6a72eecd9c02a244fae868f8",
            "file_name": "Sample_Annual_Report_2025.pdf",
        },
        {
            "document_id": "6a8d3412940a084b9b0c139d",
            "file_name": "74762093-898c-4a94-b8d1-c7ca5b5f063d_Sample_Annual_Report_2025.pdf",
        },
    ]

    for document in documents:
        print(
            document["document_id"],
            document["file_name"]
        )


asyncio.run(main())