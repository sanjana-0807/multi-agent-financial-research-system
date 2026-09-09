from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.responses import FileResponse

from models.report import Report
from services.research_service import ResearchService
from services.pdf_service import PDFService


class ReportService:

    @staticmethod
    async def generate(document_id: str):

        # ---------------------------------------------------------
        # 1. Get Extraction Agent output
        # ---------------------------------------------------------
        extraction = ResearchService.extract(document_id)

        # ResearchService returns a dictionary.
        # Therefore, use dictionary access instead of extraction.company.
        company_name = extraction.get("company", "Unknown")
        fiscal_year = extraction.get("fiscal_year", 0)

        # ---------------------------------------------------------
        # 2. Get Red Flag Agent output
        # ---------------------------------------------------------
        red_flags_data = ResearchService.red_flags(document_id)
        red_flags = red_flags_data.get("red_flags", [])

        # ---------------------------------------------------------
        # 3. Build extracted financial data
        # ---------------------------------------------------------
        extracted_data = {
            "summary": (
                f"{company_name} showed financial performance "
                f"for FY{fiscal_year}."
            ),
            "financials": {
                "Revenue": extraction.get("revenue"),
                "Profit": extraction.get("net_profit"),
                "Assets": extraction.get("assets"),
                "Liabilities": extraction.get("liabilities"),
                "Cash Flow": extraction.get("cash_flow"),
                "EPS": extraction.get("eps"),
            },
            "outlook": "Financial outlook requires further analysis.",
        }

        report_period = f"FY{fiscal_year}"

        # ---------------------------------------------------------
        # 4. Comparison Agent integration point
        # ---------------------------------------------------------
        # The Comparison Agent belongs to another team member.
        # Do not implement or duplicate it here.
        #
        # The existing team integration can provide comparison data
        # through this field later.
        comparison_data = {}

        # ---------------------------------------------------------
        # 5. Build structured report
        # ---------------------------------------------------------
        report_data = {
            "Company Name": company_name,
            "Report Period": report_period,
            "Executive Summary": extracted_data["summary"],
            "Key Financials": extracted_data["financials"],
            "Red Flags": red_flags,
            "Comparison": comparison_data,
            "Outlook": extracted_data["outlook"],
        }

        # ---------------------------------------------------------
        # 6. Validate required report sections
        # ---------------------------------------------------------
        if not report_data["Company Name"]:
            raise HTTPException(
                status_code=400,
                detail="Company name is missing."
            )

        if not report_data["Report Period"]:
            raise HTTPException(
                status_code=400,
                detail="Report period is missing."
            )

        if not report_data["Executive Summary"]:
            raise HTTPException(
                status_code=400,
                detail="Executive summary is missing."
            )

        if not report_data["Key Financials"]:
            raise HTTPException(
                status_code=400,
                detail="Financial data is missing."
            )

        # ---------------------------------------------------------
        # 7. Generate report ID
        # ---------------------------------------------------------
        report_id = "R" + datetime.now().strftime("%Y%m%d%H%M%S")

        # ---------------------------------------------------------
        # 8. Save structured report to MongoDB
        # ---------------------------------------------------------
        report = Report(
            report_id=report_id,
            company_name=company_name,
            report_period=report_period,
            executive_summary=report_data["Executive Summary"],
            key_financials=report_data["Key Financials"],
            red_flags=red_flags,
            comparison=comparison_data,
            outlook=report_data["Outlook"],
            status="completed",
            created_at=datetime.now(timezone.utc),
        )

        await report.insert()

        # ---------------------------------------------------------
        # 9. Generate PDF report
        # ---------------------------------------------------------
        try:
            pdf_path = PDFService.generate(
                report_data,
                report_id
            )

            report.pdf_path = pdf_path
            await report.save()

        except Exception as exc:
            report.status = "completed"
            report.error = f"PDF generation failed: {str(exc)}"
            await report.save()

            raise HTTPException(
                status_code=500,
                detail=f"Report created, but PDF generation failed: {str(exc)}"
            )

        # ---------------------------------------------------------
        # 10. Return structured report response
        # ---------------------------------------------------------
        return {
            "report_id": report_id,
            "status": "completed",
            "pdf_available": True,
            "report": {
                "title": (
                    f"{company_name} - Comprehensive Financial Analysis Report "
                    f"({report_period})"
                ),
                "generated_at": datetime.now(timezone.utc).strftime(
                    "%B %d, %Y"
                ),
                "summary": report_data["Executive Summary"],
                "sections": [
                    {
                        "heading": "Key Financials",
                        "content": str(
                            report_data["Key Financials"]
                        ),
                    },
                    {
                        "heading": "Red Flags & Risks",
                        "content": str(red_flags),
                    },
                    {
                        "heading": "Company Comparison",
                        "content": str(comparison_data),
                    },
                    {
                        "heading": "Outlook",
                        "content": report_data["Outlook"],
                    },
                ],
            },
        }

    @staticmethod
    async def get_status(report_id: str):

        report = await Report.find_one(
            Report.report_id == report_id
        )

        if not report:
            return None

        return {
            "report_id": report.report_id,
            "status": report.status,
            "pdf_available": bool(report.pdf_path),
            "report": {
                "title": (
                    f"{report.company_name} - Comprehensive Financial Analysis Report "
                    f"({report.report_period})"
                ),
                "generated_at": report.created_at.strftime(
                    "%B %d, %Y"
                ),
                "summary": report.executive_summary,
                "sections": [
                    {
                        "heading": "Key Financials",
                        "content": str(report.key_financials),
                    },
                    {
                        "heading": "Red Flags & Risks",
                        "content": str(report.red_flags),
                    },
                    {
                        "heading": "Company Comparison",
                        "content": str(report.comparison),
                    },
                    {
                        "heading": "Outlook",
                        "content": report.outlook or "",
                    },
                ],
            },
        }

    @staticmethod
    async def download(report_id: str):

        report = await Report.find_one(
            Report.report_id == report_id
        )

        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )

        if not report.pdf_path:
            raise HTTPException(
                status_code=404,
                detail="PDF report is not available"
            )

        return FileResponse(
            path=report.pdf_path,
            media_type="application/pdf",
            filename=f"{report.report_id}.pdf",
        )