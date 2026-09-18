# agents/report_agent/crew.py

"""
Fast Report Agent narrative generation.

The Report Agent receives already-computed financial information
from the existing agents and generates only:

    1. Executive Summary
    2. Outlook

It does NOT:
    - search the web
    - query ChromaDB
    - read PDFs
    - calculate financial metrics
    - run another agent
    - perform multiple LLM calls

Performance target:
    ~20-30 seconds total for the narrative generation stage,
    depending on Ollama/model loading and hardware.
"""

import json
import re
import time
from typing import Optional

from starlette.concurrency import run_in_threadpool

from agents.report_agent.agent import llm
from agents.report_agent.tasks import REPORT_TASK_DESCRIPTION

from models.company import Company
from models.red_flag import RedFlagResult
from models.comparison_result import ComparisonResult


# ============================================================================
# CONFIGURATION
# ============================================================================

# Keep the prompt compact.
# Large prompts significantly increase Ollama processing time.
MAX_RED_FLAG_CHARS = 5000
MAX_COMPARISON_CHARS = 5000
MAX_PROMPT_CHARS = 14000

# Keep generated narrative concise.
MIN_SUMMARY_CHARS = 250
MIN_OUTLOOK_CHARS = 200


# ============================================================================
# JSON PARSING
# ============================================================================

