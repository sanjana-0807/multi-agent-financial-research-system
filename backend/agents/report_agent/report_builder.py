"""Analyst-style financial research PDF builder.

The builder focuses on editorial layout, predictable alignment and compact use of
page space. Financial reasoning remains outside this module; this file only
presents the already-computed report data.
"""
from io import BytesIO
from typing import Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether,
)

from models.company import Company
from models.red_flag import RedFlagResult
from models.comparison_result import ComparisonResult
from agents.report_agent.section_templates import (
    financials_table_rows,
    financial_kpis,
    red_flags_rows,
    comparison_sections,
)

# -----------------------------------------------------------------------------
# Editorial palette: mostly neutral, with purple used only for the company.
# -----------------------------------------------------------------------------
NAVY = colors.HexColor("#3F4652")
INK = colors.HexColor("#1F2937")
SLATE = colors.HexColor("#64748B")
MUTED = colors.HexColor("#94A3B8")
LIGHT = colors.HexColor("#F8FAFC")
LIGHTER = colors.HexColor("#FBFCFE")
BORDER = colors.HexColor("#D9E0E8")
WHITE = colors.white
PURPLE = colors.HexColor("#6D3FD3")
PURPLE_LIGHT = colors.HexColor("#F4F0FF")
TEAL = colors.HexColor("#0F8FA8")
CORAL = colors.HexColor("#E66A55")
GOLD = colors.HexColor("#C99A1A")
GREEN = colors.HexColor("#18845F")
GREEN_LIGHT = colors.HexColor("#ECFDF5")
RED = colors.HexColor("#B93845")
RED_LIGHT = colors.HexColor("#FFF1F2")
AMBER = colors.HexColor("#B7791F")
AMBER_LIGHT = colors.HexColor("#FFF8E7")

PAGE_W, PAGE_H = letter
CONTENT_W = 7.0 * inch


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(
        name="TitleX", fontName="Helvetica-Bold", fontSize=24, leading=27,
        textColor=NAVY, spaceAfter=2,
    ))
    s.add(ParagraphStyle(
        name="TickerX", fontName="Helvetica-Bold", fontSize=10, leading=13,
        textColor=PURPLE, spaceAfter=2,
    ))
    s.add(ParagraphStyle(
        name="SubX", fontName="Helvetica", fontSize=8.5, leading=11,
        textColor=SLATE, spaceAfter=8,
    ))
    s.add(ParagraphStyle(
        name="H1X", fontName="Helvetica-Bold", fontSize=15, leading=18,
        textColor=NAVY, spaceBefore=7, spaceAfter=6,
    ))
    s.add(ParagraphStyle(
        name="H2X", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
        textColor=INK, spaceBefore=3, spaceAfter=4,
    ))
    s.add(ParagraphStyle(
        name="BodyX", fontName="Helvetica", fontSize=9.2, leading=13.3,
        textColor=INK, spaceAfter=5,
    ))
    s.add(ParagraphStyle(
        name="BodyTight", fontName="Helvetica", fontSize=8.5, leading=11.5,
        textColor=INK,
    ))
    s.add(ParagraphStyle(
        name="SmallX", fontName="Helvetica", fontSize=7.2, leading=9.2,
        textColor=SLATE,
    ))
    s.add(ParagraphStyle(
        name="TinyX", fontName="Helvetica", fontSize=6.4, leading=8,
        textColor=MUTED,
    ))
    s.add(ParagraphStyle(
        name="THX", fontName="Helvetica-Bold", fontSize=7.7, leading=9,
        textColor=INK,
    ))
    s.add(ParagraphStyle(
        name="TCX", fontName="Helvetica", fontSize=8.2, leading=10.5,
        textColor=INK,
    ))
    s.add(ParagraphStyle(
        name="TCBX", fontName="Helvetica-Bold", fontSize=8.2, leading=10.5,
        textColor=INK,
    ))
    s.add(ParagraphStyle(
        name="LabelX", fontName="Helvetica-Bold", fontSize=7, leading=8,
        textColor=SLATE,
    ))
    s.add(ParagraphStyle(
        name="ValueX", fontName="Helvetica-Bold", fontSize=13, leading=14,
        textColor=NAVY,
    ))
    return s


def _p(text, style):
    return Paragraph(escape(str(text or "")), style)


def _rich(text, style):
    return Paragraph(str(text or ""), style)


