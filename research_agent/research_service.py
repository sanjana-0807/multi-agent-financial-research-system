from agent.extraction_agent import ExtractionAgent

from models.extracted_metric import ExtractedMetric
from models.red_flag import RedFlag


class ResearchService:

    # =========================================================
    # EXTRACT FINANCIAL METRICS
    # =========================================================

    @staticmethod
    async def extract(document_id: str):

        # Get financial data from Extraction Agent
        result = ExtractionAgent.extract_financial_metrics(document_id)

        # Check whether metrics already exist
        existing_metric = await ExtractedMetric.find_one(
            ExtractedMetric.document_id == document_id
        )

        # -----------------------------------------------------
        # UPDATE EXISTING METRIC
        # -----------------------------------------------------

        if existing_metric:

            existing_metric.company = result.get("company")
            existing_metric.fiscal_year = result.get("fiscal_year")
            existing_metric.revenue = result.get("revenue")
            existing_metric.net_profit = result.get("net_profit")
            existing_metric.assets = result.get("assets")
            existing_metric.liabilities = result.get("liabilities")
            existing_metric.cash_flow = result.get("cash_flow")
            existing_metric.eps = result.get("eps")

            # Calculate net profit margin
            revenue = result.get("revenue")
            net_profit = result.get("net_profit")

            if revenue and revenue != 0 and net_profit is not None:
                existing_metric.ratios["net_profit_margin"] = (
                    net_profit / revenue
                ) * 100

            await existing_metric.save()

            return {
                "message": "Financial metrics updated successfully",
                "data": result
            }

        # -----------------------------------------------------
        # CREATE NEW METRIC
        # -----------------------------------------------------

        revenue = result.get("revenue")
        net_profit = result.get("net_profit")

        net_profit_margin = 0.0

        if revenue and revenue != 0 and net_profit is not None:
            net_profit_margin = (
                net_profit / revenue
            ) * 100

        metric = ExtractedMetric(
            metric_id=f"M_{document_id}",
            document_id=document_id,
            company=result.get("company"),
            fiscal_year=result.get("fiscal_year"),
            revenue=revenue,
            net_profit=net_profit,
            assets=result.get("assets"),
            liabilities=result.get("liabilities"),
            cash_flow=result.get("cash_flow"),
            eps=result.get("eps"),

            ratios={
                "current_ratio": 0.0,
                "debt_to_equity": 0.0,
                "net_profit_margin": net_profit_margin
            }
        )

        await metric.insert()

        return {
            "message": "Financial metrics extracted successfully",
            "data": result
        }


    # =========================================================
    # RED FLAGS
    # =========================================================

    @staticmethod
    async def red_flags(document_id: str):

        # Find existing red flag record
        existing_flag = await RedFlag.find_one(
            RedFlag.document_id == document_id
        )

        # -----------------------------------------------------
        # Get financial metrics
        # -----------------------------------------------------

        metric = await ExtractedMetric.find_one(
            ExtractedMetric.document_id == document_id
        )

        if metric is None:

            return {
                "document_id": document_id,
                "company": None,
                "risk_level": "Unknown",
                "red_flags": [
                    "Financial metrics have not been extracted yet."
                ]
            }

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
            ) * 100

            if liability_ratio > 80:

                red_flags.append(
                    "Liabilities are high compared with total assets."
                )

                risk_level = "High"

            elif liability_ratio > 50:

                red_flags.append(
                    "Liabilities are moderately high compared with total assets."
                )

                risk_level = "Medium"


        # -----------------------------------------------------
        # Check net profit
        # -----------------------------------------------------

        if (
            metric.net_profit is not None
            and metric.net_profit < 0
        ):

            red_flags.append(
                "Company reported a negative net profit."
            )

            risk_level = "High"


        # -----------------------------------------------------
        # Check revenue
        # -----------------------------------------------------

        if metric.revenue is None:

            red_flags.append(
                "Revenue information is missing."
            )

            if risk_level == "Low":
                risk_level = "Medium"


        # -----------------------------------------------------
        # No problems detected
        # -----------------------------------------------------

        if not red_flags:

            red_flags.append(
                "No significant accounting anomalies detected."
            )


        # -----------------------------------------------------
        # SAVE / UPDATE RED FLAGS
        # -----------------------------------------------------

        if existing_flag:

            existing_flag.company = metric.company
            existing_flag.risk_level = risk_level
            existing_flag.red_flags = red_flags

            await existing_flag.save()

        else:

            flag = RedFlag(
                flag_id=f"RF_{document_id}",
                document_id=document_id,
                company=metric.company,
                risk_level=risk_level,
                red_flags=red_flags
            )

            await flag.insert()


        # -----------------------------------------------------
        # RETURN RESULT
        # -----------------------------------------------------

        return {
            "document_id": document_id,
            "company": metric.company,
            "risk_level": risk_level,
            "red_flags": red_flags
        }