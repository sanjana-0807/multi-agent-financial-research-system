from fastapi import APIRouter, UploadFile, File, Form, Depends

from core.dependencies import get_current_user
import services.document_service as document_service
from schemas.document_schema import DocumentUploadResponse

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    company_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    return await document_service.upload_document(
        company_id,
        file,
    )