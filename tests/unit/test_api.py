import typing
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from agents.common.models import ExperienceLevel, LocationType, OpportunityRecord, OpportunityType
from backend.main import app, get_repository
from backend.repository import InMemoryOpportunityRepository

client = TestClient(app)

# A sample record for tests
dummy_record = OpportunityRecord(
    source_url="https://example.com",
    source_name="Example Source",
    title="Example Opportunity",
    opportunity_type=OpportunityType.HACKATHON,
    location_type=LocationType.HANOI,
    experience_level=ExperienceLevel.STUDENT,
    content_hash="a" * 64,
    scraped_at=datetime.now(UTC),
)


@pytest.fixture
def repo_override() -> typing.Generator[InMemoryOpportunityRepository, None, None]:
    repo = InMemoryOpportunityRepository()
    app.dependency_overrides[get_repository] = lambda: repo
    yield repo
    app.dependency_overrides.clear()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_opportunities_empty(repo_override: InMemoryOpportunityRepository) -> None:
    response = client.get("/opportunities")
    assert response.status_code == 200
    assert response.json() == []


def test_list_opportunities_populated(repo_override: InMemoryOpportunityRepository) -> None:
    repo_override.add_opportunity(dummy_record)
    response = client.get("/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Example Opportunity"


def test_list_opportunities_filtered_match(repo_override: InMemoryOpportunityRepository) -> None:
    repo_override.add_opportunity(dummy_record)
    response = client.get("/opportunities?opportunity_type=hackathon&location_type=hanoi")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_opportunities_filtered_no_match(repo_override: InMemoryOpportunityRepository) -> None:
    repo_override.add_opportunity(dummy_record)
    response = client.get("/opportunities?opportunity_type=internship")
    assert response.status_code == 200
    assert response.json() == []


def test_get_opportunity_success(repo_override: InMemoryOpportunityRepository) -> None:
    repo_override.add_opportunity(dummy_record)
    response = client.get(f"/opportunities/{dummy_record.content_hash}")
    assert response.status_code == 200
    assert response.json()["title"] == "Example Opportunity"


def test_get_opportunity_not_found(repo_override: InMemoryOpportunityRepository) -> None:
    response = client.get("/opportunities/" + "b" * 64)
    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found"
