from __future__ import annotations

import httpx
import pytest
from pydantic import HttpUrl

from agents.common.models import OpportunityType
from agents.pipeline.runner import PipelineRunner
from agents.scraper.raw_store import RawSnapshotStore
from agents.scraper.source_registry import SourceDefinition, SourceKind


def make_source() -> SourceDefinition:
    return SourceDefinition(
        id="pipeline-source",
        name="Pipeline Source",
        kind=SourceKind.HTML,
        base_url=HttpUrl("https://example.com"),
        discovery_urls=[HttpUrl("https://example.com/opportunity")],
        allowed_domains=["example.com"],
        opportunity_types={OpportunityType.TALENT_PROGRAM},
        enabled=True,
        requests_per_minute=60,
    )


async def request_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text="User-agent: *\nAllow: /", request=request)
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8"},
        text=(
            "<html><head><meta property='og:title' content='Student Talent Program'></head>"
            "<body><p>Talent program dành cho sinh viên.</p></body></html>"
        ),
        request=request,
    )


@pytest.mark.asyncio
async def test_pipeline_fetches_persists_and_extracts(tmp_path) -> None:
    runner = PipelineRunner(RawSnapshotStore(tmp_path))
    async with httpx.AsyncClient(transport=httpx.MockTransport(request_handler)) as client:
        items = await runner.run_source(make_source(), client)

    assert len(items) == 1
    item = items[0]
    assert item.snapshot_created is True
    assert item.snapshot_path.exists()
    assert item.opportunity.title == "Student Talent Program"
    assert item.opportunity.opportunity_type is OpportunityType.TALENT_PROGRAM


@pytest.mark.asyncio
async def test_pipeline_second_run_reuses_snapshot(tmp_path) -> None:
    runner = PipelineRunner(RawSnapshotStore(tmp_path))
    async with httpx.AsyncClient(transport=httpx.MockTransport(request_handler)) as client:
        first = await runner.run_source(make_source(), client)
        second = await runner.run_source(make_source(), client)

    assert first[0].snapshot_path == second[0].snapshot_path
    assert first[0].snapshot_created is True
    assert second[0].snapshot_created is False
