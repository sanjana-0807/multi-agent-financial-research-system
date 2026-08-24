from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

# ============================================================
# ROUTES
# ============================================================

from backend.routes.research import router as research_router

# ============================================================
# MODELS
# ============================================================

from backend.models.red_flag import RedFlagResult
from models.extracted_metric import ExtractedMetric
from models.red_flag import RedFlag

# ============================================================
# SERVICES
# ============================================================

from backend.services.red_flag_service import run_red_flag_analysis


load_dotenv()


# ============================================================
# MONGODB LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting Financial Research API...")

    # --------------------------------------------------------
    # Environment variables
    # --------------------------------------------------------

    mongo_uri = os.getenv("MONGO_URI")
    database_name = os.getenv("DATABASE_NAME")

    if not mongo_uri:
        raise RuntimeError(
            "MONGO_URI is not set in .env"
        )

    if not database_name:
        raise RuntimeError(
            "DATABASE_NAME is not set in .env"
        )

    # --------------------------------------------------------
    # MongoDB connection
    # --------------------------------------------------------

    client = AsyncIOMotorClient(mongo_uri)

    database = client[database_name]

    # --------------------------------------------------------
    # Beanie initialization
    # --------------------------------------------------------

    await init_beanie(
        database=database,
        document_models=[
            RedFlagResult,
            ExtractedMetric,
            RedFlag,
        ],
    )

    print(
        "Beanie MongoDB initialized successfully!"
    )

    # --------------------------------------------------------
    # Application runs
    # --------------------------------------------------------

    yield

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    client.close()

    print(
        "MongoDB connection closed."
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Financial Research API",
    description=(
        "Financial document extraction "
        "and red-flag analysis API"
    ),
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================
# REGISTER RESEARCH ROUTES
# ============================================================

app.include_router(
    research_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "message": "Financial Research API is running",
        "status": "success",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
    }


# ============================================================
# RED FLAG ANALYSIS
# ============================================================

@app.post(
    "/research/red-flags/{document_id}"
)
async def analyze_red_flags(
    document_id: str
):

    result = await run_red_flag_analysis(
        document_id
    )

    return {
        "success": True,
        "data": result,
    }