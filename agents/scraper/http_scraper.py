"""HTTP scraper that enforces source-level crawl policy."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx
from pydantic import HttpUrl

from agents.common.models import RawDocument
from agents.scraper.source_registry import SourceDefinition


class ScraperError(Exception):
    """Base error for a policy-enforcing scraper."""


class SourceDisabledError(ScraperError):
    """Raised when a caller tries to crawl a source that is not enabled."""


class CrawlPolicyError(ScraperError):
    """Raised when an URL or robots policy rejects a crawl."""


class FetchError(ScraperError):
    """Raised when a permitted request cannot yield a usable document."""


class HttpScraper:
    """Fetch HTML discovery pages only after domain and robots checks pass."""

    def __init__(
        self,
        source: SourceDefinition,
        client: httpx.AsyncClient,
        *,
        user_agent: str = "hackathon_data/0.1",
    ) -> None:
        self._source = source
        self._client = client
        self._user_agent = user_agent
        self._robots: dict[str, RobotFileParser] = {}
        self._last_fetch_started_at: float | None = None

    async def fetch_discovery_pages(self) -> tuple[RawDocument, ...]:
        """Fetch configured discovery pages sequentially within the RPM policy."""

        documents = []
        for url in self._source.discovery_urls:
            documents.append(await self.fetch_page(url))
        return tuple(documents)

    async def fetch_page(self, url: HttpUrl) -> RawDocument:
        """Fetch one allowed HTML page and convert it to an immutable RawDocument."""

        self._ensure_source_is_enabled()
        if not self._source.allows_url(url):
            raise CrawlPolicyError(f"URL {url} is outside source allowlist")

        await self._ensure_robots_permit(url)
        await self._wait_for_rate_limit()
        response = await self._request(url)
        self._last_fetch_started_at = time.monotonic()

        if response.status_code < 200 or response.status_code >= 300:
            raise FetchError(f"unexpected HTTP status {response.status_code} for {url}")

        content_type = response.headers.get("content-type", "")
        if not self._is_html(content_type):
            raise FetchError(f"expected HTML content, got {content_type or 'missing content-type'}")

        return RawDocument.from_text(
            source_id=self._source.id,
            url=str(response.url),
            fetched_at=datetime.now(UTC),
            status_code=response.status_code,
            content_type=content_type,
            text=response.text,
        )

    def _ensure_source_is_enabled(self) -> None:
        if not self._source.enabled:
            raise SourceDisabledError(f"source {self._source.id!r} is disabled")

    async def _ensure_robots_permit(self, url: HttpUrl) -> None:
        robots_url = self._robots_url_for(url)
        parser = self._robots.get(robots_url)
        if parser is None:
            response = await self._request(robots_url)
            parser = RobotFileParser()
            parser.set_url(robots_url)
            if response.status_code == 404:
                parser.parse(["User-agent: *", "Allow: /"])
            elif 200 <= response.status_code < 300:
                parser.parse(response.text.splitlines())
            else:
                raise CrawlPolicyError(
                    f"cannot verify robots.txt for {url}: HTTP {response.status_code}"
                )
            self._robots[robots_url] = parser

        if not parser.can_fetch(self._user_agent, str(url)):
            raise CrawlPolicyError(f"robots.txt disallows {url}")

    async def _wait_for_rate_limit(self) -> None:
        if self._last_fetch_started_at is None:
            return

        interval_seconds = 60 / self._source.requests_per_minute
        elapsed = time.monotonic() - self._last_fetch_started_at
        if elapsed < interval_seconds:
            await asyncio.sleep(interval_seconds - elapsed)

    async def _request(self, url: HttpUrl | str) -> httpx.Response:
        try:
            return await self._client.get(str(url), headers={"User-Agent": self._user_agent})
        except httpx.HTTPError as error:
            raise FetchError(f"request failed for {url}: {error}") from error

    @staticmethod
    def _robots_url_for(url: HttpUrl) -> str:
        parts = urlsplit(str(url))
        return urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))

    @staticmethod
    def _is_html(content_type: str) -> bool:
        media_type = content_type.partition(";")[0].lower().strip()
        return media_type in {"text/html", "application/xhtml+xml"}
