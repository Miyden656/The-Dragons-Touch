"""Collection/card-pool loader for The Dragon's Touch.

v0.6.4.1 scope:
- Load a local TXT collection/card-pool file.
- Parse quantity + card name lines in common MTG/decklist export format.
- Normalize names against the local Scryfall lookup when available.
- Report counts and not-found entries.
- Do not make recommendations yet.

Recommended MVP format:
    1 Sol Ring
    1 Keruga, the Macrosage (IKO) 225
    4 Duress (STA) 29

CSV support is intentionally minimal and best-effort for later compatibility. The
TXT loader is the primary supported path for this patch.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


_SET_COLLECTOR_RE = re.compile(r"\s+\([A-Z0-9]{2,8}\)\s+[A-Za-z0-9★*\-]+.*$")
_QUANTITY_RE = re.compile(r"^\s*(?P<qty>\d+)\s+(?P<rest>.+?)\s*$")
_SUFFIX_RE = re.compile(r"\s+\*[^*]+\*\s*$")


@dataclass(slots=True)
class CollectionCardEntry:
    raw_line: str
    card_name: str
    quantity: int = 1
    normalized_name: str | None = None
    found_in_scryfall: bool = False


@dataclass(slots=True)
class CollectionLoadSummary:
    mode: str = "none"
    collection_file: str | None = None
    loaded: bool = False
    file_exists: bool = False
    total_cards: int = 0
    unique_cards: int = 0
    found_cards: int = 0
    not_found_cards: list[str] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)
    entries: list[CollectionCardEntry] = field(default_factory=list)
    card_quantities: Counter[str] = field(default_factory=Counter)

    @property
    def active(self) -> bool:
        return self.mode != "none"

    @property
    def ready_for_matching(self) -> bool:
        return self.active and self.loaded and self.unique_cards > 0


def _lookup_name(name: str, scryfall_lookup: dict[str, dict[str, Any]]) -> tuple[str, bool]:
    """Return canonical name if found in Scryfall lookup, else original name."""
    clean = name.strip()
    if not clean:
        return clean, False

    candidates = [clean, clean.lower()]
    # Some local lookup builders use lower-case keys; some keep canonical names.
    for candidate in candidates:
        record = scryfall_lookup.get(candidate)
        if record:
            return str(record.get("name") or clean), True

    # Try exact case-insensitive search only as a small fallback. The collection
    # file is usually only a few hundred cards, but Scryfall lookup is large; keep
    # this cheap by not doing fuzzy matching.
    lowered = clean.lower()
    record = scryfall_lookup.get(lowered)
    if record:
        return str(record.get("name") or clean), True
    return clean, False


def _strip_export_suffixes(text: str) -> str:
    """Remove set/collector/foil suffixes while preserving card names."""
    value = text.strip()
    value = _SUFFIX_RE.sub("", value).strip()
    value = _SET_COLLECTOR_RE.sub("", value).strip()
    return value


def parse_collection_txt_lines(lines: Iterable[str], scryfall_lookup: dict[str, dict[str, Any]] | None = None) -> tuple[list[CollectionCardEntry], list[str]]:
    scryfall_lookup = scryfall_lookup or {}
    entries: list[CollectionCardEntry] = []
    warnings: list[str] = []

    for line_number, raw in enumerate(lines, start=1):
        raw_line = raw.rstrip("\n")
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        quantity = 1
        card_text = stripped
        match = _QUANTITY_RE.match(stripped)
        if match:
            quantity = int(match.group("qty"))
            card_text = match.group("rest").strip()

        card_name = _strip_export_suffixes(card_text)
        if not card_name:
            warnings.append(f"Line {line_number}: could not parse card name from `{raw_line}`")
            continue

        normalized, found = _lookup_name(card_name, scryfall_lookup)
        entries.append(CollectionCardEntry(
            raw_line=raw_line,
            card_name=card_name,
            quantity=max(1, quantity),
            normalized_name=normalized,
            found_in_scryfall=found,
        ))

    return entries, warnings


def _first_present(row: dict[str, str], keys: list[str]) -> str | None:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        if key in lowered and str(lowered[key]).strip():
            return str(lowered[key]).strip()
    return None


def parse_collection_csv(path: Path, scryfall_lookup: dict[str, dict[str, Any]] | None = None) -> tuple[list[CollectionCardEntry], list[str]]:
    """Best-effort CSV parser for common inventory exports.

    TXT remains the preferred format for v0.6.4.1. This exists so a simple CSV
    with Name/Quantity columns can be counted without failing.
    """
    scryfall_lookup = scryfall_lookup or {}
    entries: list[CollectionCardEntry] = []
    warnings: list[str] = []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return [], ["CSV file has no header row; use TXT format or add Name/Quantity columns."]
            for line_number, row in enumerate(reader, start=2):
                name = _first_present(row, ["name", "card name", "card", "card_name"])
                qty_text = _first_present(row, ["quantity", "qty", "count", "owned"])
                if not name:
                    warnings.append(f"CSV line {line_number}: no recognized card-name column")
                    continue
                try:
                    quantity = int(qty_text) if qty_text else 1
                except ValueError:
                    quantity = 1
                normalized, found = _lookup_name(name, scryfall_lookup)
                entries.append(CollectionCardEntry(
                    raw_line=", ".join(f"{k}={v}" for k, v in row.items()),
                    card_name=name,
                    quantity=max(1, quantity),
                    normalized_name=normalized,
                    found_in_scryfall=found,
                ))
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for line_number, row in enumerate(reader, start=2):
                name = _first_present(row, ["name", "card name", "card", "card_name"])
                if not name:
                    warnings.append(f"CSV line {line_number}: no recognized card-name column")
                    continue
                normalized, found = _lookup_name(name, scryfall_lookup)
                entries.append(CollectionCardEntry(raw_line=str(row), card_name=name, quantity=1, normalized_name=normalized, found_in_scryfall=found))

    return entries, warnings


def load_collection_file(
    collection_file: str | Path | None,
    mode: str = "none",
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
) -> CollectionLoadSummary:
    """Load and summarize a local collection/card-pool file.

    The summary is intentionally passive in v0.6.4.1. Later patches will consume
    the parsed entries for candidate matching and collection-only/preferred logic.
    """
    normalized_mode = (mode or "none").strip().lower()
    if normalized_mode in {"off", "no", "false", "0", "disabled"}:
        normalized_mode = "none"
    if normalized_mode not in {"none", "prefer", "only", "shakeup"}:
        normalized_mode = "none"

    summary = CollectionLoadSummary(mode=normalized_mode, collection_file=str(collection_file) if collection_file else None)
    if normalized_mode == "none":
        summary.parse_warnings.append("Collection mode is off; no collection file was loaded.")
        return summary

    if not collection_file:
        summary.parse_warnings.append("Collection mode is active, but no collection file was provided.")
        return summary

    path = Path(collection_file).expanduser()
    summary.collection_file = str(path)
    summary.file_exists = path.exists()
    if not path.exists():
        summary.parse_warnings.append(f"Collection file not found: {path}")
        return summary

    if path.suffix.lower() == ".csv":
        entries, warnings = parse_collection_csv(path, scryfall_lookup=scryfall_lookup)
    else:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            entries, warnings = parse_collection_txt_lines(handle, scryfall_lookup=scryfall_lookup)

    quantities: Counter[str] = Counter()
    not_found: list[str] = []
    for entry in entries:
        key = entry.normalized_name or entry.card_name
        quantities[key] += entry.quantity
        if not entry.found_in_scryfall and entry.card_name not in not_found:
            not_found.append(entry.card_name)

    summary.loaded = True
    summary.entries = entries
    summary.total_cards = sum(entry.quantity for entry in entries)
    summary.unique_cards = len(quantities)
    summary.found_cards = len([entry for entry in entries if entry.found_in_scryfall])
    summary.not_found_cards = not_found
    summary.parse_warnings = warnings
    summary.card_quantities = quantities
    return summary
