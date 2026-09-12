# agents/report_agent/crew.py

"""
Report Agent narrative generation.

The report uses a direct LLM call rather than CrewAI's Task/Crew execution
path. This avoids the CrewAI JSON-repair path that can unexpectedly route
through OpenAI.

The LLM is responsible only for narrative analysis.
All financial calculations and source data come from the existing agents.
"""

import json
import re
from typing import Optional

from starlette.concurrency import run_in_threadpool

from agents.report_agent.agent import llm
from agents.report_agent.tasks import REPORT_TASK_DESCRIPTION

from models.company import Company
from models.red_flag import RedFlagResult
from models.comparison_result import ComparisonResult


# ============================================================================
# JSON PARSING
# ============================================================================

def _extract_json(raw: str) -> dict:
    """
    Extract a JSON object from an LLM response.

    Handles:
    - plain JSON
    - ```json fenced JSON
    - accidental text surrounding JSON
    """

    text = str(raw or "").strip()

    text = re.sub(
        r"^```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    text = re.sub(
        r"```$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"No JSON object found in LLM output: {text[:300]}"
        )

    return json.loads(match.group(0))


# ============================================================================
# NUMBER HELPERS
# ============================================================================

def _number(value, decimals=2):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _money(value):
    if value is None:
        return "N/A"

    try:
        value = float(value)

        if abs(value) >= 1000:
            return f"{value:,.0f}"

        return f"{value:,.2f}"

    except (TypeError, ValueError):
        return str(value)


def _percent(value):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):,.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _ratio(value):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):,.2f}x"
    except (TypeError, ValueError):
        return str(value)


# ============================================================================
# FINANCIAL CONTEXT
# ============================================================================

def _format_financials(extraction: dict) -> str:
    ratios = extraction.get("ratios", {}) or {}

    lines = [
        f"Revenue: {_money(extraction.get('revenue'))}",
        f"Net Profit: {_money(extraction.get('net_profit'))}",
        f"Total Assets: {_money(extraction.get('assets'))}",
        f"Total Liabilities: {_money(extraction.get('liabilities'))}",
        f"Cash Flow: {_money(extraction.get('cash_flow'))}",
        f"EPS: {_number(extraction.get('eps'))}",
        (
            "Net Profit Margin: "
            f"{_percent(ratios.get('net_profit_margin'))}"
        ),
        (
            "Debt-to-Equity: "
            f"{_ratio(ratios.get('debt_to_equity'))}"
        ),
        (
            "Current Ratio: "
            f"{_ratio(ratios.get('current_ratio'))}"
        ),
    ]

    return "\n".join(lines)


# ============================================================================
# RED FLAGS
# ============================================================================

def _format_red_flags(
    red_flags: Optional[RedFlagResult],
) -> str:

    if red_flags is None or not red_flags.flags:
        return (
            "No red flag records are available for this report. "
            "Do not invent risk findings."
        )

    lines = [
        f"Overall Risk: {red_flags.overall_risk or 'Not assessed'}"
    ]

    for index, flag in enumerate(red_flags.flags, start=1):

        lines.append(
            f"""
Risk {index}
Category: {flag.category or 'N/A'}
Severity: {flag.severity or 'N/A'}
Title: {flag.title or 'Unnamed risk'}
Explanation: {flag.explanation or 'N/A'}
Evidence: {flag.evidence or 'N/A'}
Source Metric: {flag.source_metric_id or 'N/A'}
Source Page: {flag.page_number or 'N/A'}
""".strip()
        )

    return "\n\n".join(lines)


# ============================================================================
# COMPARISON CONTEXT
# ============================================================================

