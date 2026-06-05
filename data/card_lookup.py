"""Scryfall card-object helpers.

Round 3 cleanup goal:
- Move face-aware card utility functions out of the monolith.
- Preserve the stable v0.6.2.6 behavior used by later legality, strategy,
  role-tagging, and report modules.
"""

from __future__ import annotations

import re
from typing import Any


def normalize_text(text: object) -> str:
    return " ".join(str(text).lower().replace("\n", " ").split())


def format_color_identity(color_identity: list[str] | set[str] | tuple[str, ...] | None) -> str:
    if not color_identity:
        return "Colorless"
    return "/".join([color for color in ["W", "U", "B", "R", "G"] if color in color_identity])


def get_card_faces(card: dict[str, Any]) -> list[dict[str, Any]]:
    faces = card.get("card_faces", []) or []
    if faces:
        return faces
    return [{
        "name": card.get("name", "Unknown"),
        "type_line": card.get("type_line", ""),
        "oracle_text": card.get("oracle_text", ""),
        "cmc": card.get("cmc", 0),
        "mana_cost": card.get("mana_cost", ""),
    }]


def get_full_oracle_text(card: dict[str, Any]) -> str:
    parts: list[str] = []
    if card.get("oracle_text"):
        parts.append(card.get("oracle_text", ""))
    for face in card.get("card_faces", []) or []:
        face_parts: list[str] = []
        for key in ["name", "type_line", "oracle_text"]:
            if face.get(key):
                face_parts.append(face[key])
        if face_parts:
            parts.append("\n".join(face_parts))
    return "\n\n".join(parts)


def is_basic_land(card: dict[str, Any]) -> bool:
    return "Basic" in card.get("type_line", "") and "Land" in card.get("type_line", "")


def get_duplicate_exception_limit(card: dict[str, Any]) -> int | str | None:
    text = normalize_text(get_full_oracle_text(card))
    if "a deck can have any number of cards named" in text:
        return "unlimited"
    words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    }
    for word, number in words.items():
        if f"a deck can have up to {word} cards named" in text:
            return number
    match = re.search(r"a deck can have up to (\d+) cards named", text)
    return int(match.group(1)) if match else None


def parse_mana_cost_value(mana_cost: str | None) -> float | None:
    """Estimate mana value from a Scryfall mana_cost string.

    This avoids using whole-card combined CMC for split/adventure/room-style faces
    when the face itself has a mana_cost but not a face-level cmc.
    """
    if not mana_cost:
        return None

    total = 0
    symbols = re.findall(r"\{([^}]+)\}", mana_cost)

    for symbol in symbols:
        symbol = symbol.upper()
        if symbol in {"X", "Y", "Z"}:
            continue
        if symbol.isdigit():
            total += int(symbol)
            continue
        if symbol.startswith("2/"):
            total += 2
            continue
        total += 1

    return float(total)


def get_face_mana_values(card: dict[str, Any]) -> list[tuple[str, float, str, str]]:
    values: list[tuple[str, float, str, str]] = []
    whole_card_cmc = card.get("cmc", 0)

    for face in get_card_faces(card):
        face_name = face.get("name", card.get("name", "Unknown"))
        face_type = face.get("type_line", "")
        if "Land" in face_type:
            continue

        mana_cost = face.get("mana_cost", "")
        parsed_cmc = parse_mana_cost_value(mana_cost)

        if parsed_cmc is not None:
            cmc = parsed_cmc
            source = "face mana_cost"
        else:
            face_cmc = face.get("cmc")
            if face_cmc is not None:
                cmc = face_cmc
                source = "face cmc"
            else:
                cmc = whole_card_cmc
                source = "whole-card cmc fallback"

        values.append((face_name, float(cmc or 0), face_type, source))

    return values


def get_representative_nonland_mana_value(card: dict[str, Any]) -> float | None:
    values = get_face_mana_values(card)
    if not values:
        return None
    return min(cmc for _, cmc, _, _ in values)


def format_face_mana_summary(card: dict[str, Any]) -> str:
    values = get_face_mana_values(card)
    if not values:
        return "Land or no nonland mana value"
    return "; ".join(f"{name}: {cmc:g}" for name, cmc, _, _ in values)


def has_type_on_any_face(card: dict[str, Any], card_type: str) -> bool:
    target = card_type.lower()
    for face in get_card_faces(card):
        if target in face.get("type_line", "").lower():
            return True
    return target in card.get("type_line", "").lower()


def get_face_aware_major_types(card: dict[str, Any]) -> set[str]:
    major_card_types = ["Artifact", "Battle", "Creature", "Enchantment", "Instant", "Land", "Planeswalker", "Sorcery"]
    found: set[str] = set()
    for face in get_card_faces(card):
        face_type = face.get("type_line", "")
        for card_type in major_card_types:
            if card_type in face_type:
                found.add(card_type)
    if not found:
        for card_type in major_card_types:
            if card_type in card.get("type_line", ""):
                found.add(card_type)
    return found


def infer_card_type_tags(card: dict[str, Any]) -> list[str]:
    return sorted(card_type.lower() for card_type in get_face_aware_major_types(card))


def build_scryfall_lookup(cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a lower-case name lookup for Scryfall card records.

    Double-faced / modal-DFC / Adventure / split / Battle cards are stored by their
    full ``"Front // Back"`` name, but decklists very often list only the front face
    (e.g. ``"Darkbore Pathway"`` for ``"Darkbore Pathway // Slitherbore Pathway"``).
    Without an alias those cards resolve to nothing, so the engine marks them
    "not found in Scryfall", tags them role-uncertain, and may recommend cutting a
    real dual land. We add per-face aliases so a front-face-only name resolves to
    the full card. Full names are inserted first and the aliases use ``setdefault``,
    so a genuine standalone card that happens to share a face name always wins.
    """
    lookup = {card["name"].lower(): card for card in cards if card.get("name")}

    for card in cards:
        for face in card.get("card_faces", []) or []:
            if not isinstance(face, dict):
                continue
            face_name = face.get("name")
            if face_name:
                lookup.setdefault(str(face_name).lower(), card)
    return lookup


def lookup_card(name: object, scryfall_lookup: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return scryfall_lookup.get(str(name).lower())
