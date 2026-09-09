from fastapi import APIRouter, HTTPException

from services.report_service import ReportService


router = APIRouter(
    prefix="/report",
    tags=["Report"]
)


@router.post("/generate")
async def generate_report(document_id: str):
    return await ReportService.generate(document_id)


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