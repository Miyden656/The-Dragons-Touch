#!/usr/bin/env python3
"""v0.8.6.2-dev — shared normalization helpers for combo awareness.

Scope guard: helper split only; no behavior changes, no API calls, no app integration.
"""

from __future__ import annotations

import re
from typing import Iterable

MANA_SYMBOL_ORDER = "WUBRG"
SET_SUFFIX_RE = re.compile(r"\s+\([A-Z0-9]+\)\s+\d+.*$", re.IGNORECASE)
TRAILING_CATEGORY_RE = re.compile(r"\s+#.*$")
BRACKET_TAG_RE = re.compile(r"\s*\[[^\]]+\]\s*$")

def normalize_card_name(name: str) -> str:
    """Normalize card names for matching across decklists, collection files, and combo index."""
    return " ".join(str(name).strip().casefold().split())

def clean_card_name(raw_name: str) -> str:
    """Clean common deck/export decorations while preserving real card names."""
    name = str(raw_name).strip()
    if not name:
        return ""
    name = TRAILING_CATEGORY_RE.sub("", name).strip()
    name = SET_SUFFIX_RE.sub("", name).strip()
    name = BRACKET_TAG_RE.sub("", name).strip()
    name = name.strip('"').strip("'").strip()
    return name

def normalize_header_text(text: str) -> str:
    """Normalize deck section/header text for parser decisions."""
    return " ".join(str(text).strip().casefold().rstrip(":").split())

def canonical_identity(identity: str | Iterable[str] | None) -> set[str]:
    """Convert WUBRG-like identity values into a set of mana color letters."""
    if identity is None:
        return set()
    if isinstance(identity, str):
        text = identity.upper().replace("C", "")
        return {char for char in text if char in MANA_SYMBOL_ORDER}
    result: set[str] = set()
    for item in identity:
        text = str(item).upper()
        for char in text:
            if char in MANA_SYMBOL_ORDER:
                result.add(char)
    return result

def identity_to_string(identity_set: set[str]) -> str:
    if not identity_set:
        return "Colorless/unknown"
    return "".join([char for char in MANA_SYMBOL_ORDER if char in identity_set])

def is_subset_identity(combo_identity: str | Iterable[str] | None, commander_identity: set[str] | None) -> bool:
    if commander_identity is None:
        return True
    return canonical_identity(combo_identity).issubset(commander_identity)

