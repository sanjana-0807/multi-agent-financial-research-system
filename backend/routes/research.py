from fastapi import APIRouter, HTTPException

from backend.agents.extraction_agent.document_fetcher import (
    fetch_document_text
)
from backend.agents.extraction_agent.tasks import run_extraction

from models.extracted_metric import ExtractedMetric


router = APIRouter(
    prefix="/research",
    tags=["Research"]
)


# ============================================================
# EXTRACT FINANCIAL METRICS
# ============================================================

@router.post("/extract/{document_id}")
async def extract_financial_metrics(document_id: str):

    # --------------------------------------------------------
    # Fetch document
    # --------------------------------------------------------

    document_text = fetch_document_text(document_id)

    if document_text is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:

        # ----------------------------------------------------
        # Run extraction
        # ----------------------------------------------------

        result = run_extraction(
            document_text=document_text,
            document_id=document_id
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Financial extraction returned no result"
            )

        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )

        # ----------------------------------------------------
        # SAVE / UPDATE MONGODB
        # ----------------------------------------------------

        metric_id = result.get(
            "metric_id",
            f"M_{document_id}"
        )

        existing_metric = await ExtractedMetric.find_one(
            ExtractedMetric.document_id == document_id
        )

        if existing_metric:

            # Update the existing MongoDB document
            existing_metric.metric_id = metric_id
            existing_metric.document_id = document_id

            existing_metric.company = result.get(
                "company"
            )

            existing_metric.fiscal_year = result.get(
                "fiscal_year"
            )

            existing_metric.revenue = result.get(
                "revenue"
            )

            existing_metric.net_profit = result.get(
                "net_profit"
            )

            existing_metric.assets = result.get(
                "assets"
            )

            existing_metric.liabilities = result.get(
                "liabilities"
            )

            existing_metric.cash_flow = result.get(
                "cash_flow"
            )

            existing_metric.eps = result.get(
                "eps"
            )

            existing_metric.ratios = result.get(
                "ratios",
                {}
            )

            await existing_metric.save()

            saved_metric = existing_metric

        else:

            # Create a new MongoDB document
            saved_metric = ExtractedMetric(
                metric_id=metric_id,
                document_id=document_id,

                company=result.get(
                    "company"
                ),

                fiscal_year=result.get(
                    "fiscal_year"
                ),

                revenue=result.get(
                    "revenue"
                ),

                net_profit=result.get(
                    "net_profit"
                ),

                assets=result.get(
                    "assets"
                ),

                liabilities=result.get(
                    "liabilities"
                ),

                cash_flow=result.get(
                    "cash_flow"
                ),

                eps=result.get(
                    "eps"
                ),

                ratios=result.get(
                    "ratios",
                    {}
                ),
            )

            await saved_metric.insert()

        # ----------------------------------------------------
        # Return the saved data
        # ----------------------------------------------------

        saved_data = saved_metric.model_dump()

        if saved_data.get("id") is not None:
            saved_data["id"] = str(
                saved_data["id"]
            )

        return {
            "success": True,
            "data": {
                "message": "Financial metrics extracted successfully",
                "data": saved_data
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Financial extraction failed: {str(e)}"
        )


# ============================================================
# GET FINANCIAL METRICS
# ============================================================

@router.get("/metrics/{document_id}")
async def get_financial_metrics(document_id: str):

    try:

        metric = await ExtractedMetric.find_one(
            ExtractedMetric.document_id == document_id
        )

        if not metric:
            raise HTTPException(
                status_code=404,
                detail="Financial metrics not found"
            )

        data = metric.model_dump()

        # Convert MongoDB ObjectId to string
        if data.get("id") is not None:
            data["id"] = str(
                data["id"]
            )

        return {
            "success": True,
            "data": data
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve financial metrics: {str(e)}"
        )