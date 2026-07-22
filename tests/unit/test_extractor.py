from datetime import UTC, datetime

import pytest
from pydantic import HttpUrl

from agents.common.models import ExperienceLevel, LocationType, OpportunityType, RawDocument
from agents.extractor.core import extract_opportunity
from agents.scraper.source_registry import SourceDefinition, SourceKind


@pytest.fixture
def mock_source():
    return SourceDefinition(
        id="test_source",
        name="Test Source",
        kind=SourceKind.HTML,
        base_url=HttpUrl("https://example.com"),
        discovery_urls=[HttpUrl("https://example.com/jobs")],
        allowed_domains=["example.com"],
        opportunity_types={OpportunityType.INTERNSHIP},
        enabled=True,
    )


def test_extract_json_ld_job_posting(mock_source):
    html = """
    <html>
        <head>
            <script type="application/ld+json">
                {
                    "@context": "https://schema.org/",
                    "@type": "JobPosting",
                    "title": "Software Engineering Intern",
                    "description": "An awesome internship."
                }
            </script>
        </head>
        <body></body>
    </html>
    """
    doc = RawDocument.from_text(
        source_id="test_source",
        url="https://example.com/internship",
        fetched_at=datetime.now(UTC),
        status_code=200,
        content_type="text/html",
        text=html,
    )

    record = extract_opportunity(doc, mock_source)
    assert record.title == "Software Engineering Intern"
    assert record.description == "An awesome internship."
    assert record.opportunity_type == OpportunityType.INTERNSHIP
    assert record.content_hash == doc.content_hash
    assert record.scraped_at == doc.fetched_at


def test_extract_json_ld_event(mock_source):
    html = """
    <html>
        <head>
            <script type="application/ld+json">
                {
                    "@context": "https://schema.org/",
                    "@type": "Event",
                    "name": "Global Hackathon 2026",
                    "description": "Hack the planet."
                }
            </script>
        </head>
        <body></body>
    </html>
    """
    doc = RawDocument.from_text(
        source_id="test_source",
        url="https://example.com/hackathon",
        fetched_at=datetime.now(UTC),
        status_code=200,
        content_type="text/html",
        text=html,
    )

    record = extract_opportunity(doc, mock_source)
    assert record.title == "Global Hackathon 2026"
    assert record.description == "Hack the planet."
    assert record.opportunity_type == OpportunityType.HACKATHON


def test_extract_fallback_title(mock_source):
    html = """
    <html>
        <head>
            <title>Fallback Title</title>
        </head>
        <body></body>
    </html>
    """
    doc = RawDocument.from_text(
        source_id="test_source",
        url="https://example.com/unknown",
        fetched_at=datetime.now(UTC),
        status_code=200,
        content_type="text/html",
        text=html,
    )

    record = extract_opportunity(doc, mock_source)
    assert record.title == "Fallback Title"
    assert record.opportunity_type == OpportunityType.OTHER
    assert record.location_type == LocationType.UNKNOWN
    assert record.experience_level == ExperienceLevel.NOT_SPECIFIED


def test_extract_invalid_json_ld_survives(mock_source):
    html = """
    <html>
        <head>
            <script type="application/ld+json">
                { invalid json
            </script>
            <meta property="og:title" content="OG Title">
        </head>
        <body></body>
    </html>
    """
    doc = RawDocument.from_text(
        source_id="test_source",
        url="https://example.com/invalid-json",
        fetched_at=datetime.now(UTC),
        status_code=200,
        content_type="text/html",
        text=html,
    )

    record = extract_opportunity(doc, mock_source)
    assert record.title == "OG Title"


def test_source_id_mismatch_raises_error(mock_source):
    doc = RawDocument.from_text(
        source_id="different_source",
        url="https://example.com/job",
        fetched_at=datetime.now(UTC),
        status_code=200,
        content_type="text/html",
        text="<html></html>",
    )

    with pytest.raises(ValueError, match="Mismatch source ID"):
        extract_opportunity(doc, mock_source)


def test_article_classifies_talent_program_from_explicit_evidence():
    source = SourceDefinition(
        id="news-source",
        name="News Source",
        kind=SourceKind.HTML,
        base_url=HttpUrl("https://news.example.com"),
        discovery_urls=[HttpUrl("https://news.example.com/education")],
        allowed_domains=["news.example.com"],
        opportunity_types={OpportunityType.TALENT_PROGRAM, OpportunityType.INTERNSHIP},
        enabled=True,
    )
    html = """
    <html>
      <head>
        <meta property="og:title" content="Technology Talent Program">
        <meta property="og:description" content="A program for technology students.">
      </head>
      <body>
        <h1>Technology Talent Program</h1>
        <p>Chương trình tài năng dành cho sinh viên công nghệ.</p>
        <p>Ứng viên đăng ký tại <a href="https://apply.example.org/form">đây</a>.</p>
      </body>
    </html>
    """
    doc = RawDocument.from_text(
        source_id="news-source",
        url="https://news.example.com/talent-program",
        fetched_at=datetime.now(UTC),
        status_code=200,
        content_type="text/html",
        text=html,
    )

    record = extract_opportunity(doc, source)

    assert record.opportunity_type is OpportunityType.TALENT_PROGRAM
    assert record.experience_level is ExperienceLevel.STUDENT
    assert record.target_audiences == ["university_student"]
    assert str(record.application_url) == "https://apply.example.org/form"