def _format_comparisons(
    comparisons: list[ComparisonResult],
) -> str:

    if not comparisons:
        return (
            "No peer comparison was performed for this company. "
            "Do not invent peer conclusions."
        )

    sections = []

    for comp in comparisons:

        tickers = list(comp.tickers or [])

        lines = [
            f"Comparison Group: {', '.join(tickers) or 'N/A'}"
        ]

        # ---------------------------------------------------------------
        # Ratios
        # ---------------------------------------------------------------

        for ratio in comp.ratio_comparisons or []:

            lines.append(
                f"\nRatio: {ratio.ratio_name}"
            )

            values = ratio.values or {}

            for ticker in tickers:
                if ticker in values:
                    lines.append(
                        f"  {ticker}: {_number(values[ticker])}"
                    )

            # Additional values not explicitly listed in tickers.
            for ticker, value in values.items():
                if ticker not in tickers:
                    lines.append(
                        f"  {ticker}: {_number(value)}"
                    )

            if ratio.industry_average is not None:
                lines.append(
                    "  Industry Average: "
                    f"{_number(ratio.industry_average)}"
                )

            if ratio.best_performer:
                lines.append(
                    f"  Best Performer: {ratio.best_performer}"
                )

        # ---------------------------------------------------------------
        # Industry rankings
        # ---------------------------------------------------------------

        if comp.industry_rankings:

            lines.append("\nIndustry Rankings:")

            rankings = sorted(
                comp.industry_rankings,
                key=lambda item: item.rank,
            )

            for rank in rankings:

                score_text = ""

                if rank.score is not None:
                    score_text = (
                        f", Score: {_number(rank.score)}"
                    )

                lines.append(
                    f"  #{rank.rank} {rank.ticker}{score_text}"
                )

        # ---------------------------------------------------------------
        # Trend analysis
        # ---------------------------------------------------------------

        if comp.trend_analysis:

            lines.append("\nTrend Data:")

            for point in comp.trend_analysis:
                lines.append(
                    f"  Period: {point.period}, "
                    f"Ticker: {point.ticker}, "
                    f"Value: {_number(point.value)}"
                )

        # ---------------------------------------------------------------
        # Existing comparison summary
        # ---------------------------------------------------------------

        if comp.summary:
            lines.append(
                "\nExisting Comparison Summary:"
            )
            lines.append(str(comp.summary))

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


# ============================================================================
# DETERMINISTIC FALLBACK
# ============================================================================

def _fallback_narrative(
    company: Company,
    extraction: dict,
    red_flags: Optional[RedFlagResult],
    comparisons: list[ComparisonResult],
) -> dict:
    """
    Produces a professional fallback narrative if the LLM is unavailable.

    IMPORTANT:
    This intentionally does not mention AI, automation, failed generation,
    or missing narrative generation.
    """

    ratios = extraction.get("ratios", {}) or {}

    revenue = extraction.get("revenue")
    net_profit = extraction.get("net_profit")
    assets = extraction.get("assets")
    liabilities = extraction.get("liabilities")
    cash_flow = extraction.get("cash_flow")
    eps = extraction.get("eps")

    margin = ratios.get("net_profit_margin")
    debt_equity = ratios.get("debt_to_equity")
    current_ratio = ratios.get("current_ratio")

    year = extraction.get("fiscal_year") or "the reported fiscal year"

    summary_parts = []

    summary_parts.append(
        f"{company.name} ({company.ticker}) reported "
        f"revenue of {_money(revenue)} and net profit of "
        f"{_money(net_profit)} in FY {year}."
    )

    if margin is not None:
        summary_parts.append(
            f"The reported net profit margin was "
            f"{_percent(margin)}, providing a direct measure of "
            f"the company's conversion of revenue into earnings."
        )

    if assets is not None and liabilities is not None:
        summary_parts.append(
            f"The balance sheet included total assets of "
            f"{_money(assets)} against liabilities of "
            f"{_money(liabilities)}, while the reported "
            f"debt-to-equity ratio was {_ratio(debt_equity)}."
        )

    if cash_flow is not None:
        summary_parts.append(
            f"Reported cash flow was {_money(cash_flow)}, "
            f"which should be considered alongside profitability "
            f"when assessing the quality of the period's financial "
            f"performance."
        )

    if eps is not None:
        summary_parts.append(
            f"EPS was {_number(eps)}, adding an earnings-per-share "
            f"measure to the assessment of reported profitability."
        )

    if red_flags and red_flags.flags:

        high_risks = [
            flag
            for flag in red_flags.flags
            if str(flag.severity or "").upper() == "HIGH"
        ]

        if high_risks:
            summary_parts.append(
                f"The risk assessment identifies "
                f"{len(high_risks)} high-severity issue(s), "
                f"which warrant particular attention when evaluating "
                f"the company's financial position."
            )
        else:
            summary_parts.append(
                f"The red-flag assessment identifies "
                f"{len(red_flags.flags)} issue(s) requiring "
                f"continued monitoring."
            )

    if comparisons:
        summary_parts.append(
            "The available peer comparison provides additional "
            "context for evaluating the company's financial ratios "
            "and relative industry position."
        )

    executive_summary = " ".join(summary_parts)

    # ------------------------------------------------------------------
    # Outlook
    # ------------------------------------------------------------------

    outlook_parts = []

    outlook_parts.append(
        f"The near-term assessment should focus on the relationship "
        f"between reported profitability, cash generation and the "
        f"company's balance-sheet position."
    )

    if margin is not None:
        outlook_parts.append(
            f"With a net profit margin of {_percent(margin)}, "
            f"future reporting periods should be evaluated for "
            f"whether profitability remains consistent with the "
            f"current reported level."
        )

    if debt_equity is not None:
        outlook_parts.append(
            f"The debt-to-equity ratio of {_ratio(debt_equity)} "
            f"also provides an important reference point for "
            f"monitoring financial leverage."
        )

    if red_flags and red_flags.flags:

        titles = [
            str(flag.title)
            for flag in red_flags.flags[:3]
            if flag.title
        ]

        if titles:
            outlook_parts.append(
                "Particular attention should remain on the identified "
                "risk areas, including "
                + ", ".join(titles)
                + "."
            )

    if comparisons:
        outlook_parts.append(
            "Peer comparison should continue to be used to determine "
            "whether the company's relative position remains stable "
            "as additional financial information becomes available."
        )

    outlook_parts.append(
        "The most useful monitoring points are therefore the "
        "company's reported profitability, cash-flow performance, "
        "balance-sheet leverage and the persistence of the risks "
        "identified in the current assessment."
    )

    conclusion = (
        f"Conclusion: The reported results provide a financial profile "
        f"that should be assessed through profitability, balance-sheet "
        f"strength, cash generation and identified risk factors rather "
        f"than through any single metric. The available comparison data "
        f"adds context to the company's relative position, while the "
        f"red-flag assessment identifies areas requiring continued "
        f"attention. Subsequent reporting periods should be reviewed "
        f"against these same measures to determine whether the current "
        f"financial profile remains consistent."
    )

    outlook = " ".join(outlook_parts) + "\n\n" + conclusion

    return {
        "executive_summary": executive_summary,
        "outlook": outlook,
    }


