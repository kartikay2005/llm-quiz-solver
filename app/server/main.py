"""FastAPI main application."""
from fastapi import FastAPI
from app.server.router import router

app = FastAPI(title="LLM Analysis Quiz Solver")
app.include_router(router)


@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"status": "ok"}
