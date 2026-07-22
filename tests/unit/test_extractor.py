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


def test_article_classifies_fpt_futuretech_scenario():
    source = SourceDefinition(
        id="fpt-source",
        name="FPT Source",
        kind=SourceKind.HTML,
        base_url=HttpUrl("https://fpt.example.com"),
        discovery_urls=[HttpUrl("https://fpt.example.com/news")],
        allowed_domains=["fpt.example.com"],
        opportunity_types={OpportunityType.TALENT_PROGRAM},
        enabled=True,
    )
    html = """
    <html>
      <head>
        <title>FPT FutureTech Talents 2026</title>
        <meta property="article:published_time" content="2026-03-26T17:00:00+07:00">
      </head>
      <body>
        <h1>FPT FutureTech Talents</h1>
        <p>Đây là chương trình tài năng.</p>
        <p>Thời gian nhận hồ sơ là từ ngày 26/3 đến ngày 15/8.</p>
        <p>Đối tượng: Sinh viên năm 3-5 các trường đại học công nghệ.</p>
        <p>Quyền lợi: Nhận học bổng trị giá 50 triệu VNĐ.</p>
        <p>Chương trình tập trung vào các công nghệ AI, Cloud,
        Cyber Security và Điện toán lượng tử (Quantum).</p>
      </body>
    </html>
    """
    doc = RawDocument.from_text(
        source_id="fpt-source",
        url="https://fpt.example.com/talent",
        fetched_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        status_code=200,
        content_type="text/html",
        text=html,
    )

    record = extract_opportunity(doc, source)

    assert record.title == "FPT FutureTech Talents 2026"
    assert record.opportunity_type is OpportunityType.TALENT_PROGRAM
    # deadline parsed to 2026-08-15 23:59:59
    assert record.registration_deadline == datetime(2026, 8, 15, 23, 59, 59, tzinfo=UTC)
    assert set(record.technologies) == {"AI", "Cloud", "Cyber Security", "Quantum"}
    assert record.eligibility_text == "Sinh viên năm 3-5 các trường đại học công nghệ"
    assert record.compensation_text == "Nhận học bổng trị giá 50 triệu VNĐ"
    assert record.paid is None


def test_deadline_without_year_or_publication_metadata_stays_unknown(mock_source):
    doc = RawDocument.from_text(
        source_id="test_source",
        url="https://example.com/internship",
        fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
        status_code=200,
        content_type="text/html",
        text="<html><title>Internship</title><p>Hạn đăng ký: 15/08.</p></html>",
    )

    record = extract_opportunity(doc, mock_source)

    assert record.registration_deadline is None


def test_itemprop_publication_metadata_supplies_deadline_year(mock_source):
    doc = RawDocument.from_text(
        source_id="test_source",
        url="https://example.com/internship",
        fetched_at=datetime(2027, 1, 1, tzinfo=UTC),
        status_code=200,
        content_type="text/html",
        text=(
            '<html><head><meta itemprop="datePublished" '
            'content="2026-03-26T17:00:00+07:00"><title>Internship</title></head>'
            "<body><p>Thời gian nhận hồ sơ từ ngày 26/3 đến ngày 10/4.</p></body></html>"
        ),
    )

    record = extract_opportunity(doc, mock_source)

    assert record.registration_deadline == datetime(2026, 4, 10, 23, 59, 59, tzinfo=UTC)
