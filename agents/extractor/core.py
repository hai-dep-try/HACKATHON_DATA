"""Deterministic extraction from RawDocument to OpportunityRecord."""

import json
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

    # 3. HTML Minimal Fallback
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
        content_hash=doc.content_hash,
        scraped_at=doc.fetched_at,
    )
