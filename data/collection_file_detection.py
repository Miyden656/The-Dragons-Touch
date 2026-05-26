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

def _iter_scryfall_records(
    scryfall_lookup: dict[str, dict[str, Any]],
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if scryfall_cards:
        return [card for card in scryfall_cards if isinstance(card, dict)]
    # Fallback is less complete because name lookup collapses printings, but it
    # preserves compatibility if full Scryfall cards are not passed yet.
    return [card for card in scryfall_lookup.values() if isinstance(card, dict)]

def _first_present(row: dict[str, str], keys: list[str]) -> str | None:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        if key in lowered and str(lowered[key]).strip():
            return str(lowered[key]).strip()
    return None