def _line(width=CONTENT_W, color=BORDER, thickness=0.55, before=0, after=5):
    t = Table([[""]], colWidths=[width], rowHeights=[0.01 * inch])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), thickness, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), before),
        ("BOTTOMPADDING", (0, 0), (-1, -1), after),
    ]))
    return t


def _section_heading(title, styles, kicker=None):
    parts = []
    if kicker:
        parts.append(_rich(
            f'<font color="{PURPLE.hexval()}"><b>{escape(kicker.upper())}</b></font>',
            styles["TinyX"],
        ))
        parts.append(Spacer(1, 1))
    parts.append(Paragraph(escape(title), styles["H1X"]))
    return parts


def _kpi_strip(kpis, styles):
    """Four aligned values; intentionally no boxes or vertical separators."""
    n = min(len(kpis), 4)
    widths = [CONTENT_W / n] * n
    cells = []
    for i, k in enumerate(kpis[:4]):
        cells.append([
            _p(k.get("label", ""), styles["LabelX"]),
            _p(k.get("value", ""), styles["ValueX"]),
        ])
    t = Table([cells], colWidths=widths, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    # A single subtle baseline instead of individual card borders.
    cmds.append(("LINEBELOW", (0, 0), (-1, -1), 1.4, PURPLE))
    t.setStyle(TableStyle(cmds))
    return t


def _table(data, widths, header=True, align_right_cols=None):
    align_right_cols = align_right_cols or []
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, BORDER),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF1F4"))]
    for r in range(1 if header else 0, len(data)):
        if r % 2 == 0:
            cmds.append(("BACKGROUND", (0, r), (-1, r), LIGHTER))
        cmds.append(("LINEBELOW", (0, r), (-1, r), 0.35, BORDER))
    for c in align_right_cols:
        cmds.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(cmds))
    return t


def _metric_bars(title, metrics, width=3.36 * inch, height=1.48 * inch):
    """Small editorial bar chart for page 1; no axes/grid clutter."""
    d = Drawing(width, height)
    vals = [(str(label), float(value)) for label, value in metrics if value is not None]
    if not vals:
        return d
    max_v = max(v for _, v in vals) or 1.0
    d.add(String(0, height - 9, title.upper(), fontName="Helvetica-Bold", fontSize=7.4, fillColor=NAVY))
    plot_x = 78
    plot_w = width - 128
    row_h = 21
    base_y = height - 28
    for i, (label, value) in enumerate(vals[:5]):
        y = base_y - i * row_h
        d.add(String(0, y + 1, label, fontName="Helvetica-Bold", fontSize=6.7, fillColor=SLATE))
        d.add(Line(plot_x, y, plot_x + plot_w, y, strokeColor=BORDER, strokeWidth=1.0))
        bw = max(2, plot_w * value / max_v)
        d.add(Rect(plot_x, y - 2.5, bw, 5, fillColor=PURPLE, strokeColor=PURPLE))
        suffix = ""
        if abs(value) >= 1000:
            text = f"${value / 1000:.1f}B"
        else:
            text = f"${value:,.0f}M"
        d.add(String(plot_x + plot_w + 5, y - 2.2, text, fontName="Helvetica-Bold", fontSize=6.6, fillColor=INK))
    return d


def _balance_chart(extraction, width=3.36 * inch, height=1.48 * inch):
    assets = extraction.get("assets")
    liabilities = extraction.get("liabilities")
    d = Drawing(width, height)
    d.add(String(0, height - 9, "BALANCE SHEET", fontName="Helvetica-Bold", fontSize=7.4, fillColor=NAVY))
    vals = [("Assets", assets), ("Liabilities", liabilities)]
    nums = [float(v) for _, v in vals if isinstance(v, (int, float))]
    mx = max(nums) if nums else 1.0
    plot_x, plot_w = 78, width - 128
    for i, (label, value) in enumerate(vals):
        y = height - 31 - i * 27
        d.add(String(0, y + 1, label, fontName="Helvetica-Bold", fontSize=6.7, fillColor=SLATE))
        d.add(Line(plot_x, y, plot_x + plot_w, y, strokeColor=BORDER, strokeWidth=1.0))
        if isinstance(value, (int, float)):
            bw = max(2, plot_w * float(value) / mx)
            fill = NAVY if label == "Assets" else SLATE
            d.add(Rect(plot_x, y - 3, bw, 6, fillColor=fill, strokeColor=fill))
            d.add(String(plot_x + plot_w + 5, y - 2.5, f"${float(value)/1000:.1f}B", fontName="Helvetica-Bold", fontSize=6.6, fillColor=INK))
    return d


