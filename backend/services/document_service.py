import os
import shutil
from uuid import uuid4

from fastapi import UploadFile

from models.document import DocumentModel
from schemas.document_schema import DocumentUploadResponse

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


async def upload_document(
    company_id: str,
    file: UploadFile,
) -> DocumentUploadResponse:

    filename = f"{uuid4()}_{file.filename}"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename,
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = DocumentModel(
        company_id=company_id,
        file_name=file.filename,
        file_path=filepath,
        status="Uploaded",
    )

    await document.insert()

    return DocumentUploadResponse(
        id=str(document.id),
        company_id=document.company_id,
        file_name=document.file_name,
        file_path=document.file_path,
        status=document.status,
        uploaded_at=document.uploaded_at,
    )