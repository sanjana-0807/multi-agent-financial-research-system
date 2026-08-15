from fastapi import APIRouter, HTTPException

from research_agent.research_service import ResearchService
from models.extracted_metric import ExtractedMetric


router = APIRouter(
    prefix="/research",
    tags=["Research"]
)


# -----------------------------------
# Research Home
# -----------------------------------

@router.get("/")
async def research_home():
    return {
        "message": "Research API is working"
    }


# -----------------------------------
# Extract Financial Metrics
# -----------------------------------

@router.post("/extract/{document_id}")
async def extract_metrics(document_id: str):

    try:

        result = await ResearchService.extract(document_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------------
# Get Saved Financial Metrics
# -----------------------------------

@router.get("/metrics/{document_id}")
async def get_metrics(document_id: str):

    try:

        metric = await ExtractedMetric.find_one(
            ExtractedMetric.document_id == document_id
        )

        if not metric:

            raise HTTPException(
                status_code=404,
                detail="Financial metrics not found"
            )

        return {
            "success": True,
            "data": {
                "metric_id": metric.metric_id,
                "document_id": metric.document_id,
                "company": metric.company,
                "fiscal_year": metric.fiscal_year,
                "revenue": metric.revenue,
                "net_profit": metric.net_profit,
                "assets": metric.assets,
                "liabilities": metric.liabilities,
                "cash_flow": metric.cash_flow,
                "eps": metric.eps,
                "ratios": metric.ratios
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------------
# Get Red Flags
# -----------------------------------

@router.get("/red-flags/{document_id}")
async def get_red_flags(document_id: str):

    try:

        result = await ResearchService.red_flags(document_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )