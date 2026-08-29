from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


def create_pdf(filename, report_data):

    document = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8
    )

    content = []

    # Title
    content.append(
        Paragraph("Financial Research Report", title_style)
    )

    # Company Information
    company = report_data.get("Company Name", "Unknown")
    period = report_data.get("Report Period", "Unknown")

    content.append(
        Paragraph(
            f"<b>Company:</b> {company}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Report Period:</b> {period}",
            styles["BodyText"]
        )
    )

    content.append(Spacer(1, 15))

    # Executive Summary
    content.append(
        Paragraph("Executive Summary", heading_style)
    )

    content.append(
        Paragraph(
            report_data.get("Executive Summary", ""),
            styles["BodyText"]
        )
    )

    # Key Financials
    content.append(
        Paragraph("Key Financials", heading_style)
    )

    financials = report_data.get("Key Financials", {})

    table_data = [["Financial Metric", "Value"]]

    for key, value in financials.items():
        table_data.append([key, str(value)])

    financial_table = Table(
        table_data,
        colWidths=[250, 180]
    )

    financial_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ])
    )

    content.append(financial_table)

    # Red Flags
    red_flags = report_data.get("Red Flags", [])

    if red_flags:
        content.append(
            Paragraph("Red Flags", heading_style)
        )

        for flag in red_flags:
            content.append(
                Paragraph(
                    f"• {flag}",
                    styles["BodyText"]
                )
            )

    # Comparison
    comparison = report_data.get("Comparison", {})

    if comparison:
        content.append(
            Paragraph("Comparison", heading_style)
        )

        if isinstance(comparison, dict):

            for key, value in comparison.items():
                content.append(
                    Paragraph(
                        f"<b>{key}:</b> {value}",
                        styles["BodyText"]
                    )
                )

        else:
            content.append(
                Paragraph(
                    str(comparison),
                    styles["BodyText"]
                )
            )

    # Outlook
    outlook = report_data.get("Outlook", "")

    if outlook:
        content.append(
            Paragraph("Outlook", heading_style)
        )

        content.append(
            Paragraph(
                outlook,
                styles["BodyText"]
            )
        )

    document.build(content)