def _financial_snapshot(extraction, fy, styles):
    rows = [[_p("Financial metric", styles["THX"]), _p(f"FY {fy}", styles["THX"]), _p("Reading", styles["THX"])]]
    data = dict(financials_table_rows(extraction))
    readings = {
        "Revenue": "Scale",
        "Net Profit": "Earnings",
        "Total Assets": "Asset base",
        "Total Liabilities": "Obligations",
        "Cash Flow": "Cash generation",
        "EPS": "Per-share earnings",
        "Net Profit Margin": "Profitability",
        "Debt-to-Equity": "Leverage",
        "Current Ratio": "Liquidity",
    }
    for metric, value in financials_table_rows(extraction):
        rows.append([_p(metric, styles["TCBX"]), _p(value, styles["TCX"]), _p(readings.get(metric, ""), styles["SmallX"])])
    return _table(rows, [2.55 * inch, 1.55 * inch, 2.9 * inch], align_right_cols=[1])


def _risk_color(sev):
    sev = str(sev or "").upper()
    if sev == "HIGH":
        return RED, RED_LIGHT
    if sev == "MEDIUM":
        return AMBER, AMBER_LIGHT
    return GREEN, GREEN_LIGHT



def _risk_severity_chart(flags, width=6.72 * inch, height=0.78 * inch):
    d = Drawing(width, height)
    counts = {
        "HIGH": sum(1 for sev, _, _ in flags if str(sev).upper() == "HIGH"),
        "MEDIUM": sum(1 for sev, _, _ in flags if str(sev).upper() == "MEDIUM"),
        "OTHER": sum(1 for sev, _, _ in flags if str(sev).upper() not in {"HIGH", "MEDIUM"}),
    }
    total = sum(counts.values()) or 1
    d.add(String(0, height - 9, "RISK CONCENTRATION", fontName="Helvetica-Bold", fontSize=7.4, fillColor=NAVY))
    x = 0
    bar_y = 19
    bar_w = width
    for label, value, color in [("HIGH", counts["HIGH"], RED), ("MEDIUM", counts["MEDIUM"], AMBER), ("OTHER", counts["OTHER"], GREEN)]:
        seg = bar_w * value / total
        if value:
            d.add(Rect(x, bar_y, max(seg, 3), 9, fillColor=color, strokeColor=color))
            d.add(String(x + max(seg, 3) / 2, bar_y + 12, f"{label} {value}", fontName="Helvetica-Bold", fontSize=6.4, fillColor=color, textAnchor="middle"))
        x += seg
    return d


def _benchmark_readout(section, target, styles):
    """Deterministic peer readout derived only from the comparison values."""
    tickers = section.get("tickers", []) or []
    rows = section.get("rows", []) or []
    if len(tickers) < 2 or not rows:
        return None
    a, b = tickers[0], tickers[1]
    a_leads, b_leads = [], []
    for row in rows:
        vals = row.get("raw_values", {}) or {}
        va, vb = vals.get(a), vals.get(b)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            metric = str(row.get("ratio", "Metric")).replace("_", " ").title()
            if va > vb:
                a_leads.append(metric)
            elif vb > va:
                b_leads.append(metric)
    def compact(items):
        if not items:
            return "None"
        return ", ".join(items[:4]) + (f" +{len(items)-4}" if len(items) > 4 else "")
    data = [
        [_p("Peer", styles["THX"]), _p("Higher reported value", styles["THX"])],
        [_p(a, styles["TCBX"]), _p(compact(a_leads), styles["TCX"])],
        [_p(b, styles["TCBX"]), _p(compact(b_leads), styles["TCX"])],
    ]
    return _table(data, [1.0 * inch, 5.72 * inch])


def _benchmark_average_table(section, styles):
    rows = section.get("rows", []) or []
    if not rows:
        return None
    data = [[_p("Metric", styles["THX"]), _p("Industry average", styles["THX"]), _p("Best performer", styles["THX"])]]
    for row in rows[:9]:
        avg = row.get("industry_average")
        avg_text = _fmt_value(row.get("ratio"), avg) if isinstance(avg, (int, float)) else "N/A"
        data.append([_p(str(row.get("ratio", "Metric")).replace("_", " ").title(), styles["TCX"]), _p(avg_text, styles["TCX"]), _p(str(row.get("best_performer") or "N/A"), styles["TCBX"])])
    return _table(data, [2.55 * inch, 1.75 * inch, 2.42 * inch], align_right_cols=[1])

