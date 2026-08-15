import re
from chromadb_helper import search_embedding


class ExtractionAgent:

    @staticmethod
    def extract_financial_metrics(document_id: str):

        query = """
        Extract the following financial metrics:
        revenue,
        net profit,
        total assets,
        total liabilities,
        cash flow,
        EPS,
        fiscal year,
        company name.
        """

        results = search_embedding(
            query,
            document_id=document_id,
            n_results=3
        )

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        relevant_chunks = []

        for i in range(len(ids)):

            metadata = metadatas[i] if i < len(metadatas) else {}

            if metadata.get("document_id") != document_id:
                continue

            text = documents[i] if i < len(documents) else ""
            distance = distances[i] if i < len(distances) else None

            relevant_chunks.append({
                "chunk_id": metadata.get("chunk_id"),
                "text": text,
                "metadata": metadata,
                "distance": distance
            })

        # Combine all retrieved text
        full_text = " ".join(
            chunk["text"] for chunk in relevant_chunks
        )

        # ------------------------------------------------
        # Company
        # ------------------------------------------------

        company = None

        company_match = re.search(
            r"\b(Tesla|Microsoft|Apple|Amazon|Google|NVIDIA)\b",
            full_text,
            re.IGNORECASE
        )

        if company_match:
            company = company_match.group(1)

        # ------------------------------------------------
        # Fiscal Year
        # ------------------------------------------------

        fiscal_year = None

        year_match = re.search(
            r"\b(20\d{2})\b",
            full_text
        )

        if year_match:
            fiscal_year = int(year_match.group(1))

        # ------------------------------------------------
        # Revenue
        # ------------------------------------------------

        revenue = None

        match = re.search(
            r"(?:reported\s+)?revenue\s+"
            r"(?:was|were|of|increased\s+to|increased\s+by)?\s*"
            r"(?:₹|\$)?\s*([\d,]+(?:\.\d+)?)",
            full_text,
            re.IGNORECASE
        )

        if match:
            revenue = float(match.group(1).replace(",", ""))

        # ------------------------------------------------
        # Net Profit
        # ------------------------------------------------

        net_profit = None

        match = re.search(
            r"net\s+profit\s+"
            r"(?:was|were|of|increased\s+to)?\s*"
            r"(?:₹|\$)?\s*([\d,]+(?:\.\d+)?)",
            full_text,
            re.IGNORECASE
        )

        if match:
            net_profit = float(match.group(1).replace(",", ""))

        # ------------------------------------------------
        # Total Assets
        # ------------------------------------------------

        assets = None

        match = re.search(
            r"(?:total\s+)?assets\s+"
            r"(?:were|was|of|increased\s+to)?\s*"
            r"(?:₹|\$)?\s*([\d,]+(?:\.\d+)?)",
            full_text,
            re.IGNORECASE
        )

        if match:
            assets = float(match.group(1).replace(",", ""))

        # ------------------------------------------------
        # Total Liabilities
        # ------------------------------------------------

        liabilities = None

        match = re.search(
            r"(?:total\s+)?liabilities\s+"
            r"(?:were|was|of|increased\s+to)?\s*"
            r"(?:₹|\$)?\s*([\d,]+(?:\.\d+)?)",
            full_text,
            re.IGNORECASE
        )

        if match:
            liabilities = float(match.group(1).replace(",", ""))

        # ------------------------------------------------
        # Cash Flow
        # ------------------------------------------------

        cash_flow = None

        match = re.search(
            r"cash\s+flow\s+"
            r"(?:was|were|of|increased\s+to)?\s*"
            r"(?:₹|\$)?\s*([\d,]+(?:\.\d+)?)",
            full_text,
            re.IGNORECASE
        )

        if match:
            cash_flow = float(match.group(1).replace(",", ""))

        # ------------------------------------------------
        # EPS
        # ------------------------------------------------

        eps = None

        match = re.search(
            r"(?:EPS|earnings\s+per\s+share)\s*"
            r"(?:was|were|of|increased\s+to)?\s*"
            r"(?:₹|\$)?\s*([\d,]+(?:\.\d+)?)",
            full_text,
            re.IGNORECASE
        )

        if match:
            eps = float(match.group(1).replace(",", ""))

        # ------------------------------------------------
        # Final Result
        # ------------------------------------------------

        return {
            "document_id": document_id,
            "company": company,
            "fiscal_year": fiscal_year,
            "revenue": revenue,
            "net_profit": net_profit,
            "assets": assets,
            "liabilities": liabilities,
            "cash_flow": cash_flow,
            "eps": eps,
            "chunks": relevant_chunks
        }