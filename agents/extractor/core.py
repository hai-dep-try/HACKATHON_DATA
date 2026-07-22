"""Deterministic extraction from RawDocument to OpportunityRecord."""

import json
import re
from datetime import UTC, datetime
from typing import Any

from bs4 import BeautifulSoup

from agents.common.models import (
    ExperienceLevel,
    LocationType,
    OpportunityRecord,
    OpportunityType,
    RawDocument,
)
from agents.scraper.source_registry import SourceDefinition


def _extract_from_json_ld(soup: BeautifulSoup) -> dict[str, Any] | None:
    """Find and parse the first relevant JobPosting or Event from JSON-LD."""
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            # Handle both single objects and arrays of objects
            items = data if isinstance(data, list) else [data]

            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("@type")
                if item_type in ("JobPosting", "Event"):
                    return item
        except json.JSONDecodeError:
            continue
    return None


def _classify_from_evidence(text: str, source: SourceDefinition) -> OpportunityType:
    """Classify only when page text contains evidence allowed by source config."""

    normalized = " ".join(text.lower().split())
    rules = (
        (OpportunityType.TALENT_PROGRAM, ("talent", "tài năng", "ươm mầm")),
        (OpportunityType.TRAINEE_PROGRAM, ("trainee", "quản trị viên tập sự")),
        (OpportunityType.INTERNSHIP, ("internship", "intern ", "thực tập")),
        (OpportunityType.HACKATHON, ("hackathon",)),
        (OpportunityType.FELLOWSHIP, ("fellowship",)),
        (OpportunityType.SCHOLARSHIP, ("scholarship", "học bổng")),
        (OpportunityType.BOOTCAMP, ("bootcamp",)),
    )
    for opportunity_type, keywords in rules:
        if opportunity_type in source.opportunity_types and any(
            keyword in normalized for keyword in keywords
        ):
            return opportunity_type
    return OpportunityType.OTHER


def _extract_application_url(soup: BeautifulSoup) -> str | None:
    """Find an explicit application link based on nearby call-to-action text."""

    action_terms = ("đăng ký", "ứng tuyển", "nộp hồ sơ", "apply", "register")
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href")
        if not isinstance(href, str) or not href.startswith(("https://", "http://")):
            continue
        context_node = anchor.parent if anchor.parent is not None else anchor
        context = context_node.get_text(" ", strip=True).lower()
        if any(term in context for term in action_terms):
            return href
    return None


def _extract_published_at(soup: BeautifulSoup) -> datetime | None:
    """Read article publication time from explicit page metadata."""

    meta = soup.find("meta", property="article:published_time")
    if meta is None:
        meta = soup.find("meta", attrs={"itemprop": "datePublished"})
    value = meta.get("content") if meta else None
    if not isinstance(value, str):
        return None
    try:
        published_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return published_at if published_at.tzinfo is not None else published_at.replace(tzinfo=UTC)


def _extract_deadline(text: str, published_at: datetime | None) -> datetime | None:
    """Parse an explicit deadline, using publication year only when needed."""

    match = re.search(
        r"(?i)(?:hạn đăng ký|đăng ký đến|deadline|"
        r"nhận hồ sơ[^.]{0,100}?đến(?: ngày)?)[:\s]*(\d{1,2})[-/](\d{1,2})"
        r"(?:[-/](\d{4}))?",
        text,
    )
    if match:
        explicit_year = int(match.group(3)) if match.group(3) else None
        year = explicit_year or (published_at.year if published_at else None)
        if year is None:
            return None
        try:
            return datetime(year, int(match.group(2)), int(match.group(1)), 23, 59, 59, tzinfo=UTC)
        except ValueError:
            return None
    return None


def _extract_technologies(text: str) -> list[str]:
    """Extract standard technologies mentioned in text."""
    techs = []
    # Using word boundaries to avoid partial matches, though for some we just check presence
    if re.search(r"\bAI\b|\bTrí tuệ nhân tạo\b", text, re.IGNORECASE):
        techs.append("AI")
    if re.search(r"\bCloud\b|\bĐiện toán đám mây\b", text, re.IGNORECASE):
        techs.append("Cloud")
    if re.search(r"\bCyber\s*Security\b|\bAn toàn thông tin\b|\bBảo mật\b", text, re.IGNORECASE):
        techs.append("Cyber Security")
    if re.search(r"\bQuantum\b|\bLượng tử\b", text, re.IGNORECASE):
        techs.append("Quantum")
    return techs


