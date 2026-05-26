"""Collection manifest scanning helpers.

This module records what collection files are present without parsing card
ownership details or changing collection data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


SUPPORTED_COLLECTION_SUFFIXES = {
    ".csv",
    ".txt",
    ".json",
    ".jsonl",
    ".tsv",
    ".xlsx",
}


@dataclass(frozen=True)
class CollectionFileRecord:
    """A safe manifest record for one collection file."""

    path: Path
    suffix: str
    size_bytes: int

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "suffix": self.suffix,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class CollectionManifest:
    """A safe snapshot of collection files currently present."""

    collection_dir: Path
    records: List[CollectionFileRecord] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.records)

    def as_dict(self) -> dict:
        return {
            "collection_dir": str(self.collection_dir),
            "file_count": self.file_count,
            "records": [record.as_dict() for record in self.records],
        }


def scan_collection_manifest(collection_dir: Path, include_suffixes: Iterable[str] | None = None) -> CollectionManifest:
    """Return a manifest of collection-like files without modifying them."""

    suffixes = {suffix.lower() for suffix in (include_suffixes or SUPPORTED_COLLECTION_SUFFIXES)}
    records: List[CollectionFileRecord] = []
    if collection_dir.exists():
        for path in sorted(collection_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name == ".gitkeep":
                continue
            suffix = path.suffix.lower()
            if suffix in suffixes:
                records.append(CollectionFileRecord(path=path, suffix=suffix, size_bytes=path.stat().st_size))
    return CollectionManifest(collection_dir=collection_dir, records=records)
