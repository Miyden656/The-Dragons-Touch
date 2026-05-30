"""Collection/card-pool loader for The Dragon's Touch.

v0.6.4.2 scope:
- Improve Scryfall resolution for local collection exports.
- Continue loading one or more TXT collection/card-pool files.
- Support entire collection-folder loading by combining every .txt file.
- Parse quantity + card name lines in common MTG/decklist export format.
- Preserve original exported names while resolving to Scryfall canonical names.
- Resolve real alternate/Universes Within style exports by set code + collector number when full Scryfall print data is available.
- Do not fuzzy-correct OCR/scanner/export mistakes.
- Do not make recommendations yet.

Recommended MVP format:
    1 Sol Ring
    1 Keruga, the Macrosage (IKO) 225
    4 Duress (STA) 29
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


_SET_COLLECTOR_CAPTURE_RE = re.compile(
    r"^(?P<name>.+?)\s+\((?P<set>[A-Za-z0-9]{2,8})\)\s+(?P<number>[A-Za-z0-9★*\-]+)(?P<tail>.*)$"
)
_QUANTITY_RE = re.compile(r"^\s*(?P<qty>\d+)\s+(?P<rest>.+?)\s*$")
_SUFFIX_RE = re.compile(r"\s+\*[^*]+\*\s*$")


# v1.6.1 Phase 4: name-resolution logic moved to data/card_resolution.py so
# the deck builder can call into the same routines. Re-imported here so the
# existing collection_loader API surface (parse_*, load_*) is unchanged.
from data.card_resolution import (
    build_card_resolution_indexes as _build_resolution_indexes,
    resolve_card_in_indexes as _resolve_collection_card_in_indexes,
    normalize_lookup_key as _normalize_lookup_key,
    collector_key as _collector_key,
)


def _resolve_collection_card(
    card_name: str,
    set_code: str | None,
    collector_number: str | None,
    scryfall_lookup: dict[str, dict[str, Any]],
    indexes: dict[str, Any],
) -> tuple[str, bool, str, dict[str, Any] | None]:
    """Thin wrapper preserving the historical loader signature.

    The full resolution logic now lives in data/card_resolution.py so the
    builder can reuse it. Keeping this wrapper means the call sites below
    don't have to change.
    """
    return _resolve_collection_card_in_indexes(
        card_name, set_code, collector_number, scryfall_lookup, indexes,
    )


@dataclass(slots=True)
class CollectionCardEntry:
    raw_line: str
    card_name: str
    quantity: int = 1
    normalized_name: str | None = None
    found_in_scryfall: bool = False
    source_file: str | None = None
    set_code: str | None = None
    collector_number: str | None = None
    resolution_method: str = "not_found"
    scryfall_name: str | None = None


@dataclass(slots=True)
class CollectionLoadSummary:
    mode: str = "none"
    collection_file: str | None = None
    source_mode: str = "none"
    collection_folder: str | None = None
    selected_files: list[str] = field(default_factory=list)
    loaded: bool = False
    file_exists: bool = False
    total_cards: int = 0
    unique_cards: int = 0
    found_cards: int = 0
    not_found_cards: list[str] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)
    entries: list[CollectionCardEntry] = field(default_factory=list)
    card_quantities: Counter[str] = field(default_factory=Counter)
    card_sources: dict[str, list[str]] = field(default_factory=dict)
    exact_name_matches: int = 0
    normalized_name_matches: int = 0
    set_collector_matches: int = 0
    printed_or_alternate_name_matches: int = 0
    unresolved_entries: int = 0
    resolution_method_counts: Counter[str] = field(default_factory=Counter)
    resolved_name_examples: list[str] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.mode != "none"

    @property
    def ready_for_matching(self) -> bool:
        return self.active and self.loaded and self.unique_cards > 0

    @property
    def source_file_count(self) -> int:
        return len(self.selected_files)


# v1.6.1 Phase 4: _normalize_lookup_key, _collector_key, _iter_scryfall_records,
# _build_resolution_indexes, and the resolver were moved to
# data/card_resolution.py and re-imported at the top of this file. The thin
# `_resolve_collection_card` wrapper preserves the legacy call signature so
# the parse_* / load_* functions below don't need any changes.


def _parse_card_text_and_print_info(card_text: str) -> tuple[str, str | None, str | None]:
    value = _SUFFIX_RE.sub("", card_text.strip()).strip()
    match = _SET_COLLECTOR_CAPTURE_RE.match(value)
    if not match:
        return value, None, None
    name = match.group("name").strip()
    set_code = match.group("set").strip().upper()
    collector_number = match.group("number").strip()
    return name, set_code, collector_number


def parse_collection_txt_lines(
    lines: Iterable[str],
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    source_file: str | None = None,
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> tuple[list[CollectionCardEntry], list[str]]:
    scryfall_lookup = scryfall_lookup or {}
    indexes = _build_resolution_indexes(scryfall_lookup, scryfall_cards)
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

        card_name, set_code, collector_number = _parse_card_text_and_print_info(card_text)
        if not card_name:
            location = f"{Path(source_file).name}:" if source_file else ""
            warnings.append(f"{location}Line {line_number}: could not parse card name from `{raw_line}`")
            continue

        resolved_name, found, method, _record = _resolve_collection_card(
            card_name,
            set_code,
            collector_number,
            scryfall_lookup,
            indexes,
        )
        entries.append(CollectionCardEntry(
            raw_line=raw_line,
            card_name=card_name,
            quantity=max(1, quantity),
            normalized_name=resolved_name,
            found_in_scryfall=found,
            source_file=str(source_file) if source_file else None,
            set_code=set_code,
            collector_number=collector_number,
            resolution_method=method,
            scryfall_name=resolved_name if found else None,
        ))

    return entries, warnings


def _first_present(row: dict[str, str], keys: list[str]) -> str | None:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        if key in lowered and str(lowered[key]).strip():
            return str(lowered[key]).strip()
    return None


def parse_collection_csv(
    path: Path,
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> tuple[list[CollectionCardEntry], list[str]]:
    """Best-effort CSV parser for simple Name/Quantity inventory exports."""
    scryfall_lookup = scryfall_lookup or {}
    indexes = _build_resolution_indexes(scryfall_lookup, scryfall_cards)
    entries: list[CollectionCardEntry] = []
    warnings: list[str] = []

    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except UnicodeDecodeError:
        handle = path.open("r", encoding="utf-8", errors="replace", newline="")

    with handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return [], [f"{path.name}: CSV file has no header row; use TXT format or add Name/Quantity columns."]
        for line_number, row in enumerate(reader, start=2):
            name = _first_present(row, ["name", "card name", "card", "card_name"])
            qty_text = _first_present(row, ["quantity", "qty", "count", "owned"])
            set_code = _first_present(row, ["set", "set code", "set_code", "edition"])
            collector_number = _first_present(row, ["collector number", "collector_number", "number", "collector"])
            if not name:
                warnings.append(f"{path.name}: CSV line {line_number}: no recognized card-name column")
                continue
            try:
                quantity = int(qty_text) if qty_text else 1
            except ValueError:
                quantity = 1
            resolved_name, found, method, _record = _resolve_collection_card(
                name,
                set_code,
                collector_number,
                scryfall_lookup,
                indexes,
            )
            entries.append(CollectionCardEntry(
                raw_line=", ".join(f"{k}={v}" for k, v in row.items()),
                card_name=name,
                quantity=max(1, quantity),
                normalized_name=resolved_name,
                found_in_scryfall=found,
                source_file=str(path),
                set_code=str(set_code).upper() if set_code else None,
                collector_number=collector_number,
                resolution_method=method,
                scryfall_name=resolved_name if found else None,
            ))

    return entries, warnings


def _normalize_mode(mode: str | None) -> str:
    normalized_mode = (mode or "none").strip().lower()
    if normalized_mode in {"off", "no", "false", "0", "disabled"}:
        normalized_mode = "none"
    if normalized_mode not in {"none", "prefer", "only", "shakeup"}:
        normalized_mode = "none"
    return normalized_mode


def _summarize_entries(summary: CollectionLoadSummary, entries: list[CollectionCardEntry], warnings: list[str]) -> CollectionLoadSummary:
    quantities: Counter[str] = Counter()
    not_found: list[str] = []
    sources: dict[str, set[str]] = defaultdict(set)
    method_counts: Counter[str] = Counter()
    resolved_examples: list[str] = []

    for entry in entries:
        key = entry.normalized_name or entry.card_name
        quantities[key] += entry.quantity
        method_counts[entry.resolution_method] += 1
        if entry.source_file:
            sources[key].add(str(entry.source_file))
        if not entry.found_in_scryfall and entry.card_name not in not_found:
            not_found.append(entry.card_name)
        if entry.found_in_scryfall and entry.scryfall_name and entry.card_name != entry.scryfall_name:
            example = f"{entry.card_name} -> {entry.scryfall_name}"
            if entry.set_code and entry.collector_number:
                example += f" ({entry.set_code} {entry.collector_number})"
            if example not in resolved_examples:
                resolved_examples.append(example)

    summary.loaded = True
    summary.file_exists = bool(summary.selected_files)
    summary.entries = entries
    summary.total_cards = sum(entry.quantity for entry in entries)
    summary.unique_cards = len(quantities)
    summary.found_cards = len([entry for entry in entries if entry.found_in_scryfall])
    summary.not_found_cards = not_found
    summary.parse_warnings = warnings
    summary.card_quantities = quantities
    summary.card_sources = {card: sorted(values) for card, values in sources.items()}
    summary.resolution_method_counts = method_counts
    summary.exact_name_matches = method_counts.get("exact_name", 0)
    summary.normalized_name_matches = method_counts.get("normalized_name", 0)
    summary.set_collector_matches = method_counts.get("set_collector", 0)
    summary.printed_or_alternate_name_matches = method_counts.get("printed_or_alternate_name", 0)
    summary.unresolved_entries = method_counts.get("not_found", 0)
    summary.resolved_name_examples = resolved_examples[:20]
    return summary


def load_collection_sources(
    collection_files: Sequence[str | Path] | None,
    mode: str = "none",
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    source_mode: str = "selected_files",
    collection_folder: str | Path | None = None,
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> CollectionLoadSummary:
    """Load and combine one or more collection files.

    This entry point supports selected files and entire-folder selection,
    aggregating duplicate card names across sources.
    """
    normalized_mode = _normalize_mode(mode)
    summary = CollectionLoadSummary(
        mode=normalized_mode,
        collection_file="; ".join(str(item) for item in (collection_files or [])) if collection_files else None,
        source_mode=source_mode if normalized_mode != "none" else "none",
        collection_folder=str(collection_folder) if collection_folder else None,
        selected_files=[str(Path(item)) for item in (collection_files or [])],
    )

    if normalized_mode == "none":
        summary.parse_warnings.append("Collection mode is off; no collection file was loaded.")
        return summary

    if not collection_files:
        summary.parse_warnings.append("Collection mode is active, but no collection files were selected or found.")
        return summary

    all_entries: list[CollectionCardEntry] = []
    all_warnings: list[str] = []
    existing_files: list[str] = []
    missing_files: list[str] = []

    for raw_path in collection_files:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            missing_files.append(str(path))
            all_warnings.append(f"Collection file not found: {path}")
            continue
        existing_files.append(str(path))
        if path.suffix.lower() == ".csv":
            entries, warnings = parse_collection_csv(path, scryfall_lookup=scryfall_lookup, scryfall_cards=scryfall_cards)
        else:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                entries, warnings = parse_collection_txt_lines(
                    handle,
                    scryfall_lookup=scryfall_lookup,
                    source_file=str(path),
                    scryfall_cards=scryfall_cards,
                )
        all_entries.extend(entries)
        all_warnings.extend(warnings)

    summary.selected_files = existing_files + missing_files
    summary.collection_file = "; ".join(summary.selected_files) if summary.selected_files else None
    summary.file_exists = bool(existing_files)
    if not existing_files:
        summary.parse_warnings = all_warnings
        return summary

    return _summarize_entries(summary, all_entries, all_warnings)


def load_collection_file(
    collection_file: str | Path | None,
    mode: str = "none",
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> CollectionLoadSummary:
    """Backward-compatible single-file loader."""
    files: list[str | Path] = [collection_file] if collection_file else []
    return load_collection_sources(
        files,
        mode=mode,
        scryfall_lookup=scryfall_lookup,
        source_mode="selected_files",
        scryfall_cards=scryfall_cards,
    )
