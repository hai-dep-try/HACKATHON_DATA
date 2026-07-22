"""Run enabled source discovery pages through the local MVP pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import httpx

from agents.pipeline.runner import PipelineRunner
from agents.scraper.raw_store import RawSnapshotStore
from agents.scraper.source_registry import SourceDefinition, load_source_registry


def select_sources(
    sources: list[SourceDefinition], source_id: str | None
) -> tuple[SourceDefinition, ...]:
    enabled = tuple(source for source in sources if source.enabled)
    if source_id is None:
        return enabled
    selected = tuple(source for source in enabled if source.id == source_id)
    if not selected:
        raise ValueError(f"enabled source not found: {source_id}")
    return selected


async def run(registry_path: str, source_id: str | None, raw_dir: str) -> None:
    registry = load_source_registry(registry_path)
    sources = select_sources(registry.sources, source_id)
    runner = PipelineRunner(RawSnapshotStore(raw_dir))

    output: list[dict[str, object]] = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        for source in sources:
            for item in await runner.run_source(source, client):
                output.append(
                    {
                        "source_id": item.source_id,
                        "snapshot_path": str(item.snapshot_path),
                        "snapshot_created": item.snapshot_created,
                        "opportunity": item.opportunity.model_dump(mode="json"),
                    }
                )
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="config/sources.json")
    parser.add_argument("--source")
    parser.add_argument("--raw-dir", default="data/raw")
    arguments = parser.parse_args()
    asyncio.run(run(arguments.registry, arguments.source, arguments.raw_dir))


if __name__ == "__main__":
    main()
