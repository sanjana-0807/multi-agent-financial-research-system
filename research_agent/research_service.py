from backend.agents.extraction_agent.document_fetcher import fetch_document_text
from backend.agents.extraction_agent.tasks import run_extraction

from models.extracted_metric import ExtractedMetric
from models.red_flag import RedFlag


class ResearchService:

    # =========================================================
    # EXTRACT FINANCIAL METRICS
    # =========================================================

    @staticmethod
    async def extract(document_id: str):

        # -----------------------------------------------------
        # Fetch document text
        # -----------------------------------------------------

        document_text = fetch_document_text(document_id)

        if not document_text:
            return {
                "message": "Document text not found",
                "data": {
                    "document_id": document_id
                }
            }

        # -----------------------------------------------------
        # Run extraction agent
        # -----------------------------------------------------

        result = run_extraction(
            document_text,
            document_id
        )

        # -----------------------------------------------------
        # Check whether metrics already exist
        # -----------------------------------------------------

        existing_metric = await ExtractedMetric.find_one(
            {"document_id": document_id}
        )

        # =====================================================
        # GET EXTRACTED VALUES
        # =====================================================

        company = result.get("company")
        fiscal_year = result.get("fiscal_year")
        revenue = result.get("revenue")
        net_profit = result.get("net_profit")
        assets = result.get("assets")
        liabilities = result.get("liabilities")
        cash_flow = result.get("cash_flow")
        eps = result.get("eps")

        # =====================================================
        # CALCULATE RATIOS
        # =====================================================

        # -----------------------------------------------------
        # Current Ratio
        #
        # If run_extraction already provides it, use it.
        # Otherwise use 0.0 so the Pydantic model receives
        # a valid number instead of None.
        # -----------------------------------------------------

        current_ratio = result.get("current_ratio")

        if current_ratio is None:
            current_ratio = 0.0

        # -----------------------------------------------------
        # Debt to Equity
        # -----------------------------------------------------

        debt_to_equity = result.get("debt_to_equity")

        if debt_to_equity is None:

            if (
                assets is not None
                and liabilities is not None
            ):

                equity = assets - liabilities

                if equity != 0:
                    debt_to_equity = liabilities / equity

        if debt_to_equity is None:
            debt_to_equity = 0.0

        # -----------------------------------------------------
        # Net Profit Margin
        # -----------------------------------------------------

        net_profit_margin = result.get(
            "net_profit_margin"
        )

        if (
            net_profit_margin is None
            and revenue is not None
            and revenue != 0
            and net_profit is not None
        ):
            net_profit_margin = (
                net_profit / revenue
            ) * 100

        if net_profit_margin is None:
            net_profit_margin = 0.0

        # =====================================================
        # UPDATE EXISTING METRIC
        # =====================================================

        if existing_metric:

            existing_metric.company = company
            existing_metric.fiscal_year = fiscal_year
            existing_metric.revenue = revenue
            existing_metric.net_profit = net_profit
            existing_metric.assets = assets
            existing_metric.liabilities = liabilities
            existing_metric.cash_flow = cash_flow
            existing_metric.eps = eps

            existing_metric.ratios = {
                "current_ratio": float(current_ratio),
                "debt_to_equity": float(debt_to_equity),
                "net_profit_margin": float(net_profit_margin)
            }

            await existing_metric.save()

            return {
                "message": "Financial metrics updated successfully",
                "data": {
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
                        "current_ratio": float(current_ratio),
                        "debt_to_equity": float(debt_to_equity),
                        "net_profit_margin": float(net_profit_margin)
                    }
                }
            }

        # =====================================================
        # CREATE NEW METRIC
        # =====================================================

        metric = ExtractedMetric(
            metric_id=f"M_{document_id}",
            document_id=document_id,
            company=company,
            fiscal_year=fiscal_year,
            revenue=revenue,
            net_profit=net_profit,
            assets=assets,
            liabilities=liabilities,
            cash_flow=cash_flow,
            eps=eps,
            ratios={
                "current_ratio": float(current_ratio),
                "debt_to_equity": float(debt_to_equity),
                "net_profit_margin": float(net_profit_margin)
            }
        )

        await metric.insert()

        return {
            "message": "Financial metrics extracted successfully",
            "data": {
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
                    "current_ratio": float(current_ratio),
                    "debt_to_equity": float(debt_to_equity),
                    "net_profit_margin": float(net_profit_margin)
                }
            }
        }

    # =========================================================
    # RED FLAGS
    # =========================================================

    @staticmethod
    async def red_flags(document_id: str):

        # -----------------------------------------------------
        # Get financial metrics
        # -----------------------------------------------------

        metric = await ExtractedMetric.find_one(
            {"document_id": document_id}
        )

        # -----------------------------------------------------
        # Metrics not available
        # -----------------------------------------------------

        if metric is None:

            return {
                "document_id": document_id,
                "company": None,
                "risk_level": "Unknown",
                "red_flags": [
                    "Financial metrics have not been extracted yet."
                ]
            }

        # =====================================================
        # RED FLAG ANALYSIS
        # =====================================================

        red_flags = []
        risk_level = "Low"

        # -----------------------------------------------------
        # Check liabilities
        # -----------------------------------------------------

        if (
            metric.assets is not None
            and metric.liabilities is not None
            and metric.assets > 0
        ):

            liability_ratio = (
                metric.liabilities / metric.assets
            )

            if liability_ratio > 0.8:

                red_flags.append(
                    "High liabilities compared with total assets."
                )

                risk_level = "High"

            elif liability_ratio > 0.5:

                red_flags.append(
                    "Moderate liabilities compared with total assets."
                )

                if risk_level == "Low":
                    risk_level = "Medium"

        # -----------------------------------------------------
        # Check net profit
        # -----------------------------------------------------

        if metric.net_profit is not None:

            if metric.net_profit < 0:

                red_flags.append(
                    "Company reported a net loss."
                )

                risk_level = "High"

        # -----------------------------------------------------
        # Check revenue
        # -----------------------------------------------------

        if metric.revenue is not None:

            if metric.revenue <= 0:

                red_flags.append(
                    "Revenue is zero or negative."
                )

                risk_level = "High"

        # -----------------------------------------------------
        # Check cash flow
        # -----------------------------------------------------

        if metric.cash_flow is not None:

            if metric.cash_flow < 0:

                red_flags.append(
                    "Negative cash flow detected."
                )

                if risk_level == "Low":
                    risk_level = "Medium"

        # -----------------------------------------------------
        # Check EPS
        # -----------------------------------------------------

        if metric.eps is not None:

            if metric.eps < 0:

                red_flags.append(
                    "Negative earnings per share detected."
                )

                if risk_level == "Low":
                    risk_level = "Medium"

        # -----------------------------------------------------
        # No red flags
        # -----------------------------------------------------

        if not red_flags:

            red_flags.append(
                "No major financial red flags detected."
            )

        # =====================================================
        # RETURN RESULT
        # =====================================================

        return {
            "document_id": document_id,
            "company": metric.company,
            "risk_level": risk_level,
            "red_flags": red_flags,
            "metrics": {
                "revenue": metric.revenue,
                "net_profit": metric.net_profit,
                "assets": metric.assets,
                "liabilities": metric.liabilities,
                "cash_flow": metric.cash_flow,
                "eps": metric.eps,
                "ratios": metric.ratios
            }
        }