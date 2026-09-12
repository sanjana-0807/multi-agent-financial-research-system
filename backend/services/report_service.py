# services/report_service.py
"""
Orchestrates the Report Agent.

Pulls already-computed results from Extraction (run live -- there is
no persisted metrics store in this project, see
agents/comparison_agent/data_fetcher.py), Red Flag, and Comparison
agents, asks the Report Agent's LLM step to write the Executive
Summary + Outlook, renders a PDF with reportlab, and stores it in
GridFS. A generated report is a snapshot: once rendered, its numbers
are frozen even if extraction or comparisons are re-run afterward.
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from beanie.operators import In
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from starlette.concurrency import run_in_threadpool

from database import mongo_client
from config.settings import settings

from models.company import Company
from models.red_flag import RedFlagResult
from models.comparison_result import ComparisonResult
from models.report import Report, ReportComparisonRef, ReportSectionStatus
from models.user import User

from schemas.report_schema import ReportResponse

from agents.comparison_agent.data_fetcher import get_latest_document_for_company
from agents.extraction_agent.document_fetcher import fetch_document_text
from agents.extraction_agent.tasks import run_extraction

from agents.report_agent.crew import run_report_narrative
from agents.report_agent.report_builder import build_report_pdf
from schemas.report_schema import ComparisonPreviewResponse

def _to_response(report: Report) -> ReportResponse:
    data = report.model_dump()
    data["id"] = str(report.id)
    data["workspace_id"] = str(report.workspace_id)
    data["company_id"] = str(report.company_id)
    return ReportResponse.model_validate(data)


def _gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    db = mongo_client.client[settings.DATABASE_NAME]
    return AsyncIOMotorGridFSBucket(db)


async def _resolve_company(company_id: str, workspace) -> Company:
    try:
        obj_id = PydanticObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid company id '{company_id}'")

    company = await Company.get(obj_id)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
    if company.workspace_id != workspace.id:
        raise HTTPException(
            status_code=403,
            detail=f"Company '{company_id}' does not belong to this workspace",
        )
    return company


async def _get_red_flags(document_id: str) -> Optional[RedFlagResult]:
    return await RedFlagResult.find(
        RedFlagResult.document_id == document_id,
    ).sort("-created_at").first_or_none()


async def _auto_include_comparisons(company: Company) -> list[ComparisonResult]:
    """
    Every completed comparison this company was part of, deduped by
    the exact set of companies compared (keeps the latest run of each
    group -- handles a pair being re-run, and keeps a 5-way comparison
    and its component 2-way comparisons as separate groups, since
    they're different sets of companies).

    Shared by _get_comparisons() (used during report generation) and
    list_available_comparisons() (used to preview options before
    generating), so both always agree on what "available" means.
    """
    all_results = await ComparisonResult.find(
        In(ComparisonResult.company_ids, [company.id]),
        ComparisonResult.status == "completed",
    ).to_list()

    latest_by_group: dict[frozenset, ComparisonResult] = {}
    for result in all_results:
        group_key = frozenset(str(cid) for cid in result.company_ids)
        existing = latest_by_group.get(group_key)
        candidate_time = result.completed_at or result.created_at
        existing_time = existing.completed_at or existing.created_at if existing else None
        if existing is None or candidate_time > existing_time:
            latest_by_group[group_key] = result

    return list(latest_by_group.values())


async def _get_comparisons(
    company: Company,
    comparison_ids: Optional[list[str]],
) -> list[ComparisonResult]:
    if comparison_ids:
        results = []
        for cid in comparison_ids:
            try:
                obj_id = PydanticObjectId(cid)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid comparison id '{cid}'")
            result = await ComparisonResult.get(obj_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Comparison '{cid}' not found")
            if company.id not in result.company_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Comparison '{cid}' does not include company '{company.id}'",
                )
            results.append(result)
        return results

    return await _auto_include_comparisons(company)


async def list_available_comparisons(
    company_id: str,
    workspace_id: str,
    current_user: "User",
) -> list["ComparisonPreviewResponse"]:
    """
    Read-only preview: shows exactly which comparisons WOULD be
    auto-included if generate_report() were called for this company
    right now, without generating anything. Lets the frontend show a
    picklist so a comparison_id passed to /report/generate is never
    guessed blind.
    """
    from schemas.report_schema import ComparisonPreviewResponse

    from services.workspace_service import get_workspace
    workspace = await get_workspace(workspace_id, current_user)
    company = await _resolve_company(company_id, workspace)

    comparisons = await _auto_include_comparisons(company)
    comparisons.sort(
        key=lambda c: c.completed_at or c.created_at, reverse=True
    )

    return [
        ComparisonPreviewResponse(
            comparison_id=str(c.id),
            tickers=c.tickers,
            status=c.status,
            completed_at=c.completed_at,
        )
        for c in comparisons
    ]


async def generate_report(
    company_id: str,
    workspace_id: str,
    current_user: "User",
    comparison_ids: Optional[list[str]] = None,
) -> ReportResponse:
    from services.workspace_service import get_workspace

    workspace = await get_workspace(workspace_id, current_user)
    company = await _resolve_company(company_id, workspace)

    # 1. Resolve the company's document -- reuses the exact same
    # helper Comparison Agent uses, so document-selection behavior
    # (latest indexed document) stays in one place.
    document = await get_latest_document_for_company(company)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"No processed document is linked to '{company.ticker}'. "
                "Upload and link a document before generating a report."
            ),
        )

    document_text = fetch_document_text(document.document_id)
    if document_text is None:
        raise HTTPException(
            status_code=422,
            detail=f"Document '{document.document_id}' has no indexed text.",
        )

    report = Report(
        workspace_id=workspace.id,
        company_id=company.id,
        company_name=company.name,
        ticker=company.ticker,
        document_id=document.document_id,
        fiscal_year=0,
        filename=f"{company.ticker}_report.pdf",
        status="generating",
    )
    await report.insert()

    try:
        # 2. Key Financials -- live extraction (Option A: not
        # persisted, matches Comparison Agent's own convention).
        # run_extraction() is a blocking, synchronous call into Ollama
        # -- wrapped in a threadpool so it never blocks the event
        # loop (data_fetcher.py calls it directly today; wrapping it
        # here is a deliberate improvement local to this new code
        # path, not a change to existing behavior).
        extraction = await run_in_threadpool(
            run_extraction, document_text, document_id=document.document_id
        )
        report.fiscal_year = extraction.get("fiscal_year") or 0

        # 3. Red Flags -- required section, but the report still
        # generates without it; section_status records whether it
        # was actually available.
        red_flags = await _get_red_flags(document.document_id)
        section_status = ReportSectionStatus(
            key_financials=extraction.get("revenue") is not None,
            red_flags=red_flags is not None,
        )

        # 4. Company Comparison -- optional. Auto-includes every
        # completed comparison involving this company unless specific
        # comparison_ids were requested.
        comparisons = await _get_comparisons(company, comparison_ids)
        section_status.company_comparison = len(comparisons) > 0

        report.comparisons_included = [
            ReportComparisonRef(comparison_id=str(c.id), tickers=c.tickers)
            for c in comparisons
        ]
        report.section_status = section_status

        # 5. Executive Summary + Outlook -- the LLM only ever sees
        # already-computed data, never the raw document.
        narrative = await run_report_narrative(
            company=company,
            extraction=extraction,
            red_flags=red_flags,
            comparisons=comparisons,
        )
        report.executive_summary = narrative.get("executive_summary")
        report.outlook = narrative.get("outlook")

        # 6. Render PDF
        pdf_bytes = build_report_pdf(
            company=company,
            extraction=extraction,
            red_flags=red_flags,
            comparisons=comparisons,
            executive_summary=report.executive_summary,
            outlook=report.outlook,
        )

        # 7. Store in GridFS (Atlas)
        bucket = _gridfs_bucket()
        file_id = await bucket.upload_from_stream(report.filename, pdf_bytes)

        report.gridfs_file_id = str(file_id)
        report.status = "completed"
        report.completed_at = datetime.now(timezone.utc)
        await report.save()

    except HTTPException:
        report.status = "failed"
        report.error_message = "Report generation failed during validation"
        await report.save()
        raise
    except Exception as exc:
        import traceback

        traceback.print_exc()

        report.status = "failed"
        report.error_message = str(exc)
        await report.save()

        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {type(exc).__name__}: {exc}",
        )

    return _to_response(report)


async def get_report(report_id: str) -> ReportResponse:
    try:
        obj_id = PydanticObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report id")

    report = await Report.get(obj_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(report)


async def list_reports_for_company(company_id: str) -> list[ReportResponse]:
    try:
        obj_id = PydanticObjectId(company_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    reports = await Report.find(
        Report.company_id == obj_id,
    ).sort("-created_at").to_list()
    return [_to_response(r) for r in reports]


async def download_report_pdf(report_id: str) -> tuple[bytes, str]:
    try:
        obj_id = PydanticObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report id")

    report = await Report.get(obj_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "completed" or not report.gridfs_file_id:
        raise HTTPException(
            status_code=409,
            detail=f"Report is '{report.status}', not ready for download",
        )

    bucket = _gridfs_bucket()
    stream = await bucket.open_download_stream(ObjectId(report.gridfs_file_id))
    pdf_bytes = await stream.read()
    return pdf_bytes, report.filename


async def delete_report(report_id: str) -> None:
    try:
        obj_id = PydanticObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report id")

    report = await Report.get(obj_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.gridfs_file_id:
        bucket = _gridfs_bucket()
        try:
            await bucket.delete(ObjectId(report.gridfs_file_id))
        except Exception:
            pass  # file may already be gone; don't block metadata deletion

    await report.delete()