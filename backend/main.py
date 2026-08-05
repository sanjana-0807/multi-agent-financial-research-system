from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.extraction import router as extraction_router

app = FastAPI(
    title="Multi-Agent Financial Research API",
    description="Backend API for the multi-agent financial research system",
    version="0.1.0",
)

# CORS — allow the Vite dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(extraction_router)

# Add other team routers here as they become available:
# from routes.research import router as research_router
# from routes.comparison import router as comparison_router
# app.include_router(research_router)
# app.include_router(comparison_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