def _risk_overview(flags, styles):
    high = sum(1 for sev, _, _ in flags if str(sev).upper() == "HIGH")
    medium = sum(1 for sev, _, _ in flags if str(sev).upper() == "MEDIUM")
    low = sum(1 for sev, _, _ in flags if str(sev).upper() not in {"HIGH", "MEDIUM"})
    rows = [
        [_p("Severity", styles["THX"]), _p("Count", styles["THX"]), _p("Interpretation", styles["THX"])],
        [_p("HIGH", styles["TCBX"]), _p(str(high), styles["TCX"]), _p("Immediate attention", styles["TCX"])],
        [_p("MEDIUM", styles["TCBX"]), _p(str(medium), styles["TCX"]), _p("Requires monitoring", styles["TCX"])],
        [_p("OTHER", styles["TCBX"]), _p(str(low), styles["TCX"]), _p("Lower-priority items", styles["TCX"])],
    ]
    return _table(rows, [1.4 * inch, 0.8 * inch, 4.8 * inch], align_right_cols=[1])


def _risk_item(sev, title, explanation, styles):
    rc, rb = _risk_color(sev)
    left = Paragraph(f'<font color="{rc.hexval()}"><b>{escape(str(sev).upper())}</b></font>', styles["SmallX"])
    right = _rich(f"<b>{escape(title)}</b><br/>{escape(explanation)}", styles["BodyTight"])
    t = Table([[left, right]], colWidths=[0.9 * inch, 6.1 * inch], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, 0), rb),
        ("LINEBEFORE", (0, 0), (0, 0), 2.5, rc),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _risk_health(extraction, styles):
    ratios = extraction.get("ratios", {}) or {}
    margin = ratios.get("net_profit_margin")
    de = ratios.get("debt_to_equity")
    cash = extraction.get("cash_flow")
    rows = [
        ["PROFITABILITY", "Strong" if isinstance(margin, (int, float)) and margin >= 8 else "Review", f"{float(margin):.2f}%" if isinstance(margin, (int, float)) else "N/A"],
        ["CASH GENERATION", "Positive" if isinstance(cash, (int, float)) and cash > 0 else "Review", f"${float(cash)/1000:.1f}B" if isinstance(cash, (int, float)) else "N/A"],
        ["LEVERAGE", "High" if isinstance(de, (int, float)) and de >= 3 else "Moderate", f"{float(de):.2f}x" if isinstance(de, (int, float)) else "N/A"],
    ]
    data = [[_p("Area", styles["THX"]), _p("Assessment", styles["THX"]), _p("Measure", styles["THX"])]]
    for area, assessment, measure in rows:
        data.append([_p(area, styles["TCBX"]), _p(assessment, styles["TCX"]), _p(measure, styles["TCX"])])
    return _table(data, [2.4 * inch, 2.5 * inch, 1.9 * inch], align_right_cols=[2])


def _peer_colors(tickers, target):
    palette = [TEAL, CORAL, colors.HexColor("#2563EB"), colors.HexColor("#0E9F6E")]
    out = {}
    if target in tickers:
        out[target] = PURPLE
    j = 0
    for ticker in tickers:
        if ticker not in out:
            out[ticker] = palette[j % len(palette)]
            j += 1
    return out


def _key(name):
    return str(name or "").lower().strip().replace(" ", "_").replace("-", "_")


def _fmt_value(metric, value):
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except Exception:
        return str(value)
    k = _key(metric)
    if "margin" in k:
        return f"{v:,.2f}%"
    if "debt" in k or "ratio" in k:
        return f"{v:,.2f}x"
    if k == "eps":
        return f"${v:,.2f}"
    return f"${v:,.0f}M"


def _peer_chart(section, target, width=6.72 * inch, height=3.25 * inch):
    """Aligned two-series benchmark chart with a visible industry-average marker."""
    rows = section.get("rows", []) or []
    tickers = section.get("tickers", []) or []
    tc = _peer_colors(tickers, target)
    d = Drawing(width, height)
    label_x = 0
    plot_x = 1.42 * inch
    plot_w = width - plot_x - 0.75 * inch
    top = height - 20
    row_gap = min(29, (height - 45) / max(len(rows), 1))

    # Scale is recalculated for every metric so the visual compares each pair cleanly.
    for i, row in enumerate(rows[:9]):
        y = top - i * row_gap
        metric = str(row.get("ratio", "Metric")).replace("_", " ").title()
        vals = row.get("raw_values", {}) or {}
        nums = [float(v) for v in vals.values() if isinstance(v, (int, float))]
        avg = row.get("industry_average")
        if isinstance(avg, (int, float)):
            nums.append(float(avg))
        mx = max(nums) if nums else 1.0
        if mx == 0:
            mx = 1.0
        d.add(String(label_x, y + 3, metric, fontName="Helvetica-Bold", fontSize=7.1, fillColor=INK))

        # Thin guide line; no surrounding chart box.
        d.add(Line(plot_x, y + 1, plot_x + plot_w, y + 1, strokeColor=BORDER, strokeWidth=0.7))

        if isinstance(avg, (int, float)):
            ax = plot_x + plot_w * float(avg) / mx
            d.add(Line(ax, y - 8, ax, y + 15, strokeColor=GOLD, strokeWidth=1.6))
            d.add(Circle(ax, y + 4, 2.5, fillColor=GOLD, strokeColor=WHITE, strokeWidth=0.6))

        for j, ticker in enumerate(tickers[:2]):
            value = vals.get(ticker)
            if not isinstance(value, (int, float)):
                continue
            yy = y + (6 if j == 0 else -3)
            bw = max(2.5, plot_w * float(value) / mx)
            d.add(Rect(plot_x, yy, bw, 4.5, fillColor=tc[ticker], strokeColor=tc[ticker]))
            if row.get("best_performer") == ticker:
                d.add(Circle(plot_x + bw, yy + 2.25, 2.8, fillColor=GOLD, strokeColor=WHITE, strokeWidth=0.6))
            d.add(String(plot_x + plot_w + 6, yy - 1.2, _fmt_value(metric, value), fontName="Helvetica-Bold", fontSize=6.5, fillColor=tc[ticker]))

    return d


