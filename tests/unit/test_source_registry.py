from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.common.models import OpportunityType, RawDocument
from agents.scraper.source_registry import SourceRegistry, load_source_registry


def test_loads_example_registry() -> None:
    registry = load_source_registry(Path("config/sources.example.json"))

    assert len(registry.sources) == 2
    assert registry.enabled_sources() == ()
    assert OpportunityType.INTERNSHIP in registry.sources[1].opportunity_types


def test_rejects_discovery_url_outside_allowlist() -> None:
    with pytest.raises(ValidationError, match="outside allowed_domains"):
        SourceRegistry.model_validate(
            {
                "sources": [
                    {
                        "id": "unsafe-source",
                        "name": "Unsafe",
                        "kind": "html",
                        "base_url": "https://safe.example.com",
                        "discovery_urls": ["https://untrusted.example.net/jobs"],
                        "allowed_domains": ["safe.example.com"],
                        "opportunity_types": ["internship"],
                    }
                ]
            }
        )


def test_rejects_duplicate_source_ids() -> None:
    source = {
        "id": "same-source",
        "name": "Same",
        "kind": "rss",
        "base_url": "https://example.com",
        "discovery_urls": ["https://example.com/feed"],
        "allowed_domains": ["example.com"],
        "opportunity_types": ["internship"],
    }
    with pytest.raises(ValidationError, match="source ids must be unique"):
        SourceRegistry.model_validate({"sources": [source, source]})


def test_raw_document_derives_and_validates_content_hash() -> None:
    document = RawDocument.from_text(
        source_id="example-source",
        url="https://example.com/jobs/1",
        fetched_at=datetime(2026, 7, 22, tzinfo=UTC),
        status_code=200,
        content_type="text/html; charset=utf-8",
        text="<html>Internship</html>",
    )

    assert document.content_hash == sha256(document.text.encode()).hexdigest()


def test_raw_document_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        RawDocument.from_text(
            source_id="example-source",
            url="https://example.com/jobs/1",
            fetched_at=datetime(2026, 7, 22),
            status_code=200,
            content_type="text/html",
            text="Internship",
        )
