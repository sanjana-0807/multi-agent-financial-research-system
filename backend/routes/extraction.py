from fastapi import APIRouter, HTTPException
from agents.extraction_agent.tasks import run_extraction
from agents.extraction_agent.document_fetcher import fetch_document_text
from schemas.extraction_schema import ExtractionResponse, ExtractionRequest

router = APIRouter(prefix="/api", tags=["extraction"])


@router.get("/extract/{document_id}", response_model=ExtractionResponse)
def get_extraction(document_id: str):
    document_text = fetch_document_text(document_id)
    if document_text is None:
        raise HTTPException(status_code=404, detail="document not found")

    result = run_extraction(document_text, document_id=document_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/extract", response_model=ExtractionResponse)
def post_extraction(req: ExtractionRequest):
    return get_extraction(req.document_id)