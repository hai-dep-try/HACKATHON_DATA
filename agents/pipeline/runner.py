"""Orchestrate fetch, raw persistence, and deterministic extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from agents.common.models import OpportunityRecord
from agents.extractor.core import extract_opportunity
from agents.scraper.http_scraper import HttpScraper
from agents.scraper.raw_store import RawSnapshotStore
from agents.scraper.source_registry import SourceDefinition


@dataclass(frozen=True, slots=True)
class PipelineItem:
    """One processed discovery page and its persisted raw snapshot."""

    source_id: str
    snapshot_path: Path
    snapshot_created: bool
    opportunity: OpportunityRecord


class PipelineRunner:
    """Run enabled source discovery pages through the MVP pipeline."""

    def __init__(self, raw_store: RawSnapshotStore) -> None:
        self._raw_store = raw_store

    async def run_source(
        self,
        source: SourceDefinition,
        client: httpx.AsyncClient,
    ) -> tuple[PipelineItem, ...]:
        """Fetch, persist, and extract every configured discovery page."""

        documents = await HttpScraper(source, client).fetch_discovery_pages()
        items = []
        for document in documents:
            snapshot = self._raw_store.save(document)
            opportunity = extract_opportunity(document, source)
            items.append(
                PipelineItem(
                    source_id=source.id,
                    snapshot_path=snapshot.path,
                    snapshot_created=snapshot.created,
                    opportunity=opportunity,
                )
            )
        return tuple(items)
