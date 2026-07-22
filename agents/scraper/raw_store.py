"""Content-addressed local persistence for raw scraper documents."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from agents.common.models import RawDocument

_SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
_CONTENT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class SnapshotWriteResult:
    """Result of an idempotent raw snapshot write."""

    path: Path
    created: bool


class RawSnapshotStore:
    """Store one JSON snapshot per source ID and SHA-256 content hash."""

    def __init__(self, root: str | Path = "data/raw") -> None:
        self._root = Path(root)

    def save(self, document: RawDocument) -> SnapshotWriteResult:
        """Persist a document once; an existing content hash is not overwritten."""

        source_dir = self._root / document.source_id
        source_dir.mkdir(parents=True, exist_ok=True)
        path = source_dir / f"{document.content_hash}.json"
        payload = document.model_dump_json(indent=2)

        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                try:
                    handle.write(payload)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                except Exception:
                    handle.close()
                    path.unlink(missing_ok=True)
                    raise
        except FileExistsError:
            return SnapshotWriteResult(path=path, created=False)

        return SnapshotWriteResult(path=path, created=True)

    def load(self, source_id: str, content_hash: str) -> RawDocument:
        """Load and validate a snapshot without accepting path traversal input."""

        self._validate_key(source_id, content_hash)
        path = self._root / source_id / f"{content_hash}.json"
        document = RawDocument.model_validate_json(path.read_text(encoding="utf-8"))
        if document.source_id != source_id or document.content_hash != content_hash:
            raise ValueError("snapshot identity does not match storage key")
        return document

    @staticmethod
    def _validate_key(source_id: str, content_hash: str) -> None:
        if _SOURCE_ID_PATTERN.fullmatch(source_id) is None:
            raise ValueError("invalid source_id")
        if _CONTENT_HASH_PATTERN.fullmatch(content_hash) is None:
            raise ValueError("invalid content_hash")
