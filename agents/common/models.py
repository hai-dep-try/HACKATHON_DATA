"""Versioned data contracts exchanged between pipeline agents."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class LocationType(StrEnum):
    """Normalized opportunity location categories."""

    HANOI = "hanoi"
    HO_CHI_MINH_CITY = "ho_chi_minh_city"
    ONLINE = "online"
    HYBRID = "hybrid"
    INTERNATIONAL = "international"
    OTHER_VIETNAM = "other_vietnam"
    UNKNOWN = "unknown"


class OpportunityType(StrEnum):
    """Kinds of opportunities supported by the aggregation pipeline."""

    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    TALENT_PROGRAM = "talent_program"
    TRAINEE_PROGRAM = "trainee_program"
    FELLOWSHIP = "fellowship"
    SCHOLARSHIP = "scholarship"
    COMPETITION = "competition"
    BOOTCAMP = "bootcamp"
    OTHER = "other"


class ExperienceLevel(StrEnum):
    """Normalized prior-experience expectations."""

    NO_EXPERIENCE = "no_experience"
    STUDENT = "student"
    NEW_GRADUATE = "new_graduate"
    ENTRY_LEVEL = "entry_level"
    NOT_SPECIFIED = "not_specified"


class RawDocument(BaseModel):
    """Immutable handoff from a scraper to downstream extraction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    url: HttpUrl
    fetched_at: datetime
    status_code: int = Field(ge=100, le=599)
    content_type: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @classmethod
    def from_text(
        cls,
        *,
        source_id: str,
        url: str,
        fetched_at: datetime,
        status_code: int,
        content_type: str,
        text: str,
    ) -> RawDocument:
        """Build a document and derive its stable SHA-256 content hash."""

        return cls(
            source_id=source_id,
            url=url,
            fetched_at=fetched_at,
            status_code=status_code,
            content_type=content_type,
            text=text,
            content_hash=sha256(text.encode("utf-8")).hexdigest(),
        )

    @model_validator(mode="after")
    def validate_timestamp_and_hash(self) -> RawDocument:
        if self.fetched_at.tzinfo is None:
            raise ValueError("fetched_at must include timezone information")
        expected_hash = sha256(self.text.encode("utf-8")).hexdigest()
        if self.content_hash != expected_hash:
            raise ValueError("content_hash does not match text")
        return self


class ScoreBreakdown(BaseModel):
    """Explainable components of a priority score, totaling at most 100."""

    model_config = ConfigDict(extra="forbid")

    location: float = Field(default=0, ge=0, le=30)
    timing: float = Field(default=0, ge=0, le=25)
    technology_fit: float = Field(default=0, ge=0, le=20)
    opportunity: float = Field(default=0, ge=0, le=15)
    source_quality: float = Field(default=0, ge=0, le=10)

    @property
    def total(self) -> float:
        return sum(
            (
                self.location,
                self.timing,
                self.technology_fit,
                self.opportunity,
                self.source_quality,
            )
        )


class OpportunityRecord(BaseModel):
    """Canonical representation of a student or entry-level opportunity."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    source_url: HttpUrl
    source_name: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    canonical_url: HttpUrl | None = None
    opportunity_type: OpportunityType = OpportunityType.HACKATHON
    organizer: str | None = Field(default=None, max_length=300)
    application_url: HttpUrl | None = None
    location_type: LocationType = LocationType.UNKNOWN
    location_text: str | None = None
    target_audiences: list[str] = Field(default_factory=list)
    eligible_majors: list[str] = Field(default_factory=list)
    eligibility_text: str | None = None
    experience_level: ExperienceLevel = ExperienceLevel.NOT_SPECIFIED
    paid: bool | None = None
    compensation_text: str | None = None
    registration_deadline: datetime | None = None
    event_start: datetime | None = None
    event_end: datetime | None = None
    technologies: list[str] = Field(default_factory=list)
    repository_urls: list[HttpUrl] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    priority_score: float = Field(default=0, ge=0, le=100)
    extraction_confidence: float = Field(default=0, ge=0, le=1)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    scraped_at: datetime

    @model_validator(mode="after")
    def validate_dates_and_score(self) -> OpportunityRecord:
        aware_dates = (
            self.registration_deadline,
            self.event_start,
            self.event_end,
            self.scraped_at,
        )
        if any(value is not None and value.tzinfo is None for value in aware_dates):
            raise ValueError("all datetimes must include timezone information")
        if self.event_start and self.event_end and self.event_end < self.event_start:
            raise ValueError("event_end must be on or after event_start")
        if abs(self.priority_score - self.score_breakdown.total) > 1e-6:
            raise ValueError("priority_score must equal score_breakdown total")
        return self


# Backward-compatible name for early code that only handled hackathons. New code
# should use OpportunityRecord and set opportunity_type explicitly.
HackathonRecord: TypeAlias = OpportunityRecord
