# routes/extraction.py
from fastapi import APIRouter, HTTPException, Depends

from agents.extraction_agent.tasks import run_extraction
from agents.extraction_agent.document_fetcher import fetch_document_text
from schemas.extraction_schema import ExtractionResponse, ExtractionRequest
from core.dependencies import get_current_user

router = APIRouter(prefix="/extraction", tags=["Extraction"])


@router.get("/{document_id}", response_model=ExtractionResponse)
def get_extraction(document_id: str, current_user=Depends(get_current_user)):
    """
    Runs financial-metric extraction against a document already indexed
    by the Document Agent (see routes/documents.py). The document must
    have been uploaded and processed first -- this reads its chunks back
    out of ChromaDB by document_id.

    NOTE: this is a synchronous ("def", not "async def") route on
    purpose. It calls out to the Anthropic API via CrewAI, which can
    take several seconds. FastAPI automatically runs sync route handlers
    in a worker thread pool, so this does not block the event loop the
    way a blocking call inside an "async def" route would.
    """
    document_text = fetch_document_text(document_id)
    if document_text is None:
        raise HTTPException(status_code=404, detail="document not found")

    result = run_extraction(document_text, document_id=document_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/run", response_model=ExtractionResponse)
def post_extraction(req: ExtractionRequest, current_user=Depends(get_current_user)):
    return get_extraction(req.document_id, current_user=current_user)