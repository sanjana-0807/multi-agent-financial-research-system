from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from schemas.document_schema import LinkCompanyRequest
from services.document_service import DocumentService
from utils.security import get_current_user


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    company_id: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
):
    """
    Upload and index a PDF document.

    company_id is optional during upload. A document can also
    be linked later using PATCH /documents/{document_id}/link-company.
    """
    result = await DocumentService.process_upload(
        file,
        company_id=company_id,
    )

    return result


# ============================================================
# GET LATEST DOCUMENT FOR COMPANY
# IMPORTANT: Keep this BEFORE /{document_id}
# ============================================================

@router.get("/company/{company_id}/latest")
async def get_latest_document_for_company(
    company_id: str,
    current_user=Depends(get_current_user),
):
    """
    Return the latest indexed document linked to the company.

    The frontend uses this endpoint to determine which
    document_id should be used for extraction, red flags,
    and document-based research.
    """
    document = await DocumentService.get_latest_for_company(
        company_id
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="No indexed document is linked to this company yet.",
        )

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "status": document.status,
        "company_id": document.company_id,
        "created_at": document.created_at,
    }


# ============================================================
# GET DOCUMENT
# ============================================================

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user=Depends(get_current_user),
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
        "updated_at": document.updated_at,
    }


# ============================================================
# GET DOCUMENT CHUNKS
# ============================================================

@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: str,
    current_user=Depends(get_current_user),
):
    return DocumentService.get_chunks(
        document_id
    )


# ============================================================
# LINK DOCUMENT TO COMPANY
# ============================================================

@router.patch("/{document_id}/link-company")
async def link_document_to_company(
    document_id: str,
    payload: LinkCompanyRequest,
    current_user=Depends(get_current_user),
):
    """
    Link an already-uploaded document to a Company record.
    """
    document = await DocumentService.link_company(
        document_id,
        payload.company_id,
    )

    return {
        "document_id": document.document_id,
        "company_id": document.company_id,
    }