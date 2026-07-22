"""Data access layer for opportunities."""

from typing import Protocol

from agents.common.models import ExperienceLevel, LocationType, OpportunityRecord, OpportunityType


class OpportunityRepository(Protocol):
    """Protocol for reading and writing opportunities."""

    def list_opportunities(
        self,
        opportunity_type: OpportunityType | None = None,
        experience_level: ExperienceLevel | None = None,
        location_type: LocationType | None = None,
    ) -> list[OpportunityRecord]:
        """Return all matching opportunities."""
        ...

    def get_opportunity(self, content_hash: str) -> OpportunityRecord | None:
        """Return a single opportunity by its content hash, or None if not found."""
        ...

    def add_opportunity(self, record: OpportunityRecord) -> None:
        """Add or update an opportunity record."""
        ...


class InMemoryOpportunityRepository:
    """In-memory implementation for testing and development."""

    def __init__(self) -> None:
        self._records: dict[str, OpportunityRecord] = {}

    def list_opportunities(
        self,
        opportunity_type: OpportunityType | None = None,
        experience_level: ExperienceLevel | None = None,
        location_type: LocationType | None = None,
    ) -> list[OpportunityRecord]:
        results = []
        for record in self._records.values():
            if opportunity_type is not None and record.opportunity_type is not opportunity_type:
                continue
            if experience_level is not None and record.experience_level is not experience_level:
                continue
            if location_type is not None and record.location_type is not location_type:
                continue
            results.append(record)
        return results

    def get_opportunity(self, content_hash: str) -> OpportunityRecord | None:
        return self._records.get(content_hash)

    def add_opportunity(self, record: OpportunityRecord) -> None:
        self._records[record.content_hash] = record
