from __future__ import annotations

import httpx
import pytest
from pydantic import HttpUrl

from agents.common.models import OpportunityType
from agents.scraper.http_scraper import CrawlPolicyError, HttpScraper, SourceDisabledError
from agents.scraper.source_registry import SourceDefinition, SourceKind


def make_source(*, enabled: bool = True) -> SourceDefinition:
    return SourceDefinition(
        id="example-source",
        name="Example Source",
        kind=SourceKind.HTML,
        base_url=HttpUrl("https://example.com"),
        discovery_urls=[HttpUrl("https://example.com/opportunities")],
        allowed_domains=["example.com"],
        opportunity_types={OpportunityType.INTERNSHIP},
        enabled=enabled,
        requests_per_minute=60,
    )


async def request_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text="User-agent: *\nAllow: /", request=request)
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8"},
        text="<html><title>Internship</title></html>",
        request=request,
    )


@pytest.mark.asyncio
async def test_fetches_allowed_html_as_raw_document() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(request_handler)) as client:
        scraper = HttpScraper(make_source(), client)
        document = await scraper.fetch_page(HttpUrl("https://example.com/opportunities"))

    assert document.source_id == "example-source"
    assert document.status_code == 200
    assert document.text == "<html><title>Internship</title></html>"


@pytest.mark.asyncio
async def test_refuses_disabled_source_without_request() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(request_handler)) as client:
        scraper = HttpScraper(make_source(enabled=False), client)
        with pytest.raises(SourceDisabledError):
            await scraper.fetch_page(HttpUrl("https://example.com/opportunities"))


@pytest.mark.asyncio
async def test_refuses_url_outside_allowlist() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(request_handler)) as client:
        scraper = HttpScraper(make_source(), client)
        with pytest.raises(CrawlPolicyError, match="allowlist"):
            await scraper.fetch_page(HttpUrl("https://untrusted.example.org/jobs"))


@pytest.mark.asyncio
async def test_refuses_robots_disallow() -> None:
    async def disallow_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /", request=request)
        raise AssertionError("page request should not be made")

    async with httpx.AsyncClient(transport=httpx.MockTransport(disallow_handler)) as client:
        scraper = HttpScraper(make_source(), client)
        with pytest.raises(CrawlPolicyError, match="robots.txt disallows"):
            await scraper.fetch_page(HttpUrl("https://example.com/opportunities"))
