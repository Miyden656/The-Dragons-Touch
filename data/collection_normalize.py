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
_SET_COLLECTOR_CAPTURE_RE = re.compile(
    r"^(?P<name>.+?)\s+\((?P<set>[A-Za-z0-9]{2,8})\)\s+(?P<number>[A-Za-z0-9★*\-]+)(?P<tail>.*)$"
)
_QUANTITY_RE = re.compile(r"^\s*(?P<qty>\d+)\s+(?P<rest>.+?)\s*$")
_SUFFIX_RE = re.compile(r"\s+\*[^*]+\*\s*$")

def _normalize_lookup_key(text: object) -> str:
    return " ".join(str(text).strip().lower().replace("\n", " ").split())

def _collector_key(set_code: str | None, collector_number: str | None) -> tuple[str, str] | None:
    if not set_code or not collector_number:
        return None
    number = str(collector_number).strip().lower()
    number = number.replace("★", "").replace("*", "")
    return (str(set_code).strip().lower(), number)

def _build_resolution_indexes(
    scryfall_lookup: dict[str, dict[str, Any]],
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    records = _iter_scryfall_records(scryfall_lookup, scryfall_cards)
    exact_name_index: dict[str, dict[str, Any]] = {}
    alternate_name_index: dict[str, dict[str, Any]] = {}
    set_collector_index: dict[tuple[str, str], dict[str, Any]] = {}

    for card in records:
        name = card.get("name")
        if name:
            exact_name_index.setdefault(str(name).lower(), card)
            exact_name_index.setdefault(_normalize_lookup_key(name), card)

        for alt_key in ["printed_name", "flavor_name"]:
            alt_name = card.get(alt_key)
            if alt_name:
                alternate_name_index.setdefault(str(alt_name).lower(), card)
                alternate_name_index.setdefault(_normalize_lookup_key(alt_name), card)

        for face in card.get("card_faces", []) or []:
            for alt_key in ["name", "printed_name", "flavor_name"]:
                alt_name = face.get(alt_key)
                if alt_name:
                    alternate_name_index.setdefault(str(alt_name).lower(), card)
                    alternate_name_index.setdefault(_normalize_lookup_key(alt_name), card)

        key = _collector_key(card.get("set"), card.get("collector_number"))
        if key:
            set_collector_index.setdefault(key, card)

    return {
        "exact_name": exact_name_index,
        "alternate_name": alternate_name_index,
        "set_collector": set_collector_index,
    }

def _resolve_collection_card(
    card_name: str,
    set_code: str | None,
    collector_number: str | None,
    scryfall_lookup: dict[str, dict[str, Any]],
    indexes: dict[str, Any],
) -> tuple[str, bool, str, dict[str, Any] | None]:
    """Resolve without fuzzy-correcting bad export data.

    Resolution order:
    1. Exact Scryfall name match.
    2. Normalized name match.
    3. Set code + collector number match.
    4. Printed/flavor/card-face alternate name match.
    5. Not found.
    """
    clean = card_name.strip()
    if not clean:
        return clean, False, "not_found", None

    # 1. Exact name match. This uses the original lookup first to preserve legacy behavior.
    record = scryfall_lookup.get(clean.lower()) or indexes["exact_name"].get(clean.lower())
    if record:
        return str(record.get("name") or clean), True, "exact_name", record

    # 2. Normalized name match.
    normalized_key = _normalize_lookup_key(clean)
    record = indexes["exact_name"].get(normalized_key)
    if record:
        return str(record.get("name") or clean), True, "normalized_name", record

    # 3. Set code + collector number match. This is for real alternate printed names/reskins.
    key = _collector_key(set_code, collector_number)
    if key:
        record = indexes["set_collector"].get(key)
        if record:
            return str(record.get("name") or clean), True, "set_collector", record

    # 4. Printed/flavor/card-face alternate name match.
    record = indexes["alternate_name"].get(clean.lower()) or indexes["alternate_name"].get(normalized_key)
    if record:
        return str(record.get("name") or clean), True, "printed_or_alternate_name", record

    return clean, False, "not_found", None

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
