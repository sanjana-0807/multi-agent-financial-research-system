from contextlib import asynccontextmanager
from fastapi import FastAPI

from database.mongo_client import init_db
from routes import companies
from routes import auth
from routes import research
from routes import documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MongoDB and initialize Beanie document models
    await init_db()
    yield


app = FastAPI(
    title="Multi-Agent Financial Research System",
    description="Backend API for Multi-Agent Financial Research System",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(companies.router)
app.include_router(auth.router)
app.include_router(research.router)
app.include_router(documents.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Multi-Agent Financial Research System Backend"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }