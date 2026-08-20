# agents/comparison_agent/data_fetcher.py
"""
Resolves each Company being compared to its most recently indexed
document and runs the Extraction Agent's deterministic pipeline
against it.

There is no persisted metrics store in this project -- extraction is
computed on demand from the document's stored chunks, exactly like
routes/extraction.py does for a single document. This module just does
that once per company being compared.
"""
from typing import Optional

from models.company import Company
from models.document import DocumentModel
from agents.extraction_agent.document_fetcher import fetch_document_text
from agents.extraction_agent.tasks import run_extraction


async def get_latest_document_for_company(
    company: Company,
) -> Optional[DocumentModel]:
    return await DocumentModel.find(
        DocumentModel.company_id == str(company.id),
        DocumentModel.status == "indexed",
    ).sort("-created_at").first_or_none()


async def get_extraction_for_company(company: Company) -> Optional[dict]:
    """
    Returns an ExtractionResponse-shaped dict (see
    schemas/extraction_schema.py) for the company's latest indexed
    document, or None if the company has no linked, processed document.
    """
    document = await get_latest_document_for_company(company)
    if document is None:
        return None

    document_text = fetch_document_text(document.document_id)
    if document_text is None:
        return None

    return run_extraction(document_text, document_id=document.document_id)


async def get_extractions_for_companies(
    companies: list[Company],
) -> tuple[dict[str, dict], list[str]]:
    """
    Returns (extractions, missing_tickers).

    extractions maps ticker -> ExtractionResponse dict for every
    company that had a linked, processed document. missing_tickers
    lists tickers with no linked/processed document -- callers should
    treat this as a hard stop rather than silently comparing partial
    or fabricated data.
    """
    extractions: dict[str, dict] = {}
    missing: list[str] = []

    for company in companies:
        result = await get_extraction_for_company(company)
        if result is None:
            missing.append(company.ticker)
        else:
            extractions[company.ticker] = result

    return extractions, missing