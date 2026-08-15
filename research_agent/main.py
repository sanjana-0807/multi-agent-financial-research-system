from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

from models.extracted_metric import ExtractedMetric
from models.red_flag import RedFlag

from routes.research_routes import router as research_router


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Connect to MongoDB
    client = AsyncIOMotorClient(
        os.getenv("MONGO_URI")
    )

    database = client[os.getenv("DATABASE_NAME")]

    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[
            ExtractedMetric,
            RedFlag
        ]
    )

    print("Beanie MongoDB initialized successfully!")

    yield

    # Close MongoDB connection
    client.close()


app = FastAPI(
    title="Financial Research API",
    description="Financial document extraction and research API",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(research_router)


@app.get("/")
def root():

    return {
        "message": "Financial Research API is running"
    }