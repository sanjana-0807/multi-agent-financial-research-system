from fastapi import APIRouter, Depends, UploadFile, File

from services.document_service import DocumentService
from utils.security import get_current_user


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    # Execute the actual document ingestion pipeline.
    result = await DocumentService.process_upload(file)

    return result

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user=Depends(get_current_user)
):
    document = await DocumentService.get_document(
        document_id
    )

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "file_size": document.file_size,
        "page_count": document.page_count,
        "chunk_count": document.chunk_count,
        "status": document.status,
        "created_at": document.created_at,
        "updated_at": document.updated_at
    }


@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: str,
    current_user=Depends(get_current_user)
):
    return DocumentService.get_chunks(
        document_id
    )