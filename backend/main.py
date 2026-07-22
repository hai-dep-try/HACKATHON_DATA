"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="hackathon_data API", version="0.1.0")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return liveness state without checking external dependencies."""

    return {"status": "ok"}
