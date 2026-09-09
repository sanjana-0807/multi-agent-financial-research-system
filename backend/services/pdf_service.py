import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Windows Arial supports the ₹ symbol correctly.
pdfmetrics.registerFont(
    TTFont("Arial", r"C:\Windows\Fonts\arial.ttf")
)
pdfmetrics.registerFont(
    TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf")
)

REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "reports"
)

os.makedirs(REPORT_DIR, exist_ok=True)


class PDFService:

    @staticmethod
    def generate(report_data: dict, report_id: str) -> str:

        filename = f"{report_id}.pdf"
        file_path = os.path.join(REPORT_DIR, filename)

        document = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Arial-Bold",
            fontSize=18,
            leading=22,
            alignment=1,
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            "ReportHeading",
            parent=styles["Heading2"],
            fontName="Arial-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontName="Arial",
            fontSize=10,
            leading=14,
            spaceAfter=6,
        )

        small_style = ParagraphStyle(
            "ReportSmall",
            parent=styles["BodyText"],
            fontName="Arial",
            fontSize=9,
            leading=12,
        )

        content = []

        company_name = report_data.get(
            "Company Name",
            "Unknown"
        )

        report_period = report_data.get(
            "Report Period",
            "Unknown"
        )

        content.append(
            Paragraph(
                "Financial Research Report",
                title_style
            )
        )

        content.append(
            Paragraph(
                f"<b>Company:</b> {company_name}",
                body_style
            )
        )

        content.append(
            Paragraph(
                f"<b>Report Period:</b> {report_period}",
                body_style
            )
        )

        content.append(Spacer(1, 8))

        # ---------------------------------------------------------
        # Executive Summary
        # ---------------------------------------------------------
        content.append(
            Paragraph(
                "Executive Summary",
                heading_style
            )
        )

        content.append(
            Paragraph(
                str(
                    report_data.get(
                        "Executive Summary",
                        "Not available"
                    )
                ),
                body_style
            )
        )

        # ---------------------------------------------------------
        # Key Financials
        # ---------------------------------------------------------
        content.append(
            Paragraph(
                "Key Financials",
                heading_style
            )
        )

        financials = report_data.get(
            "Key Financials",
            {}
        )

        financial_rows = [
            ["Metric", "Value"]
        ]

        for key, value in financials.items():
            display_value = (
                "Not available"
                if value is None
                else str(value)
            )

            financial_rows.append(
                [str(key), display_value]
            )

        financial_table = Table(
            financial_rows,
            colWidths=[70 * mm, 90 * mm]
        )

        financial_table.setStyle(
            TableStyle(
                [
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, -1),
                        "Arial",
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Arial-Bold",
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        content.append(financial_table)
        content.append(Spacer(1, 8))

        # ---------------------------------------------------------
        # Red Flags
        # ---------------------------------------------------------
        content.append(
            Paragraph(
                "Red Flags & Risks",
                heading_style
            )
        )

        red_flags = report_data.get(
            "Red Flags",
            []
        )

        if red_flags:
            for flag in red_flags:
                content.append(
                    Paragraph(
                        f"• {flag}",
                        body_style
                    )
                )
        else:
            content.append(
                Paragraph(
                    "• No major financial risks detected.",
                    body_style
                )
            )

        # ---------------------------------------------------------
        # Company Comparison
        # ---------------------------------------------------------
        content.append(
            Paragraph(
                "Company Comparison",
                heading_style
            )
        )

        comparison = report_data.get(
            "Comparison",
            {}
        )

        if comparison:
            if isinstance(comparison, dict):
                for key, value in comparison.items():
                    content.append(
                        Paragraph(
                            f"<b>{key}:</b> {value}",
                            body_style
                        )
                    )
            else:
                content.append(
                    Paragraph(
                        str(comparison),
                        body_style
                    )
                )
        else:
            content.append(
                Paragraph(
                    "Comparison data is not available.",
                    body_style
                )
            )

        # ---------------------------------------------------------
        # Outlook
        # ---------------------------------------------------------
        content.append(
            Paragraph(
                "Outlook",
                heading_style
            )
        )

        content.append(
            Paragraph(
                str(
                    report_data.get(
                        "Outlook",
                        "Not available"
                    )
                ),
                body_style
            )
        )

        # ---------------------------------------------------------
        # Footer
        # ---------------------------------------------------------
        content.append(Spacer(1, 12))

        content.append(
            Paragraph(
                "Generated by Multi-Agent Financial Research System",
                small_style
            )
        )

        document.build(content)

        return file_path