"""
Non-LLM financial statement extractor.
Replaces the CrewAI/OpenAI extraction agent with deterministic regex parsing.

Handles two known document styles, tried in order per field:
  A) OCR-style label lines with "Rs." currency and Indian comma grouping
     e.g. "Total Revenue .........ccccceeeeees Rs. 45,20,00,000"
  B) Prose annual-report style with two-column ($FY_current $FY_prior) tables
     e.g. "Revenue $412,600 $358,200" inside a
     "Consolidated Statement of Operations ... Consolidated Balance Sheet" section

Add more section/label patterns here as new document formats show up.
"""
import re
from typing import Optional


def _num(raw: Optional[str]) -> Optional[float]:
    """Strip commas/whitespace and convert to float/int. No unit scaling — extracted as-is."""
    if raw is None:
        return None
    cleaned = raw.replace(",", "").replace("$", "").strip()
    if cleaned == "":
        return None
    val = float(cleaned)
    return int(val) if val.is_integer() else val


def _find(pattern: str, text: str, flags=re.IGNORECASE) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


def _section(text: str, start_pat: str, end_pat: Optional[str]) -> str:
    """Return the text between start_pat and end_pat (or end of string). Empty string if start not found."""
    m_start = re.search(start_pat, text, re.IGNORECASE)
    if not m_start:
        return ""
    start = m_start.end()
    if end_pat:
        m_end = re.search(end_pat, text[start:], re.IGNORECASE)
        end = start + m_end.start() if m_end else len(text)
    else:
        end = len(text)
    return text[start:end]


def extract_financial_data(document_text: str, metric_id: str, document_id: str) -> dict:
    text = document_text

    # ---------- Company name ----------
    # Works for both "ACME INDUSTRIES LTD." and "Nova Orbital Technologies, Inc."
    company = _find(
        r"^(.*?\b(?:Ltd|Limited|Inc|Corp|Corporation|LLC|PLC)\.?)\b",
        text,
    )
    if company:
        company = company.strip().rstrip(".") + "."

    # ---------- Fiscal year ----------
    fy_raw = (
        _find(r"\bFY\s*[-:]?\s*(\d{4})\b", text)
        or _find(r"Fiscal\s+Year\s*(?:ended\s+\w+\s+\d{1,2},\s*)?(\d{4})", text)
    )
    fiscal_year = int(fy_raw) if fy_raw else None

    # ============================================================
    # FORMAT A: OCR-style "Label ...dots... Rs. 12,34,567" lines
    # ============================================================
    revenue = _num(_find(r"Total\s+Revenue[\s\S]{0,80}?Rs\.?\s*([\d,]+)", text))
    net_profit = _num(_find(r"Net\s+Profit(?!\s+Margin)[\s\S]{0,80}?Rs\.?\s*([\d,]+)", text))
    assets = _num(_find(r"Total\s+Assets[\s\S]{0,80}?Rs\.?\s*([\d,]+)", text))
    liabilities = _num(_find(r"Total\s+Liabilities[\s\S]{0,80}?Rs\.?\s*([\d,]+)", text))
    cash_flow = _num(_find(r"Cash\s+Flow\s+from\s+Operations[\s\S]{0,80}?Rs\.?\s*([\d,]+)", text))
    eps = _num(_find(r"Earnings\s+Per\s+Share\s*\(EPS\)[\s\S]{0,60}?Rs\.?\s*([\d]+\.?\d*)", text))
    current_ratio = _num(_find(r"Current\s+Ratio[\s\S]{0,60}?([\d]+\.\d+)", text))
    debt_to_equity = _num(_find(r"Debt\s+to\s+Equity\s+Ratio[\s\S]{0,60}?([\d]+\.\d+)", text))
    net_profit_margin = _num(_find(r"Net\s+Profit\s+Margin[\s\S]{0,60}?([\d]+\.?\d*)\s*%", text))

    current_assets = None
    current_liabilities = None

    # ============================================================
    # FORMAT B: prose annual-report style, two-column $ tables
    # ============================================================
    ops_section = _section(
        text,
        r"Consolidated\s+Statement\s+of\s+Operations",
        r"Consolidated\s+Balance\s+Sheet",
    )
    bs_section = _section(
        text,
        r"Consolidated\s+Balance\s+Sheet",
        r"Consolidated\s+Statement\s+of\s+Cash\s+Flows",
    )
    cf_section = _section(
        text,
        r"Consolidated\s+Statement\s+of\s+Cash\s+Flows",
        r"Management.?s\s+Discussion",
    )

    if revenue is None:
        revenue = _num(_find(r"\bRevenue\s+\$([\d,]+)\s+\$[\d,]+", ops_section))
    if net_profit is None:
        net_profit = _num(_find(r"\bNet\s+income\s+\$([\d,]+)\s+\$[\d,]+", ops_section))
    if eps is None:
        eps = _num(_find(r"Diluted\s+earnings\s+per\s+share\s+\$([\d,]+\.?\d*)\s+\$[\d,]+\.?\d*", ops_section))

    if assets is None:
        assets = _num(_find(r"Total\s+assets\s+\$([\d,]+)\s+\$[\d,]+", bs_section))
    if liabilities is None:
        liabilities = _num(_find(r"Total\s+liabilities\s+\$([\d,]+)\s+\$[\d,]+", bs_section))
    current_assets = _num(_find(r"Total\s+current\s+assets\s+\$([\d,]+)\s+\$[\d,]+", bs_section))
    current_liabilities = _num(_find(r"Total\s+current\s+liabilities\s+\$([\d,]+)\s+\$[\d,]+", bs_section))

    if cash_flow is None:
        cash_flow = _num(
            _find(r"Net\s+cash\s+provided\s+by\s+operating\s+activities\s+\$([\d,]+)\s+\$?[\(\-]?[\d,]+", cf_section)
        )

    # ---------- Ratios: use stated values, else compute ----------
    if current_ratio is None and current_assets and current_liabilities:
        current_ratio = round(current_assets / current_liabilities, 2)

    if debt_to_equity is None and liabilities is not None and assets is not None and (assets - liabilities) != 0:
        debt_to_equity = round(liabilities / (assets - liabilities), 2)

    if net_profit_margin is None and net_profit is not None and revenue not in (None, 0):
        net_profit_margin = round((net_profit / revenue) * 100, 2)

    return {
        "metric_id": metric_id,
        "document_id": document_id,
        "company": company,
        "fiscal_year": fiscal_year,
        "revenue": revenue,
        "net_profit": net_profit,
        "assets": assets,
        "liabilities": liabilities,
        "cash_flow": cash_flow,
        "eps": eps,
        "ratios": {
            "current_ratio": current_ratio,
            "debt_to_equity": debt_to_equity,
            "net_profit_margin": net_profit_margin,
        },
    }


