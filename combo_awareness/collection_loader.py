#!/usr/bin/env python3
"""v0.8.6.2-dev — local collection loading for combo awareness.

Scope guard: loader split only; no behavior changes, no API calls.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .deck_parser import extract_card_name_from_line
from .models import CollectionIndex
from .normalization import normalize_card_name

LIKELY_COLLECTION_NAME_FIELDS = [
    "name",
    "card name",
    "cardname",
    "card",
    "title",
]

def read_csv_collection_file(path: Path, collection_index: CollectionIndex) -> None:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            return

        normalized_fields = {normalize_card_name(field): field for field in reader.fieldnames if field}
        name_field = None
        for candidate in LIKELY_COLLECTION_NAME_FIELDS:
            if candidate in normalized_fields:
                name_field = normalized_fields[candidate]
                break
        if name_field is None:
            name_field = reader.fieldnames[0]

        for row in reader:
            collection_index.add(row.get(name_field, ""), path)

def read_text_collection_file(path: Path, collection_index: CollectionIndex) -> None:
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "//")):
            continue
        parsed = extract_card_name_from_line(line)
        if parsed:
            _, card_name = parsed
            collection_index.add(card_name, path)
        else:
            collection_index.add(line, path)

def load_collection_index(collection_dir: Path | None) -> CollectionIndex:
    collection = CollectionIndex()
    if collection_dir is None or not collection_dir.exists():
        return collection

    supported_suffixes = {".txt", ".csv", ".tsv"}
    for path in sorted(collection_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in supported_suffixes:
            continue
        try:
            if path.suffix.lower() in {".csv", ".tsv"}:
                read_csv_collection_file(path, collection)
            else:
                read_text_collection_file(path, collection)
        except Exception:
            # Collection parsing should not break isolated combo matching.
            continue
    return collection

