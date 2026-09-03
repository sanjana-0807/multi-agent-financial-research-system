import asyncio
from io import BytesIO

from fastapi import UploadFile

from services.document_service import DocumentService
from database.mongo_client import init_db


PDF_PATH = r".\documents\D09AE81D6_D955A489C_NVIDIA-2025-Annual-Report.pdf"


async def main():

    # Initialize MongoDB + Beanie
    print("Initializing database...")
    await init_db()
    print("Database initialized.")

    # Read PDF
    with open(PDF_PATH, "rb") as f:
        content = f.read()

    upload = UploadFile(
        filename="D09AE81D6_D955A489C_NVIDIA-2025-Annual-Report.pdf",
        file=BytesIO(content),
    )

    # Run existing Document Service
    print("Indexing document...")
    result = await DocumentService.process_upload(upload)

    print("\n===== DOCUMENT INDEXING RESULT =====")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())