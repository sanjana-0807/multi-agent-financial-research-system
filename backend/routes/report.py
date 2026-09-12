# routes/report.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from schemas.report_schema import (
    ReportGenerateRequest,
    ReportResponse,
    ComparisonPreviewResponse,
)
from services import report_service
from core.dependencies import get_current_user

router = APIRouter(prefix="/report", tags=["Report"])


@router.get(
    "/company/{company_id}/available-comparisons",
    response_model=list[ComparisonPreviewResponse],
)
async def get_available_comparisons(
    company_id: str,
    workspace_id: str = Query(..., description="Workspace this company belongs to"),
    current_user=Depends(get_current_user),
):
    """
    Preview which comparisons WOULD be auto-included if you generated
    a report for this company right now -- one entry per distinct
    group of companies compared (e.g. NVDA vs WMT, NVDA vs PEP each
    show up separately), already deduped to the latest run of each
    group. Use the returned comparison_id values in
    ReportGenerateRequest.comparison_ids to hand-pick a subset instead
    of auto-including everything.
    """
    return await report_service.list_available_comparisons(
        company_id=company_id,
        workspace_id=workspace_id,
        current_user=current_user,
    )


@router.post("/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: ReportGenerateRequest,
    current_user=Depends(get_current_user),
):
    """
    Generates a report synchronously and returns it once complete.
    Comparison data is auto-included unless payload.comparison_ids is
    provided. See services/report_service.py for the full flow.
    """
    return await report_service.generate_report(
        company_id=payload.company_id,
        workspace_id=payload.workspace_id,
        current_user=current_user,
        comparison_ids=payload.comparison_ids,
    )


@router.get("/company/{company_id}", response_model=list[ReportResponse])
async def list_reports_for_company(
    company_id: str,
    current_user=Depends(get_current_user),
):
    return await report_service.list_reports_for_company(company_id)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user=Depends(get_current_user),
):
    return await report_service.get_report(report_id)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user=Depends(get_current_user),
):
    pdf_bytes, filename = await report_service.download_report_pdf(report_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    current_user=Depends(get_current_user),
):
    await report_service.delete_report(report_id)