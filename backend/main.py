"""FastAPI application entry point."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from agents.common.models import (
    ExperienceLevel,
    LocationType,
    OpportunityRecord,
    OpportunityType,
)
from backend.repository import InMemoryOpportunityRepository, OpportunityRepository

app = FastAPI(title="hackathon_data API", version="0.1.0")

# Global default instance for development
_default_repo = InMemoryOpportunityRepository()


def get_repository() -> OpportunityRepository:
    """Dependency to provide the active repository."""
    return _default_repo


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return liveness state without checking external dependencies."""
    return {"status": "ok"}


@app.get("/opportunities", tags=["opportunities"])
def list_opportunities(
    repo: Annotated[OpportunityRepository, Depends(get_repository)],
    opportunity_type: OpportunityType | None = None,
    experience_level: ExperienceLevel | None = None,
    location_type: LocationType | None = None,
) -> list[OpportunityRecord]:
    """List opportunities, optionally filtered by type, level, or location."""
    return repo.list_opportunities(
        opportunity_type=opportunity_type,
        experience_level=experience_level,
        location_type=location_type,
    )


@app.get("/opportunities/{content_hash}", tags=["opportunities"])
def get_opportunity(
    content_hash: str,
    repo: Annotated[OpportunityRepository, Depends(get_repository)],
) -> OpportunityRecord:
    """Get a single opportunity by its exact content hash."""
    record = repo.get_opportunity(content_hash)
    if record is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return record
