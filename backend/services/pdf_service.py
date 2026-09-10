import os
from html import escape

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


# -------------------------------------------------------------
# Fonts
# -------------------------------------------------------------
# Windows Arial supports normal text and the Indian Rupee symbol.
pdfmetrics.registerFont(
    TTFont("Arial", r"C:\Windows\Fonts\arial.ttf")
)

pdfmetrics.registerFont(
    TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf")
)


# -------------------------------------------------------------
# Report output directory
# -------------------------------------------------------------
REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "reports"
)

os.makedirs(REPORT_DIR, exist_ok=True)


class PDFService:

    # ---------------------------------------------------------
    # Formatting helpers
    # ---------------------------------------------------------
    @staticmethod
    def _format_number(value):
        """Format financial numbers for readable PDF display."""

        if value is None:
            return "Not available"

        if isinstance(value, float):
            if value.is_integer():
                return f"{int(value):,}"

            return f"{value:,.2f}"

        if isinstance(value, int):
            return f"{value:,}"

        return str(value)

    @staticmethod
    def _format_ratio(value, ratio_name):
        """Format comparison ratios appropriately."""

        if value is None:
            return "N/A"

        if ratio_name == "net_profit_margin":
            return f"{value:.2f}%"

        if ratio_name == "debt_to_equity":
            return f"{value:.2f}"

        if ratio_name == "eps":
            return f"{value:.2f}"

        return f"{value:,.2f}"

    @staticmethod
    def _metric_display_name(ratio_name):
        """Convert internal metric names into readable report labels."""

        names = {
            "revenue": "Revenue",
            "net_profit": "Net Profit",
            "assets": "Assets",
            "liabilities": "Liabilities",
            "cash_flow": "Cash Flow",
            "eps": "EPS",
            "debt_to_equity": "Debt-to-Equity",
            "net_profit_margin": "Net Profit Margin",
        }

        return names.get(
            ratio_name,
            str(ratio_name).replace("_", " ").title()
        )

    @staticmethod
    def _company_display_name(ticker):
        """Convert common ticker symbols into readable company names."""

        names = {
            "WM": "Walmart",
            "NVDA": "NVIDIA",
            "TSLA": "Tesla",
            "PEP": "PepsiCo",
            "MSFT": "Microsoft",
            "AAPL": "Apple",
            "AMZN": "Amazon",
            "GOOGL": "Alphabet",
            "META": "Meta",
        }

        return names.get(
            str(ticker).upper(),
            str(ticker)
        )

    @staticmethod
    def _add_page_number(canvas, document):
        """Add page number to each PDF page."""

        canvas.saveState()

        canvas.setFont(
            "Arial",
            8
        )

        page_number = canvas.getPageNumber()

        canvas.drawCentredString(
            A4[0] / 2,
            10 * mm,
            f"Page {page_number}"
        )

        canvas.restoreState()

    # ---------------------------------------------------------
    # Comparison section
    # ---------------------------------------------------------
    @staticmethod
    def _build_comparison_section(
        content,
        comparison,
        heading_style,
        body_style,
    ):
        """Render Comparison Agent output as readable analyst tables."""

        if not comparison:
            content.append(
                Paragraph(
                    "Comparison data is not available.",
                    body_style
                )
            )
            return

        if not isinstance(comparison, dict):
            content.append(
                Paragraph(
                    escape(str(comparison)),
                    body_style
                )
            )
            return

        tickers = comparison.get(
            "tickers",
            []
        )

        ratio_comparisons = comparison.get(
            "ratio_comparisons",
            []
        )

        industry_rankings = comparison.get(
            "industry_rankings",
            []
        )

        summary = comparison.get(
            "summary"
        )

        # -----------------------------------------------------
        # Companies Compared
        # -----------------------------------------------------
        if tickers:

            comparison_subheading = ParagraphStyle(
                "ComparisonSubheading",
                parent=heading_style,
                fontName="Arial-Bold",
                fontSize=11,
                leading=14,
                spaceBefore=4,
                spaceAfter=5,
                textColor=colors.HexColor("#374151"),
            )

            content.append(
                Paragraph(
                    "Companies Compared",
                    comparison_subheading
                )
            )

            company_names = [
                PDFService._company_display_name(ticker)
                for ticker in tickers
            ]

            company_text = " vs ".join(
                escape(str(name))
                for name in company_names
            )

            content.append(
                Paragraph(
                    company_text,
                    body_style
                )
            )

        # -----------------------------------------------------
        # Financial Comparison Table
        # -----------------------------------------------------
        if ratio_comparisons and len(tickers) >= 2:

            first_ticker = tickers[0]
            second_ticker = tickers[1]

            first_company = PDFService._company_display_name(
                first_ticker
            )

            second_company = PDFService._company_display_name(
                second_ticker
            )

            comparison_rows = [
                [
                    "Financial Metric",
                    first_company,
                    second_company,
                    "Industry Avg.",
                    "Better",
                ]
            ]

            for item in ratio_comparisons:

                if not isinstance(item, dict):
                    continue

                ratio_name = item.get(
                    "ratio_name",
                    "Metric"
                )

                values = item.get(
                    "values",
                    {}
                )

                first_value = values.get(
                    first_ticker
                )

                second_value = values.get(
                    second_ticker
                )

                industry_average = item.get(
                    "industry_average"
                )

                best_performer = item.get(
                    "best_performer"
                )

                display_name = (
                    PDFService._metric_display_name(
                        ratio_name
                    )
                )

                if industry_average is None:
                    industry_display = "N/A"
                else:
                    industry_display = (
                        PDFService._format_ratio(
                            industry_average,
                            ratio_name
                        )
                    )

                if best_performer:
                    better_company = (
                        PDFService._company_display_name(
                            best_performer
                        )
                    )
                else:
                    better_company = "N/A"

                comparison_rows.append(
                    [
                        display_name,
                        PDFService._format_ratio(
                            first_value,
                            ratio_name
                        ),
                        PDFService._format_ratio(
                            second_value,
                            ratio_name
                        ),
                        industry_display,
                        better_company,
                    ]
                )

            comparison_table = Table(
                comparison_rows,
                colWidths=[
                    39 * mm,
                    27 * mm,
                    27 * mm,
                    29 * mm,
                    35 * mm,
                ],
                repeatRows=1,
            )

            comparison_table.setStyle(
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
                            colors.HexColor("#1F2937"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#CBD5E1"),
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "ALIGN",
                            (1, 1),
                            (-1, -1),
                            "CENTER",
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            7.8,
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            content.append(
                Spacer(1, 4)
            )

            content.append(
                comparison_table
            )

        # -----------------------------------------------------
        # Industry Ranking
        # -----------------------------------------------------
        if industry_rankings:

            ranking_subheading = ParagraphStyle(
                "RankingSubheading",
                parent=heading_style,
                fontName="Arial-Bold",
                fontSize=11,
                leading=14,
                spaceBefore=8,
                spaceAfter=5,
                textColor=colors.HexColor("#374151"),
            )

            content.append(
                Spacer(1, 8)
            )

            content.append(
                Paragraph(
                    "Industry Ranking",
                    ranking_subheading
                )
            )

            ranking_rows = [
                [
                    "Rank",
                    "Company",
                    "Score",
                ]
            ]

            sorted_rankings = sorted(
                industry_rankings,
                key=lambda item: (
                    item.get(
                        "rank",
                        999
                    )
                    if isinstance(item, dict)
                    else 999
                ),
            )

            for ranking in sorted_rankings:

                if not isinstance(ranking, dict):
                    continue

                rank = ranking.get(
                    "rank",
                    "N/A"
                )

                ticker = ranking.get(
                    "ticker",
                    "N/A"
                )

                score = ranking.get(
                    "score"
                )

                company_name = (
                    PDFService._company_display_name(
                        ticker
                    )
                )

                if isinstance(
                    score,
                    (int, float)
                ):
                    display_score = f"{score:.1f}"
                else:
                    display_score = "N/A"

                ranking_rows.append(
                    [
                        str(rank),
                        company_name,
                        display_score,
                    ]
                )

            ranking_table = Table(
                ranking_rows,
                colWidths=[
                    30 * mm,
                    75 * mm,
                    45 * mm,
                ],
                repeatRows=1,
            )

            ranking_table.setStyle(
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
                            colors.HexColor("#1F2937"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#CBD5E1"),
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "ALIGN",
                            (0, 0),
                            (0, -1),
                            "CENTER",
                        ),
                        (
                            "ALIGN",
                            (2, 0),
                            (2, -1),
                            "CENTER",
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
                            5,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            content.append(
                ranking_table
            )

        # -----------------------------------------------------
        # Comparison Summary
        # -----------------------------------------------------
        if summary:

            summary_subheading = ParagraphStyle(
                "SummarySubheading",
                parent=heading_style,
                fontName="Arial-Bold",
                fontSize=11,
                leading=14,
                spaceBefore=8,
                spaceAfter=5,
                textColor=colors.HexColor("#374151"),
            )

            content.append(
                Spacer(1, 8)
            )

            content.append(
                Paragraph(
                    "Comparison Summary",
                    summary_subheading
                )
            )

            content.append(
                Paragraph(
                    escape(str(summary)),
                    body_style
                )
            )

    # ---------------------------------------------------------
    # Main PDF generation
    # ---------------------------------------------------------
    @staticmethod
    def generate(
        report_data: dict,
        report_id: str
    ) -> str:

        filename = f"{report_id}.pdf"

        file_path = os.path.join(
            REPORT_DIR,
            filename
        )

        document = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()

        # -----------------------------------------------------
        # Styles
        # -----------------------------------------------------
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Arial-Bold",
            fontSize=20,
            leading=24,
            alignment=1,
            spaceAfter=10,
            textColor=colors.HexColor("#111827"),
        )

        company_style = ParagraphStyle(
            "CompanyName",
            parent=styles["Heading2"],
            fontName="Arial-Bold",
            fontSize=14,
            leading=18,
            alignment=1,
            spaceAfter=5,
            textColor=colors.HexColor("#374151"),
        )

        period_style = ParagraphStyle(
            "ReportPeriod",
            parent=styles["BodyText"],
            fontName="Arial",
            fontSize=10,
            leading=14,
            alignment=1,
            spaceAfter=12,
            textColor=colors.HexColor("#6B7280"),
        )

        heading_style = ParagraphStyle(
            "ReportHeading",
            parent=styles["Heading2"],
            fontName="Arial-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=7,
            textColor=colors.HexColor("#111827"),
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontName="Arial",
            fontSize=10,
            leading=14,
            spaceAfter=6,
            textColor=colors.HexColor("#374151"),
        )

        small_style = ParagraphStyle(
            "ReportSmall",
            parent=styles["BodyText"],
            fontName="Arial",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#6B7280"),
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

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------
        content.append(
            Spacer(1, 8)
        )

        content.append(
            Paragraph(
                "Financial Research Report",
                title_style
            )
        )

        content.append(
            Paragraph(
                escape(str(company_name)),
                company_style
            )
        )

        content.append(
            Paragraph(
                f"Report Period: {escape(str(report_period))}",
                period_style
            )
        )

        # -----------------------------------------------------
        # Executive Summary
        # -----------------------------------------------------
        content.append(
            Paragraph(
                "Executive Summary",
                heading_style
            )
        )

        executive_summary = report_data.get(
            "Executive Summary",
            "Not available"
        )

        content.append(
            Paragraph(
                escape(str(executive_summary)),
                body_style
            )
        )

        # -----------------------------------------------------
        # Key Financials
        # -----------------------------------------------------
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
            [
                "Metric",
                "Value",
            ]
        ]

        if isinstance(
            financials,
            dict
        ):

            for key, value in financials.items():

                financial_rows.append(
                    [
                        str(key),
                        PDFService._format_number(
                            value
                        ),
                    ]
                )

        financial_table = Table(
            financial_rows,
            colWidths=[
                70 * mm,
                80 * mm,
            ],
            repeatRows=1,
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
                        colors.HexColor("#1F2937"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
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
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        content.append(
            financial_table
        )

        # -----------------------------------------------------
        # Red Flags & Risks
        # -----------------------------------------------------
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
                        f"&bull; {escape(str(flag))}",
                        body_style
                    )
                )

        else:

            content.append(
                Paragraph(
                    "&bull; No major financial risks detected.",
                    body_style
                )
            )

        # -----------------------------------------------------
        # Company Comparison
        # -----------------------------------------------------
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

        PDFService._build_comparison_section(
            content,
            comparison,
            heading_style,
            body_style,
        )

        # -----------------------------------------------------
        # Outlook
        # -----------------------------------------------------
        content.append(
            Paragraph(
                "Outlook",
                heading_style
            )
        )

        outlook = report_data.get(
            "Outlook",
            "Not available"
        )

        content.append(
            Paragraph(
                escape(str(outlook)),
                body_style
            )
        )

        # -----------------------------------------------------
        # Footer
        # -----------------------------------------------------
        content.append(
            Spacer(1, 14)
        )

        content.append(
            Paragraph(
                "Generated by Multi-Agent Financial Research System",
                small_style
            )
        )

        # -----------------------------------------------------
        # Build PDF
        # -----------------------------------------------------
        document.build(
            content,
            onFirstPage=PDFService._add_page_number,
            onLaterPages=PDFService._add_page_number,
        )

        return file_path