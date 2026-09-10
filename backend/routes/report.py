from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_current_user
from services.report_service import ReportService


router = APIRouter(
    prefix="/report",
    tags=["Report"]
)


@router.post("/generate")
async def generate_report(
    document_id: str,
    comparison_id: str | None = None,
    current_user=Depends(get_current_user),
):
    return await ReportService.generate(
        document_id,
        current_user,
        comparison_id,
    )


@router.get("/status/{report_id}")
async def get_report_status(report_id: str):
    result = await ReportService.get_status(report_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return result


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    return await ReportService.download(report_id)