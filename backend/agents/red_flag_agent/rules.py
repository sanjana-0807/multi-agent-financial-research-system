# agents/red_flag_agent/rules.py
"""
Deterministic rule engine for numeric red-flag detection.

Operates only on structured ExtractionResponse data (revenue, net_profit,
assets, liabilities, cash_flow, eps, ratios). Never touches an LLM --
every flag here is reproducible and traceable to a specific metric_id,
satisfying the project's "strictly grounded" requirement.

NOTE: this currently runs on a SINGLE fiscal year's data, since the
Extraction Agent only returns one year per document today. Rules that
would normally compare year-over-year (e.g. "rising" debt) are
implemented here as single-year leverage/stress thresholds instead.
When multi-year ExtractionResponse data becomes available, add a
second set of functions (e.g. detect_rising_debt_trend) that take a
list of records sorted by fiscal_year and compare deltas -- do not
replace these, since single-year stress checks remain useful even
when multi-year data exists.
"""
from typing import Optional


def _flag(category: str, title: str, severity: str, explanation: str,
          evidence: str, metric_id: str) -> dict:
    return {
        "category": category,
        "title": title,
        "severity": severity,
        "explanation": explanation,
        "evidence": evidence,
        "source_metric_id": metric_id,
        "page_number": None,
    }


def detect_leverage_risk(data: dict, metric_id: str) -> list[dict]:
    """Rising Debt category -- single-year leverage check."""
    flags = []
    dte = (data.get("ratios") or {}).get("debt_to_equity")
    liabilities = data.get("liabilities")
    assets = data.get("assets")

    if dte is not None:
        if dte > 2.0:
            flags.append(_flag(
                "rising_debt", "High Leverage",
                "HIGH",
                "Debt-to-equity ratio indicates the company is financed "
                "predominantly by debt relative to equity, increasing "
                "financial risk if earnings decline.",
                f"debt_to_equity = {dte}", metric_id,
            ))
        elif dte > 1.0:
            flags.append(_flag(
                "rising_debt", "Elevated Leverage",
                "MEDIUM",
                "Debt-to-equity ratio is above 1.0, meaning liabilities "
                "exceed equity funding.",
                f"debt_to_equity = {dte}", metric_id,
            ))

    if liabilities is not None and assets is not None and assets > 0:
        ratio = liabilities / assets
        if ratio > 0.7:
            flags.append(_flag(
                "rising_debt", "Liabilities Approaching Total Assets",
                "HIGH" if ratio > 0.85 else "MEDIUM",
                "Liabilities make up a large share of total assets, "
                "leaving a thin equity cushion.",
                f"liabilities/assets = {ratio:.2f} "
                f"(liabilities={liabilities}, assets={assets})",
                metric_id,
            ))

    return flags


def detect_margin_weakness(data: dict, metric_id: str) -> list[dict]:
    """Falling Margins category -- single-year margin-quality check."""
    flags = []
    npm = (data.get("ratios") or {}).get("net_profit_margin")

    if npm is not None:
        if npm < 0:
            flags.append(_flag(
                "falling_margins", "Negative Net Profit Margin",
                "HIGH",
                "The company reported a net loss relative to revenue "
                "for the period.",
                f"net_profit_margin = {npm}%", metric_id,
            ))
        elif npm < 5:
            flags.append(_flag(
                "falling_margins", "Thin Net Profit Margin",
                "MEDIUM",
                "Net profit margin is low, leaving little buffer against "
                "rising costs or revenue softness.",
                f"net_profit_margin = {npm}%", metric_id,
            ))

    return flags


def detect_cash_flow_issues(data: dict, metric_id: str) -> list[dict]:
    """Cash Flow Issues category."""
    flags = []
    net_profit = data.get("net_profit")
    cash_flow = data.get("cash_flow")

    if net_profit is not None and cash_flow is not None:
        if net_profit > 0 and cash_flow <= 0:
            flags.append(_flag(
                "cash_flow_issues", "Profit Not Backed by Cash Flow",
                "HIGH",
                "The company reported positive net profit but flat or "
                "negative cash flow -- a classic earnings-quality "
                "warning sign (profit may include non-cash items or "
                "aggressive revenue recognition).",
                f"net_profit={net_profit}, cash_flow={cash_flow}",
                metric_id,
            ))
        elif net_profit > 0 and cash_flow < (0.5 * net_profit):
            flags.append(_flag(
                "cash_flow_issues", "Cash Flow Lagging Reported Profit",
                "MEDIUM",
                "Cash flow is materially lower than net profit, worth "
                "investigating for working-capital or accrual issues.",
                f"net_profit={net_profit}, cash_flow={cash_flow}",
                metric_id,
            ))
    elif cash_flow is not None and cash_flow < 0:
        flags.append(_flag(
            "cash_flow_issues", "Negative Cash Flow",
            "HIGH",
            "The company reported negative cash flow for the period.",
            f"cash_flow={cash_flow}", metric_id,
        ))

    return flags


def detect_financial_risk(data: dict, metric_id: str) -> list[dict]:
    """Financial Risks category -- liquidity and solvency stress."""
    flags = []
    current_ratio = (data.get("ratios") or {}).get("current_ratio")
    liabilities = data.get("liabilities")
    assets = data.get("assets")

    if current_ratio is not None:
        if current_ratio < 1.0:
            flags.append(_flag(
                "financial_risk", "Liquidity Risk",
                "HIGH",
                "Current ratio below 1.0 means current liabilities "
                "exceed current assets, a short-term liquidity concern.",
                f"current_ratio = {current_ratio}", metric_id,
            ))
        elif current_ratio < 1.5:
            flags.append(_flag(
                "financial_risk", "Tight Liquidity",
                "MEDIUM",
                "Current ratio is below the commonly-used 1.5 comfort "
                "threshold for short-term obligations.",
                f"current_ratio = {current_ratio}", metric_id,
            ))

    if liabilities is not None and assets is not None and liabilities > assets:
        flags.append(_flag(
            "financial_risk", "Liabilities Exceed Assets",
            "HIGH",
            "Total liabilities exceed total assets, indicating negative "
            "book equity -- a solvency concern.",
            f"liabilities={liabilities} > assets={assets}", metric_id,
        ))

    return flags


def run_all_rules(data: dict, metric_id: str) -> list[dict]:
    """
    Runs every numeric rule category and returns a flat list of flag
    dicts, ready to be wrapped in RedFlag models.
    """
    flags: list[dict] = []
    flags += detect_leverage_risk(data, metric_id)
    flags += detect_margin_weakness(data, metric_id)
    flags += detect_cash_flow_issues(data, metric_id)
    flags += detect_financial_risk(data, metric_id)
    return flags


def compute_overall_risk(flags: list[dict]) -> str:
    if any(f["severity"] == "HIGH" for f in flags):
        return "HIGH"
    if any(f["severity"] == "MEDIUM" for f in flags):
        return "MEDIUM"
    return "LOW"