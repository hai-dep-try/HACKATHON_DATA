"""Run one configured source through HTTP fetch and deterministic extraction."""

from __future__ import annotations

import argparse
import asyncio
import sys

import httpx
from pydantic import HttpUrl

from agents.extractor.core import extract_opportunity
from agents.scraper.http_scraper import HttpScraper
from agents.scraper.source_registry import load_source_registry


async def run(registry_path: str, source_id: str, url_override: str | None) -> None:
    registry = load_source_registry(registry_path)
    source = next((item for item in registry.sources if item.id == source_id), None)
    if source is None:
        raise ValueError(f"unknown source id: {source_id}")

    url = HttpUrl(url_override) if url_override else source.discovery_urls[0]
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        document = await HttpScraper(source, client).fetch_page(url)

    record = extract_opportunity(document, source)
    print(record.model_dump_json(indent=2))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="config/sources.json")
    parser.add_argument("--source", default="vnexpress-education")
    parser.add_argument("--url")
    arguments = parser.parse_args()
    asyncio.run(run(arguments.registry, arguments.source, arguments.url))


if __name__ == "__main__":
    main()
