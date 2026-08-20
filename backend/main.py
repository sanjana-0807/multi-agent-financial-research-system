from contextlib import asynccontextmanager
from fastapi import FastAPI

from database.mongo_client import init_db

from routes import companies
from routes import auth
from routes import research
from routes import comparison
from routes import documents
from routes import extraction
from routes import red_flag

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
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(auth.router)
app.include_router(research.router)
app.include_router(comparison.router)
app.include_router(documents.router)
app.include_router(extraction.router)
app.include_router(red_flag.router)

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