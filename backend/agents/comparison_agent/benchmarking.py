# agents/comparison_agent/benchmarking.py
"""
Deterministic, non-LLM numeric comparison across companies.

Takes ExtractionResponse-shaped dicts (see agents/extraction_agent) for
each company and builds the RatioComparison / IndustryRanking objects
stored on ComparisonResult. Every number here is traceable directly
back to what the Extraction Agent pulled out of the source document --
the LLM step in crew.py only ever narrates what this module computes,
it never calculates anything itself.
"""
from models.comparison_result import RatioComparison, IndustryRanking

# Metrics pulled straight off the extraction result.
RAW_METRICS = [
    "revenue", "net_profit", "assets", "liabilities", "cash_flow", "eps",
]

# Ratios already computed by the Extraction Agent (see
# agents/extraction_agent/tasks.py:calculate_ratios).
RATIO_METRICS = ["current_ratio", "debt_to_equity", "net_profit_margin"]

# Metrics where a LOWER value is the stronger position.
LOWER_IS_BETTER = {"liabilities", "debt_to_equity"}


def _metric_value(extraction: dict, metric: str):
    if metric in RATIO_METRICS:
        return (extraction.get("ratios") or {}).get(metric)
    return extraction.get(metric)


def build_ratio_comparisons(
    extractions: dict[str, dict],
) -> list[RatioComparison]:
    """
    extractions: ticker -> ExtractionResponse dict.
    Skips a metric entirely if no company has a value for it, and
    skips a company within a metric if that company's value is None
    (e.g. EPS wasn't extractable for that filing).
    """
    comparisons: list[RatioComparison] = []

    for metric in RAW_METRICS + RATIO_METRICS:
        values: dict[str, float] = {}

        for ticker, extraction in extractions.items():
            value = _metric_value(extraction, metric)
            if value is not None:
                values[ticker] = float(value)

        if not values:
            continue

        if metric in LOWER_IS_BETTER:
            best_performer = min(values, key=values.get)
        else:
            best_performer = max(values, key=values.get)

        industry_average = round(sum(values.values()) / len(values), 4)

        comparisons.append(
            RatioComparison(
                ratio_name=metric,
                values=values,
                industry_average=industry_average,
                best_performer=best_performer,
            )
        )

    return comparisons


def build_rankings(
    extractions: dict[str, dict],
    ratio_comparisons: list[RatioComparison],
) -> list[IndustryRanking]:
    """
    Rank-sum composite score: for every metric, the best-placed company
    earns N points (N = number of companies in that metric), the
    worst earns 1. Points are summed across all metrics so differing
    scales (revenue in billions vs. a 0-2 ratio) never distort the
    overall ranking the way summing raw values would.
    """
    tickers = list(extractions.keys())
    scores: dict[str, float] = {ticker: 0.0 for ticker in tickers}

    for comparison in ratio_comparisons:
        lower_is_better = comparison.ratio_name in LOWER_IS_BETTER
        ranked = sorted(
            comparison.values.items(),
            key=lambda item: item[1],
            reverse=not lower_is_better,
        )
        n = len(ranked)
        for position, (ticker, _value) in enumerate(ranked):
            scores[ticker] = scores.get(ticker, 0.0) + (n - position)

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    return [
        IndustryRanking(ticker=ticker, rank=idx + 1, score=round(score, 2))
        for idx, (ticker, score) in enumerate(ordered)
    ]


def format_comparison_context(
    companies_by_ticker: dict[str, str],
    ratio_comparisons: list[RatioComparison],
    rankings: list[IndustryRanking],
) -> str:
    """
    Renders the already-computed numeric comparison as compact text
    for the Comparison Agent's LLM step (agents/comparison_agent/crew.py).
    The LLM only ever sees these numbers -- it never sees raw document
    text and cannot introduce a figure that isn't already here.
    """
    lines = ["COMPANIES:"]
    for ticker, name in companies_by_ticker.items():
        lines.append(f"- {ticker}: {name}")

    lines.append("\nMETRIC COMPARISON:")
    for comparison in ratio_comparisons:
        lines.append(f"\n{comparison.ratio_name}:")
        for ticker, value in comparison.values.items():
            lines.append(f"  {ticker}: {value}")
        lines.append(f"  industry_average: {comparison.industry_average}")
        lines.append(f"  best_performer: {comparison.best_performer}")

    lines.append("\nOVERALL RANKING (rank 1 = strongest composite):")
    for ranking in sorted(rankings, key=lambda r: r.rank):
        lines.append(f"  {ranking.rank}. {ranking.ticker} (score={ranking.score})")

    return "\n".join(lines)