def _peer_legend(tickers, target, styles):
    tc = _peer_colors(tickers, target)
    parts = []
    for ticker in tickers[:2]:
        parts.append(_rich(f'<font color="{tc[ticker].hexval()}">●</font> <b>{escape(ticker)}</b>', styles["SmallX"]))
    parts.append(_rich(f'<font color="{GOLD.hexval()}">●</font> Industry average', styles["SmallX"]))
    t = Table([parts], colWidths=[1.0 * inch] * len(parts), hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _podium(section, target, styles):
    rankings = sorted(section.get("rankings", []) or [], key=lambda x: x.get("rank", 99))
    if not rankings:
        return Spacer(1, 0.1 * inch)
    w, h = 6.72 * inch, 1.28 * inch
    d = Drawing(w, h)
    tc = _peer_colors(section.get("tickers", []) or [], target)
    d.add(String(0, h - 8, "INDUSTRY RANKING", fontName="Helvetica-Bold", fontSize=7.6, fillColor=NAVY))
    base_y = 4
    positions = {
        1: (2.30 * inch, base_y, 1.72 * inch, 0.86 * inch),
        2: (0.55 * inch, base_y, 1.72 * inch, 0.66 * inch),
        3: (4.05 * inch, base_y, 1.72 * inch, 0.52 * inch),
    }
    for item in rankings[:3]:
        rank = int(item.get("rank", 99))
        ticker = str(item.get("ticker", ""))
        if rank not in positions:
            continue
        x, y, bw, bh = positions[rank]
        c = tc.get(ticker, TEAL)
        d.add(Rect(x, y, bw, bh, fillColor=c, strokeColor=c))
        d.add(String(x + bw / 2, y + bh - 14, f"#{rank}", fontName="Helvetica-Bold", fontSize=11.5, fillColor=WHITE, textAnchor="middle"))
        d.add(String(x + bw / 2, y + bh / 2 - 1, ticker, fontName="Helvetica-Bold", fontSize=9, fillColor=WHITE, textAnchor="middle"))
        if item.get("score") is not None:
            d.add(String(x + bw / 2, y + 7, f"Score {float(item['score']):.2f}", fontName="Helvetica", fontSize=6.3, fillColor=WHITE, textAnchor="middle"))
    return d


def _comparison_panel(section, target, styles):
    title = section.get("title") or "Peer comparison"
    tickers = section.get("tickers", []) or []
    header = Table([[
        _rich(f'<b>{escape(title)}</b>', ParagraphStyle("peerTitle", fontName="Helvetica-Bold", fontSize=13, textColor=WHITE)),
        _rich("Peer benchmark", ParagraphStyle("peerSub", fontName="Helvetica", fontSize=7.3, textColor=WHITE, alignment=TA_RIGHT)),
    ]], colWidths=[5.3 * inch, 1.42 * inch], hAlign="LEFT")
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PURPLE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    content = [
        header,
        Spacer(1, 0.05 * inch),
        _peer_legend(tickers, target, styles),
        _peer_chart(section, target),
        Spacer(1, 0.03 * inch),
        _podium(section, target, styles),
        _rich("Gold marker = industry average. Gold dot = best performer for that metric.", styles["TinyX"]),
    ]
    outer = Table([[content]], colWidths=[6.72 * inch], hAlign="LEFT")
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PURPLE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D8CFF8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return outer


def _outlook_grid(extraction, styles):
    ratios = extraction.get("ratios", {}) or {}
    margin = ratios.get("net_profit_margin")
    de = ratios.get("debt_to_equity")
    cash = extraction.get("cash_flow")
    rows = [
        ["PROFITABILITY", f"{float(margin):.2f}%" if isinstance(margin, (int, float)) else "N/A", "Current margin"],
        ["CASH GENERATION", f"${float(cash)/1000:.1f}B" if isinstance(cash, (int, float)) else "N/A", "Reported cash flow"],
        ["LEVERAGE", f"{float(de):.2f}x" if isinstance(de, (int, float)) else "N/A", "Debt-to-equity"],
    ]
    data = [[_p("Indicator", styles["THX"]), _p("FY 2025", styles["THX"]), _p("Reference", styles["THX"])]]
    for a, b, c in rows:
        data.append([_p(a, styles["TCBX"]), _p(b, styles["TCBX"]), _p(c, styles["SmallX"])])
    return _table(data, [2.55 * inch, 1.45 * inch, 3.0 * inch], align_right_cols=[1])


def _header_footer(company, fiscal_year):
    def draw(canvas, doc):
        canvas.saveState()
        width, height = letter
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.45)
        canvas.line(doc.leftMargin, height - 0.43 * inch, width - doc.rightMargin, height - 0.43 * inch)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(doc.leftMargin, height - 0.32 * inch, f"{company.name} | {company.ticker}")
        canvas.drawRightString(width - doc.rightMargin, height - 0.32 * inch, f"FY {fiscal_year}")
        canvas.line(doc.leftMargin, 0.43 * inch, width - doc.rightMargin, 0.43 * inch)
        canvas.setFont("Helvetica", 7.2)
        canvas.drawString(doc.leftMargin, 0.27 * inch, "Financial Research")
        canvas.drawRightString(width - doc.rightMargin, 0.27 * inch, str(doc.page))
        canvas.restoreState()
    return draw