def _extract_json(raw: str) -> dict:
    """
    Extract a JSON object from an LLM response.

    Handles:
        - plain JSON
        - ```json fenced JSON
        - text surrounding JSON
    """

    text = str(raw or "").strip()

    # Remove opening markdown fence.
    text = re.sub(
        r"^```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Remove closing markdown fence.
    text = re.sub(
        r"```$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Find JSON object.
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
# TEXT LIMITER
# ============================================================================

def _limit_text(text: str, max_chars: int) -> str:
    """
    Prevent unnecessarily large prompts from being sent to Ollama.
    """

    text = str(text or "").strip()

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n[Additional context omitted for report speed.]"
    )


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

    # Only send the most important risks to the narrative LLM.
    # The full red-flag data remains available elsewhere in the report.
    flags = red_flags.flags[:5]

    for index, flag in enumerate(flags, start=1):

        lines.append(
            f"""
Risk {index}
Category: {flag.category or 'N/A'}
Severity: {flag.severity or 'N/A'}
Title: {flag.title or 'Unnamed risk'}
Explanation: {flag.explanation or 'N/A'}
Evidence: {flag.evidence or 'N/A'}
Source Page: {flag.page_number or 'N/A'}
""".strip()
        )

    return _limit_text(
        "\n\n".join(lines),
        MAX_RED_FLAG_CHARS,
    )


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

    # Limit the amount of comparison data passed to the LLM.
    for comp in comparisons[:3]:

        tickers = list(comp.tickers or [])

        lines = [
            f"Comparison Group: {', '.join(tickers) or 'N/A'}"
        ]

        # ---------------------------------------------------------------
        # Ratios
        # ---------------------------------------------------------------

        for ratio in (comp.ratio_comparisons or [])[:5]:

            lines.append(
                f"\nRatio: {ratio.ratio_name}"
            )

            values = ratio.values or {}

            for ticker in tickers:
                if ticker in values:
                    lines.append(
                        f"  {ticker}: {_number(values[ticker])}"
                    )

            if ratio.industry_average is not None:
                lines.append(
                    "  Industry Average: "
                    f"{_number(ratio.industry_average)}"
                )

        # ---------------------------------------------------------------
        # Rankings
        # ---------------------------------------------------------------

        if comp.industry_rankings:

            lines.append("\nIndustry Rankings:")

            rankings = sorted(
                comp.industry_rankings,
                key=lambda item: item.rank,
            )

            for rank in rankings[:5]:

                score_text = ""

                if rank.score is not None:
                    score_text = (
                        f", Score: {_number(rank.score)}"
                    )

                lines.append(
                    f"  #{rank.rank} "
                    f"{rank.ticker}"
                    f"{score_text}"
                )

        # ---------------------------------------------------------------
        # Trend
        # ---------------------------------------------------------------

        if comp.trend_analysis:

            lines.append("\nTrend Data:")

            for point in comp.trend_analysis[:5]:

                lines.append(
                    f"  Period: {point.period}, "
                    f"Ticker: {point.ticker}, "
                    f"Value: {_number(point.value)}"
                )

        # ---------------------------------------------------------------
        # Existing summary
        # ---------------------------------------------------------------

        if comp.summary:
            lines.append(
                "\nExisting Comparison Summary:"
            )

            lines.append(
                _limit_text(
                    str(comp.summary),
                    1500,
                )
            )

        sections.append("\n".join(lines))

    return _limit_text(
        "\n\n".join(sections),
        MAX_COMPARISON_CHARS,
    )


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
    Fast deterministic fallback.

    Used if Ollama is unavailable or returns invalid JSON.
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

    year = (
        extraction.get("fiscal_year")
        or "the reported fiscal year"
    )

    summary_parts = []

    # Basic financial profile.
    summary_parts.append(
        f"{company.name} ({company.ticker}) reported "
        f"revenue of {_money(revenue)} and net profit of "
        f"{_money(net_profit)} in FY {year}."
    )

    if margin is not None:
        summary_parts.append(
            f"The reported net profit margin was "
            f"{_percent(margin)}."
        )

    if assets is not None and liabilities is not None:
        summary_parts.append(
            f"The balance sheet included total assets of "
            f"{_money(assets)} against liabilities of "
            f"{_money(liabilities)}."
        )

    if debt_equity is not None:
        summary_parts.append(
            f"The reported debt-to-equity ratio was "
            f"{_ratio(debt_equity)}."
        )

    if cash_flow is not None:
        summary_parts.append(
            f"Reported cash flow was {_money(cash_flow)}."
        )

    if eps is not None:
        summary_parts.append(
            f"EPS was {_number(eps)}."
        )

    # Risk information.
    if red_flags and red_flags.flags:

        high_risks = [
            flag
            for flag in red_flags.flags
            if str(flag.severity or "").upper() == "HIGH"
        ]

        if high_risks:
            summary_parts.append(
                f"The risk assessment identifies "
                f"{len(high_risks)} high-severity issue(s) "
                f"requiring particular attention."
            )
        else:
            summary_parts.append(
                f"The red-flag assessment identifies "
                f"{len(red_flags.flags)} issue(s) requiring "
                f"continued monitoring."
            )

    if comparisons:
        summary_parts.append(
            "Available peer comparison data provides additional "
            "context for evaluating the company's financial position."
        )

    executive_summary = " ".join(summary_parts)

    # ------------------------------------------------------------
    # Outlook
    # ------------------------------------------------------------

    outlook_parts = [
        "The near-term assessment should focus on reported "
        "profitability, cash generation and balance-sheet position."
    ]

    if margin is not None:
        outlook_parts.append(
            f"Future reporting periods should be evaluated against "
            f"the current net profit margin of {_percent(margin)}."
        )

    if debt_equity is not None:
        outlook_parts.append(
            f"The debt-to-equity ratio of {_ratio(debt_equity)} "
            f"should remain an important leverage reference point."
        )

    if red_flags and red_flags.flags:

        titles = [
            str(flag.title)
            for flag in red_flags.flags[:3]
            if flag.title
        ]

        if titles:
            outlook_parts.append(
                "Attention should remain on the identified risk areas, "
                "including "
                + ", ".join(titles)
                + "."
            )

    if comparisons:
        outlook_parts.append(
            "Peer comparison can continue to provide context as "
            "additional financial information becomes available."
        )

    outlook_parts.append(
        "Subsequent reporting periods should be reviewed against "
        "the same financial and risk measures."
    )

    outlook = " ".join(outlook_parts)

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

    # Do NOT require 500+ characters.
    # A concise professional report is acceptable.
    if len(summary.strip()) < MIN_SUMMARY_CHARS:
        return False

    if len(outlook.strip()) < MIN_OUTLOOK_CHARS:
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
    """
    Generate the Report Agent narrative.

    Exactly ONE LLM call is attempted.

    If the call fails or produces invalid JSON,
    deterministic fallback is returned immediately.
    """

    start_time = time.perf_counter()

    # ================================================================
    # Build compact context
    # ================================================================

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

    # ================================================================
    # Build prompt
    # ================================================================

    prompt = REPORT_TASK_DESCRIPTION.format(
        **context
    )

    # Final safety limit.
    prompt = _limit_text(
        prompt,
        MAX_PROMPT_CHARS,
    )

    prompt_build_time = time.perf_counter() - start_time

    print(
        f"[Report Agent] Prompt preparation: "
        f"{prompt_build_time:.2f}s | "
        f"{len(prompt):,} chars"
    )

    # ================================================================
    # ONE LLM CALL
    # ================================================================

    def _call_llm() -> str:

        return llm.call(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior financial research analyst. "
                        "Return ONLY valid JSON. "
                        "Do not use markdown. "
                        "Do not mention AI, automation, prompts or models. "
                        "Use ONLY the financial information supplied. "
                        "Do not invent or calculate new numbers. "
                        "\n\n"
                        "Return exactly this structure: "
                        '{"executive_summary":"...",'
                        '"outlook":"..."}'
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

    llm_start = time.perf_counter()

    try:

        raw_output = await run_in_threadpool(
            _call_llm
        )

        llm_time = time.perf_counter() - llm_start

        print(
            f"[Report Agent] LLM generation: "
            f"{llm_time:.2f}s"
        )

    except Exception as exc:

        total_time = time.perf_counter() - start_time

        print(
            "[Report Agent] LLM unavailable. "
            f"Using deterministic fallback. "
            f"Error: {exc}"
        )

        print(
            f"[Report Agent] Total time: "
            f"{total_time:.2f}s"
        )

        return _fallback_narrative(
            company,
            extraction,
            red_flags,
            comparisons,
        )

    # ================================================================
    # Parse JSON
    # ================================================================

    parse_start = time.perf_counter()

    try:

        parsed = _extract_json(
            str(raw_output)
        )

        if _valid_narrative(parsed):

            total_time = time.perf_counter() - start_time
            parse_time = time.perf_counter() - parse_start

            print(
                f"[Report Agent] JSON parsing: "
                f"{parse_time:.2f}s"
            )

            print(
                f"[Report Agent] TOTAL: "
                f"{total_time:.2f}s"
            )

            return {
                "executive_summary": (
                    parsed["executive_summary"].strip()
                ),
                "outlook": (
                    parsed["outlook"].strip()
                ),
            }

        print(
            "[Report Agent] LLM returned JSON, "
            "but narrative did not meet minimum requirements."
        )

    except (
        ValueError,
        json.JSONDecodeError,
        TypeError,
    ) as exc:

        print(
            "[Report Agent] Invalid JSON returned by LLM: "
            f"{exc}"
        )

    # ================================================================
    # FALLBACK
    # ================================================================

    total_time = time.perf_counter() - start_time

    print(
        f"[Report Agent] Using deterministic fallback. "
        f"TOTAL: {total_time:.2f}s"
    )

    return _fallback_narrative(
        company,
        extraction,
        red_flags,
        comparisons,
    )