if __name__ == "__main__":
    import json

    acme = (
        "ACME INDUSTRIES LTD. Annual Financial Report - FY 2025 Statement of "
        "Financial Position (Scanned Copy) Total Revenue .........ccccceeeeees Rs. "
        "45,20,00,000 Net Profit .............ccceceeeeeee Rs. 6,75,00,000 Total "
        "Assets .......ccceeee ee eeee Rs. 1,20,00,00,000 Total Liabilities "
        "........0000.00. Rs. 55,00,00,000 Cash Flow from Operations .......... Rs. "
        "8,10,00,000 Earnings Per Share (EPS) ........... Rs. 12.45 Current Ratio' "
        "sceccerccreeeees 1.85 Debt to Equity Ratio ................ 0.62 Net "
        "Profit Margin ................0. 14.9%"
    )

    nova = (
        "Nova Orbital Technologies, Inc. Annual Report and Financial Statements — "
        "Fiscal Year 2025 Company Overview Nova Orbital Technologies, Inc. designs, "
        "manufactures, and launches small-satellite communication systems. "
        "Consolidated Statement of Operations For the fiscal years ended December 31, "
        "2025 and 2024 (in thousands, except per-share data) FY2025 FY2024 Revenue "
        "$412,600 $358,200 Cost of revenue $243,700 $204,200 Gross profit $168,900 "
        "$154,000 Research and development $58,400 $47,900 Selling, general and "
        "administrative $52,100 $44,300 Restructuring charges $9,800 $0 Operating "
        "income $48,600 $61,800 Interest expense, net $14,200 $6,100 Income before "
        "income taxes $34,400 $55,700 Provision for income taxes $3,000 $12,900 Net "
        "income $31,400 $42,800 Basic earnings per share $0.91 $1.24 Diluted earnings "
        "per share $0.87 $1.19 Weighted average diluted shares outstanding 36,092 "
        "35,966 Segment Revenue Segment FY2025 FY2024 Satellite Systems $298,100 "
        "$246,500 Ground Infrastructure $114,500 $111,700 Total Revenue $412,600 "
        "$358,200 Consolidated Balance Sheet As of December 31, 2025 and 2024 (in "
        "thousands) FY2025 FY2024 Cash and cash equivalents $62,300 $88,100 Accounts "
        "receivable, net $71,400 $58,900 Inventory $54,200 $41,600 Total current "
        "assets $187,900 $188,600 Property, plant and equipment, net $210,800 "
        "$186,300 Goodwill and intangible assets $95,400 $97,100 Total assets "
        "$494,100 $472,000 Accounts payable $48,600 $39,200 Current portion of "
        "long-term debt $22,000 $14,500 Total current liabilities $70,600 $53,700 "
        "Long-term debt $188,300 $128,200 Total liabilities $258,900 $181,900 Total "
        "stockholders' equity $235,200 $290,100 Total liabilities and stockholders' "
        "equity $494,100 $472,000 Consolidated Statement of Cash Flows (Summary) "
        "FY2025 FY2024 Net cash provided by operating activities $46,200 $71,500 Net "
        "cash used in investing activities ($58,900) ($39,200) Net cash provided by "
        "(used in) financing activities ($13,100) $18,400 Net increase (decrease) in "
        "cash ($25,800) $50,700 Management's Discussion and Analysis Total debt "
        "increased 47.4%..."
    )

    print("=== ACME ===")
    print(json.dumps(extract_financial_data(acme, "M001", "D1B8D3D4D"), indent=2))
    print("\n=== NOVA ORBITAL ===")
    print(json.dumps(extract_financial_data(nova, "M001", "D9320B3EF"), indent=2))