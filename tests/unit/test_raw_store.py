from datetime import UTC, datetime

import pytest

from agents.common.models import RawDocument
from agents.scraper.raw_store import RawSnapshotStore


def make_document(text: str = "Opportunity") -> RawDocument:
    return RawDocument.from_text(
        source_id="example-source",
        url="https://example.com/opportunity",
        fetched_at=datetime(2026, 7, 22, tzinfo=UTC),
        status_code=200,
        content_type="text/html",
        text=text,
    )


def test_save_is_idempotent_and_loads_validated_document(tmp_path) -> None:
    store = RawSnapshotStore(tmp_path)
    document = make_document()

    first = store.save(document)
    second = store.save(document)
    loaded = store.load(document.source_id, document.content_hash)

    assert first.created is True
    assert second.created is False
    assert first.path == second.path
    assert loaded == document


def test_different_content_creates_different_snapshot(tmp_path) -> None:
    store = RawSnapshotStore(tmp_path)

    first = store.save(make_document("First"))
    second = store.save(make_document("Second"))

    assert first.created is True
    assert second.created is True
    assert first.path != second.path


def test_load_rejects_path_traversal(tmp_path) -> None:
    store = RawSnapshotStore(tmp_path)

    with pytest.raises(ValueError, match="invalid source_id"):
        store.load("../outside", "a" * 64)


def test_load_detects_tampered_identity(tmp_path) -> None:
    store = RawSnapshotStore(tmp_path)
    original = make_document("Original")
    other = make_document("Other")
    result = store.save(original)
    result.path.write_text(other.model_dump_json(), encoding="utf-8")

    with pytest.raises(ValueError, match="identity"):
        store.load(original.source_id, original.content_hash)
