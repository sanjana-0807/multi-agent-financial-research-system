from fastapi import FastAPI

app = FastAPI(
    title="Multi-Agent Financial Research System",
    description="Backend API for Multi-Agent Financial Research System",
    version="1.0.0"
)


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