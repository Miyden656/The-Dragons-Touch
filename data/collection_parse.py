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

def _parse_card_text_and_print_info(card_text: str) -> tuple[str, str | None, str | None]:
    value = _SUFFIX_RE.sub("", card_text.strip()).strip()
    match = _SET_COLLECTOR_CAPTURE_RE.match(value)
    if not match:
        return value, None, None
    name = match.group("name").strip()
    set_code = match.group("set").strip().upper()
    collector_number = match.group("number").strip()
    return name, set_code, collector_number
