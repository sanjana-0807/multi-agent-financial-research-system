from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.mongo_client import init_db

from routes import companies
from routes import auth
from routes import research
from routes import comparison
from routes import documents
from routes import extraction
from routes import red_flag
from routes import workspace
from routes import research_chat


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


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API ROUTERS
# ---------------------------------------------------------

app.include_router(companies.router)
app.include_router(auth.router)
app.include_router(research.router)
app.include_router(comparison.router)
app.include_router(documents.router)
app.include_router(extraction.router)
app.include_router(red_flag.router)
app.include_router(workspace.router)

# Research Chat
app.include_router(research_chat.router)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to Multi-Agent Financial Research System Backend"
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }