"""Data-shaping helpers for the financial research report PDF."""
from typing import Optional
from models.red_flag import RedFlagResult
from models.comparison_result import ComparisonResult


def _fmt_number(value, decimals=2):
    if value is None: return "N/A"
    try: return f"{float(value):,.{decimals}f}"
    except (TypeError,ValueError): return str(value)


def _fmt_money(value):
    if value is None: return "N/A"
    try:
        value=float(value)
        return f"${value:,.0f}M" if abs(value)>=1000 else f"${value:,.2f}M"
    except (TypeError,ValueError): return str(value)


def _fmt_ratio(value):
    if value is None: return "N/A"
    try: return f"{float(value):,.2f}x"
    except (TypeError,ValueError): return str(value)


def _fmt_percent(value):
    if value is None: return "N/A"
    try: return f"{float(value):,.2f}%"
    except (TypeError,ValueError): return str(value)


def financials_table_rows(extraction: dict):
    ratios=extraction.get("ratios",{}) or {}
    return [("Revenue",_fmt_money(extraction.get("revenue"))), ("Net Profit",_fmt_money(extraction.get("net_profit"))), ("Total Assets",_fmt_money(extraction.get("assets"))), ("Total Liabilities",_fmt_money(extraction.get("liabilities"))), ("Cash Flow",_fmt_money(extraction.get("cash_flow"))), ("EPS",f"${_fmt_number(extraction.get('eps'))}"), ("Net Profit Margin",_fmt_percent(ratios.get("net_profit_margin"))), ("Debt-to-Equity",_fmt_ratio(ratios.get("debt_to_equity"))), ("Current Ratio",_fmt_ratio(ratios.get("current_ratio")))]


def financial_kpis(extraction: dict):
    ratios=extraction.get("ratios",{}) or {}
    return [{"label":"REVENUE","value":_fmt_money(extraction.get("revenue"))},{"label":"NET PROFIT","value":_fmt_money(extraction.get("net_profit"))},{"label":"NET MARGIN","value":_fmt_percent(ratios.get("net_profit_margin"))},{"label":"DEBT / EQUITY","value":_fmt_ratio(ratios.get("debt_to_equity"))}]


def red_flags_rows(red_flags: Optional[RedFlagResult]):
    if red_flags is None or not red_flags.flags: return []
    return [(str(f.severity or "UNKNOWN"),str(f.title or "Unnamed Risk"),str(f.explanation or "No explanation available.")) for f in red_flags.flags]


def comparison_sections(comparisons: list[ComparisonResult]):
    sections=[]
    for comp in comparisons:
        tickers=list(comp.tickers or [])
        rows=[]
        for ratio in comp.ratio_comparisons or []:
            vals=dict(ratio.values or {})
            rows.append({
                "ratio":ratio.ratio_name,
                "values":[(t,_fmt_number(vals.get(t))) for t in tickers],
                "raw_values":vals,
                "industry_average":ratio.industry_average,
                "best_performer":ratio.best_performer,
            })
        rankings=[{"rank":r.rank,"ticker":r.ticker,"score":r.score} for r in sorted(comp.industry_rankings or [],key=lambda x:x.rank)]
        sections.append({"title":" vs ".join(tickers),"tickers":tickers,"rows":rows,"rankings":rankings,"summary":comp.summary})
    return sections