def build_report_pdf(
    company: Company,
    extraction: dict,
    red_flags: Optional[RedFlagResult],
    comparisons: list[ComparisonResult],
    executive_summary: str,
    outlook: str,
) -> bytes:
    buffer = BytesIO()
    fy = extraction.get("fiscal_year") or "N/A"
    styles = _styles()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.62 * inch,
        bottomMargin=0.58 * inch,
        leftMargin=0.70 * inch,
        rightMargin=0.70 * inch,
        title=f"{company.name} Financial Research Report",
        author="Multi-Agent Financial Research System",
    )
    story = []

    # ------------------------------------------------------------------ PAGE 1
    story += [
        Spacer(1, 0.05 * inch),
        Paragraph(escape(company.name), styles["TitleX"]),
        Paragraph(f"{escape(company.ticker)}  |  Financial Research Report", styles["TickerX"]),
        Paragraph(f"Fiscal Year {fy}", styles["SubX"]),
        _kpi_strip(financial_kpis(extraction), styles),
        Spacer(1, 0.10 * inch),
    ]

    story += _section_heading("Executive Summary", styles, "Executive view")
    story.append(_p(executive_summary or "Not available.", styles["BodyX"]))
    story.append(Spacer(1, 0.02 * inch))

    story += _section_heading("Financial Profile", styles)
    revenue = extraction.get("revenue")
    profit = extraction.get("net_profit")
    cash = extraction.get("cash_flow")
    story.append(Table([[
        _metric_bars("Scale & earnings", [("Revenue", revenue), ("Net profit", profit), ("Cash flow", cash)]),
        _balance_chart(extraction),
    ]], colWidths=[3.46 * inch, 3.46 * inch], hAlign="LEFT", style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ])))

    story += _section_heading("Key Financials", styles)
    story.append(_financial_snapshot(extraction, fy, styles))
    story.append(PageBreak())

    # ------------------------------------------------------------------ PAGE 2
    story += _section_heading("Risk Assessment", styles, "Risk & financial health")
    flags = red_flags_rows(red_flags)
    risk = red_flags.overall_risk if red_flags else "Not assessed"
    rc, rb = _risk_color(risk)
    risk_head = Table([[
        _rich("OVERALL RISK", styles["SmallX"]),
        _rich(f'<b>{escape(str(risk).upper())}</b>', ParagraphStyle("RiskValue", fontName="Helvetica-Bold", fontSize=13, textColor=rc)),
    ]], colWidths=[1.8 * inch, 5.2 * inch], hAlign="LEFT")
    risk_head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), rb),
        ("LINEBEFORE", (0, 0), (0, 0), 3, rc),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(risk_head)
    story.append(Spacer(1, 0.12 * inch))

    story += _section_heading("Financial Health", styles)
    story.append(_risk_health(extraction, styles))
    story.append(Spacer(1, 0.10 * inch))

    story += _section_heading("Risk Summary", styles)
    if flags:
        story.append(_risk_overview(flags, styles))
        story.append(Spacer(1, 0.06 * inch))
        story.append(_risk_severity_chart(flags))
        story.append(Spacer(1, 0.08 * inch))
        for sev, title, explanation in flags:
            story.append(_risk_item(sev, title, explanation, styles))
            story.append(Spacer(1, 0.045 * inch))
    else:
        story.append(_p("No red flags were identified, or red flag analysis has not been run.", styles["BodyX"]))
    story.append(PageBreak())

    # ------------------------------------------------------------------ PAGE 3/4: one peer comparison per page
    sections = comparison_sections(comparisons)
    if sections:
        for i, section in enumerate(sections[:2]):
            story += _section_heading("Peer Comparison", styles, f"Benchmark {i + 1} of {min(len(sections), 2)}")
            story.append(_comparison_panel(section, company.ticker, styles))
            story.append(Spacer(1, 0.09 * inch))
            readout = _benchmark_readout(section, company.ticker, styles)
            average_table = _benchmark_average_table(section, styles)
            if readout:
                story.append(readout)
                story.append(Spacer(1, 0.08 * inch))
            if average_table:
                story.append(average_table)
            story.append(PageBreak())
    else:
        # Do not force an empty page when comparison data is unavailable.
        # Keep the section visible, then continue naturally into the outlook.
        story += _section_heading("Peer Comparison", styles)
        story.append(_p(
            "No peer comparison was performed for this company. The report continues with the company-level outlook below.",
            styles["BodyX"],
        ))
        story.append(Spacer(1, 0.16 * inch))

    # ------------------------------------------------------------------ FINAL PAGE
    story += _section_heading("Outlook", styles, "Forward view")
    story.append(_p(outlook or "Not available.", styles["BodyX"]))
    story.append(Spacer(1, 0.06 * inch))

    story += _section_heading("What Matters Next", styles)
    story.append(_outlook_grid(extraction, styles))
    story.append(Spacer(1, 0.14 * inch))

    story += _section_heading("Conclusion", styles)
    conclusion = (
        "The reported financial profile combines meaningful scale, positive cash generation and a solid earnings base "
        "with elevated balance-sheet leverage. The key areas to follow in subsequent reporting periods are leverage, "
        "profitability, cash generation and the company's position against its selected peers."
    )
    story.append(_p(conclusion, styles["BodyX"]))
    story.append(Spacer(1, 0.16 * inch))
    story += _section_heading("Report Note", styles)
    story.append(_p(
        "Analysis is based on the selected filing, extracted financial measures, available risk assessment and "
        "available peer-comparison results.",
        styles["SmallX"],
    ))

    doc.build(story, onFirstPage=_header_footer(company, fy), onLaterPages=_header_footer(company, fy))
    return buffer.getvalue()
