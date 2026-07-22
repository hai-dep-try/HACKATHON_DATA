from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from agents.common.models import (
    ExperienceLevel,
    HackathonRecord,
    LocationType,
    OpportunityRecord,
    OpportunityType,
    ScoreBreakdown,
)


def make_record(**overrides: object) -> HackathonRecord:
    values: dict[str, object] = {
        "source_url": "https://example.com/events/demo",
        "source_name": "Example",
        "title": "Demo Hackathon",
        "location_type": LocationType.ONLINE,
        "score_breakdown": ScoreBreakdown(location=30, timing=25),
        "priority_score": 55,
        "extraction_confidence": 0.9,
        "content_hash": "a" * 64,
        "scraped_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return HackathonRecord.model_validate(values)


def test_valid_record_exposes_explainable_score() -> None:
    record = make_record()

    assert record.score_breakdown.total == 55
    assert record.priority_score == 55


def test_rejects_priority_score_that_does_not_match_breakdown() -> None:
    with pytest.raises(ValidationError, match="priority_score"):
        make_record(priority_score=80)


def test_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        make_record(scraped_at=datetime(2026, 1, 1))


def test_supports_no_experience_internship() -> None:
    record = OpportunityRecord.model_validate(
        {
            "source_url": "https://example.com/careers/internship",
            "source_name": "Example Careers",
            "title": "Software Engineering Internship",
            "opportunity_type": OpportunityType.INTERNSHIP,
            "experience_level": ExperienceLevel.NO_EXPERIENCE,
            "target_audiences": ["university_student"],
            "paid": True,
            "content_hash": "b" * 64,
            "scraped_at": datetime(2026, 1, 1, tzinfo=UTC),
        }
    )

    assert record.opportunity_type is OpportunityType.INTERNSHIP
    assert record.experience_level is ExperienceLevel.NO_EXPERIENCE


def test_hackathon_record_name_remains_backward_compatible() -> None:
    assert HackathonRecord is OpportunityRecord
