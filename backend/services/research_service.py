from schemas.extraction_schema import ExtractionResponse


class ResearchService:

    @staticmethod
    def extract(document_id: str):

        return ExtractionResponse(
            metric_id="M001",
            document_id=document_id,
            company="Tesla",
            fiscal_year=2025,

            revenue=879891,
            net_profit=74982,
            assets=247489282,
            liabilities=628742,
            cash_flow=82782732,
            eps=847289,

            ratios={
                "current_ratio": 1.8,
                "debt_to_equity": 0.38,
                "net_profit_margin": 18.9,
            },
        )

    @staticmethod
    def red_flags(document_id: str):

        return {
            "document_id": document_id,
            "company": "Tesla",
            "risk_level": "Low",
            "red_flags": [
                "No significant accounting anomalies detected.",
                "Debt-to-equity ratio is within acceptable range."
            ]
        }