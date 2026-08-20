from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from schemas.document_schema import LinkCompanyRequest
from services.document_service import DocumentService
from utils.security import get_current_user


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    company_id: Optional[str] = Form(None),
    current_user=Depends(get_current_user)
):
    # Execute the actual document ingestion pipeline. company_id is
    # optional at upload time -- a document can be linked to a company
    # later via PATCH /documents/{document_id}/link-company instead.
    result = await DocumentService.process_upload(file, company_id=company_id)

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
        "company_id": document.company_id,
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


@router.patch("/{document_id}/link-company")
async def link_document_to_company(
    document_id: str,
    payload: LinkCompanyRequest,
    current_user=Depends(get_current_user)
):
    """
    Links an already-uploaded document to a Company record so the
    Comparison Agent can find it later. Required before a company can
    be included in a /comparison/run request.
    """
    document = await DocumentService.link_company(
        document_id, payload.company_id
    )

    return {
        "document_id": document.document_id,
        "company_id": document.company_id,
    }


@router.get("/company/{company_id}/latest")
async def get_latest_document_for_company(
    company_id: str,
    current_user=Depends(get_current_user)
):
    document = await DocumentService.get_latest_for_company(company_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="No indexed document is linked to this company yet.",
        )

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "status": document.status,
        "created_at": document.created_at,
    }