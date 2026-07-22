"""Validated configuration for public opportunity sources."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from agents.common.models import OpportunityType


class SourceKind(StrEnum):
    """Supported source transport/discovery styles."""

    HTML = "html"
    RSS = "rss"
    API = "api"


class SourceDefinition(BaseModel):
    """Crawl policy and discovery entry points for one public source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    name: str = Field(min_length=1, max_length=100)
    kind: SourceKind
    base_url: HttpUrl
    discovery_urls: list[HttpUrl] = Field(min_length=1)
    allowed_domains: list[str] = Field(min_length=1)
    opportunity_types: set[OpportunityType] = Field(min_length=1)
    enabled: bool = False
    requests_per_minute: int = Field(default=10, ge=1, le=60)
    max_concurrency: int = Field(default=1, ge=1, le=5)
    respect_robots_txt: bool = True

    @model_validator(mode="after")
    def validate_policy_and_urls(self) -> SourceDefinition:
        domains = {domain.lower().strip(".") for domain in self.allowed_domains}
        if len(domains) != len(self.allowed_domains):
            raise ValueError("allowed_domains must be unique after normalization")
        if not self.respect_robots_txt:
            raise ValueError("respect_robots_txt must remain enabled")

        for url in (self.base_url, *self.discovery_urls):
            host = (url.host or "").lower().strip(".")
            if not any(host == domain or host.endswith(f".{domain}") for domain in domains):
                raise ValueError(f"URL host {host!r} is outside allowed_domains")
        return self

    def allows_url(self, url: HttpUrl) -> bool:
        """Return whether a URL belongs to this source's domain allowlist."""

        host = (url.host or "").lower().strip(".")
        return any(
            host == domain.lower().strip(".") or host.endswith(f".{domain.lower().strip('.')}")
            for domain in self.allowed_domains
        )


class SourceRegistry(BaseModel):
    """Versioned collection of source definitions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    sources: list[SourceDefinition]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> SourceRegistry:
        ids = [source.id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source ids must be unique")
        return self

    def enabled_sources(self) -> tuple[SourceDefinition, ...]:
        """Return enabled sources without exposing a mutable registry list."""

        return tuple(source for source in self.sources if source.enabled)


def load_source_registry(path: str | Path) -> SourceRegistry:
    """Load and validate a UTF-8 JSON source registry."""

    registry_path = Path(path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return SourceRegistry.model_validate(data)
