#!/usr/bin/env python3
"""v0.8.6.2-dev — combo index and Scryfall identity loading.

Scope guard: loader split only; no behavior changes, no API calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DeckData
from .normalization import canonical_identity, normalize_card_name

def load_combo_index(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        raise FileNotFoundError(f"Combo index not found: {index_path}")
    with index_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def load_scryfall_name_identity_map(scryfall_path: Path) -> dict[str, set[str]]:
    """Load a flexible name -> color_identity map from local Scryfall data if available."""
    if not scryfall_path.exists():
        return {}

    try:
        with scryfall_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception:
        return {}

    cards: list[dict[str, Any]] = []
    if isinstance(raw, list):
        cards = [entry for entry in raw if isinstance(entry, dict)]
    elif isinstance(raw, dict):
        if isinstance(raw.get("data"), list):
            cards = [entry for entry in raw.get("data", []) if isinstance(entry, dict)]
        elif isinstance(raw.get("cards"), list):
            cards = [entry for entry in raw.get("cards", []) if isinstance(entry, dict)]
        else:
            # Some local caches use card name as the key and card object as the value.
            for key, value in raw.items():
                if isinstance(value, dict):
                    card = dict(value)
                    card.setdefault("name", key)
                    cards.append(card)

    identity_by_name: dict[str, set[str]] = {}
    for card in cards:
        name = card.get("name") or card.get("card_name")
        if not name:
            continue
        identity = card.get("color_identity")
        if identity is None:
            identity = card.get("colorIdentity")
        if identity is None:
            identity = card.get("identity")
        identity_by_name[normalize_card_name(name)] = canonical_identity(identity)
    return identity_by_name

def infer_commander_identity(deck: DeckData, scryfall_identity_by_name: dict[str, set[str]]) -> set[str] | None:
    """Infer combined commander color identity from local Scryfall data."""
    if not deck.commander_names:
        return None
    found_any = False
    combined: set[str] = set()
    for commander in deck.commander_names:
        identity = scryfall_identity_by_name.get(normalize_card_name(commander))
        if identity is None:
            continue
        found_any = True
        combined.update(identity)
    if not found_any:
        return None
    return combined