# ============================================================================
# QUALITY CHECK
# ============================================================================

def _valid_narrative(parsed: dict) -> bool:

    if not isinstance(parsed, dict):
        return False

    summary = parsed.get("executive_summary")
    outlook = parsed.get("outlook")

    if not isinstance(summary, str):
        return False

    if not isinstance(outlook, str):
        return False

    if len(summary.strip()) < 500:
        return False

    if len(outlook.strip()) < 450:
        return False

    return True


# ============================================================================
# MAIN
# ============================================================================

async def run_report_narrative(
    company: Company,
    extraction: dict,
    red_flags: Optional[RedFlagResult],
    comparisons: list[ComparisonResult],
) -> dict:

    context = {
        "company_name": company.name,
        "ticker": company.ticker,
        "fiscal_year": (
            extraction.get("fiscal_year")
            or "unknown"
        ),
        "financials_text": _format_financials(
            extraction
        ),
        "red_flags_text": _format_red_flags(
            red_flags
        ),
        "comparison_text": _format_comparisons(
            comparisons
        ),
    }

    prompt = REPORT_TASK_DESCRIPTION.format(
        **context
    )

    def _call_llm() -> str:

        return llm.call(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior financial research analyst. "
                        "Return ONLY valid JSON. "
                        "Do not mention AI, automation, prompts or models. "
                        "Use only supplied financial information."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    try:

        raw_output = await run_in_threadpool(
            _call_llm
        )

    except Exception as exc:

        print(
            "Report narrative LLM unavailable; "
            f"using deterministic financial narrative: {exc}"
        )

        return _fallback_narrative(
            company,
            extraction,
            red_flags,
            comparisons,
        )

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    try:

        parsed = _extract_json(
            str(raw_output)
        )

        if _valid_narrative(parsed):

            return {
                "executive_summary": (
                    parsed["executive_summary"].strip()
                ),
                "outlook": (
                    parsed["outlook"].strip()
                ),
            }

    except (
        ValueError,
        json.JSONDecodeError,
        TypeError,
    ) as exc:

        print(
            "Invalid report narrative returned by LLM; "
            f"using deterministic fallback: {exc}"
        )

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    return _fallback_narrative(
        company,
        extraction,
        red_flags,
        comparisons,
    )