def _extract_eligibility(text: str) -> str | None:
    """Extract short eligibility sentence."""
    match = re.search(
        r"(?i)(?:đối tượng|điều kiện|yêu cầu)[^\.:\n]*[:]*\s*([^\.\n]*(?:sinh viên)[^\.\n]*)\.",
        text,
    )  # noqa: E501
    if match:
        return match.group(1).strip()
    return None


def _extract_compensation(text: str) -> tuple[str | None, bool | None]:
    """Extract compensation text and paid boolean."""
    match = re.search(
        r"(?i)(?:quyền lợi|học bổng|trợ cấp)[^\.:\n]*[:]*\s*"
        r"([^\.\n]*(?:triệu|vnd|usd|học bổng|trợ cấp|lương)[^\.\n]*)\.",
        text,
    )
    if match:
        comp_text = match.group(1).strip()
        if re.search(r"(?i)không lương|unpaid", comp_text):
            is_paid: bool | None = False
        elif re.search(r"(?i)trợ cấp|lương|salary|stipend", comp_text):
            is_paid = True
        else:
            is_paid = None
        return comp_text, is_paid
    return None, None


def extract_opportunity(doc: RawDocument, source: SourceDefinition) -> OpportunityRecord:
    """Extract structured data from a RawDocument deterministically."""
    if doc.source_id != source.id:
        raise ValueError(f"Mismatch source ID: doc has {doc.source_id!r}, source has {source.id!r}")

    soup = BeautifulSoup(doc.text, "html.parser")

    title = None
    description = None
    opportunity_type = OpportunityType.OTHER

    # 1. JSON-LD
    json_ld = _extract_from_json_ld(soup)
    if json_ld:
        item_type = json_ld.get("@type")
        if item_type == "JobPosting":
            title = json_ld.get("title")
            description = json_ld.get("description")
            opportunity_type = OpportunityType.INTERNSHIP
        elif item_type == "Event":
            title = json_ld.get("name")
            description = json_ld.get("description")
            opportunity_type = OpportunityType.HACKATHON

    # 2. OpenGraph Fallback
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and isinstance(og_title, dict) is False:
            title = og_title.get("content")

    if not description:
        og_desc = soup.find("meta", property="og:description")
        if og_desc and isinstance(og_desc, dict) is False:
            description = og_desc.get("content")

    page_text = soup.get_text(" ", strip=True)
    if opportunity_type is OpportunityType.OTHER:
        opportunity_type = _classify_from_evidence(page_text, source)

    application_url = _extract_application_url(soup)
    mentions_students = "sinh viên" in page_text.lower() or "student" in page_text.lower()

    # 3. New extractions
    deadline = _extract_deadline(page_text, _extract_published_at(soup))
    technologies = _extract_technologies(page_text)
    eligibility_text = _extract_eligibility(page_text)
    compensation_text, is_paid = _extract_compensation(page_text)

    # 4. HTML Minimal Fallback
    if not title:
        if soup.title and soup.title.string:
            title = soup.title.string
        else:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

    # Clean up fields
    final_title = str(title).strip() if title else "Unknown"
    final_description = str(description).strip() if description else None

    # Do not infer missing information
    return OpportunityRecord(
        source_url=doc.url,
        source_name=source.name,
        title=final_title[:500],
        description=final_description,
        opportunity_type=opportunity_type,
        application_url=application_url,
        location_type=LocationType.UNKNOWN,
        target_audiences=["university_student"] if mentions_students else [],
        experience_level=(
            ExperienceLevel.STUDENT if mentions_students else ExperienceLevel.NOT_SPECIFIED
        ),
        registration_deadline=deadline,
        technologies=technologies,
        eligibility_text=eligibility_text,
        compensation_text=compensation_text,
        paid=is_paid,
        content_hash=doc.content_hash,
        scraped_at=doc.fetched_at,
    )
