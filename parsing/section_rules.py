"""Decklist section rules.

Round 3 cleanup goal:
- Keep section/header interpretation separate from deck parsing.
- Preserve the legacy v0.6.2.6 behavior for mainboard, companion,
  sideboard/reference-only, and token/helper sections.
"""

from __future__ import annotations

from collections.abc import Mapping

from data.card_lookup import normalize_text


SECTION_HEADERS: dict[str, str] = {
    "commander": "Commander", "commanders": "Commander", "background": "Commander", "backgrounds": "Commander",
    "companion": "Companion", "companions": "Companion",
    "deck": "Deck", "mainboard": "Deck", "main deck": "Deck",
    "creature": "Creatures", "creatures": "Creatures",
    "artifact": "Artifacts", "artifacts": "Artifacts",
    "enchantment": "Enchantments", "enchantments": "Enchantments",
    "instant": "Instants", "instants": "Instants",
    "sorcery": "Sorceries", "sorceries": "Sorceries",
    "land": "Lands", "lands": "Lands",
    "planeswalker": "Planeswalkers", "planeswalkers": "Planeswalkers",
    "battle": "Battles", "battles": "Battles",
    "mana base": "Lands", "manabase": "Lands",
    "ramp": "Custom: Ramp", "removal": "Custom: Removal", "interaction": "Custom: Interaction",
    "card draw": "Custom: Card Draw", "card advantage": "Custom: Card Advantage",
    "recursion": "Custom: Recursion",
    "token generation": "Custom: Token Generation",
    "tokens": "Custom: Tokens",
    "win cons": "Custom: Win Conditions", "win conditions": "Custom: Win Conditions",
}

SECTION_ORDER: list[str] = [
    "Commander", "Companion", "Creatures", "Artifacts", "Enchantments", "Battles",
    "Instants", "Sorceries", "Planeswalkers", "Lands", "Unknown / Needs Review",
]

NON_MAINBOARD_SECTION_HEADERS: set[str] = {
    "cut", "cuts", "cutboard", "removed", "remove", "maybe", "maybeboard", "sideboard",
    "side board", "considering", "consider", "wishlist", "wish list", "not owned",
    "outside the game", "lessons", "lesson", "attractions", "attraction", "stickers",
    "sticker", "planes", "planechase", "schemes", "scheme", "contraptions", "contraption",
}

REFERENCE_ONLY_SECTION_HEADERS: set[str] = {
    "token cards", "generated tokens", "tokens & extras", "tokens and extras", "extras", "extra cards",
    "helper cards", "token helpers", "generated token cards", "emblems", "emblem",
}

NON_MAINBOARD_PREFIXES: tuple[str, ...] = (
    "custom: cut", "custom: cuts", "custom: maybe", "custom: maybeboard", "custom: sideboard",
    "custom: considering", "custom: token cards", "custom: generated tokens",
)

MAJOR_CARD_TYPES: list[str] = ["Artifact", "Battle", "Creature", "Enchantment", "Instant", "Land", "Planeswalker", "Sorcery"]

MANUAL_SECTION_EXPECTED_TYPES: dict[str, set[str]] = {
    "Artifacts": {"Artifact"}, "Battles": {"Battle"}, "Creatures": {"Creature"},
    "Enchantments": {"Enchantment"}, "Instants": {"Instant"}, "Lands": {"Land"},
    "Planeswalkers": {"Planeswalker"}, "Sorceries": {"Sorcery"},
}

LIKELY_TOKEN_OR_HELPER_NAMES: set[str] = {
    "copy", "treasure", "food", "clue", "blood", "incubator", "map", "junk",
    "beast", "bird", "cat", "dog", "dinosaur", "dragon", "elf warrior",
    "goblin", "human", "human soldier", "insect", "rabbit", "saproling",
    "soldier", "spirit", "thopter", "zombie", "construct", "elemental",
    "rhino", "rhino warrior", "warrior", "plant", "fungus", "squirrel", "servo",
    "phyrexian", "incubator phyrexian", "monarch", "initiative",
}


def section_is_non_mainboard(section_name: object) -> bool:
    lowered = normalize_text(str(section_name).replace("Custom:", "").strip())
    if lowered == "companion" or lowered in NON_MAINBOARD_SECTION_HEADERS or lowered in REFERENCE_ONLY_SECTION_HEADERS:
        return True
    lowered_full = normalize_text(section_name)
    return any(lowered_full.startswith(prefix) for prefix in NON_MAINBOARD_PREFIXES)


def is_likely_token_or_helper_name(card_name: object) -> bool:
    cleaned = normalize_text(str(card_name).replace("//", " ").strip())
    if cleaned in LIKELY_TOKEN_OR_HELPER_NAMES:
        return True
    if len(cleaned.split()) <= 3 and any(word in cleaned.split() for word in ["token", "emblem"]):
        return True
    return False


def should_ignore_card_from_tokens_section(card_name: object, scryfall_lookup: Mapping[str, dict] | None = None) -> bool:
    # Legacy behavior: token/helper sections should not count normal token names as mainboard,
    # even if Scryfall recognizes a token object with that name.
    return is_likely_token_or_helper_name(card_name)


def is_token_helper_section(section_name: object) -> bool:
    cleaned = normalize_text(str(section_name).replace("Custom:", "").replace("Reference:", "").strip())
    if cleaned in {
        "tokens", "token", "token cards", "generated tokens", "tokens & extras", "tokens and extras",
        "extras", "helper cards", "token helpers", "generated token cards", "emblems", "emblem",
    }:
        return True
    if "token" in cleaned and any(word in cleaned for word in ["extra", "generated", "helper", "card"]):
        return True
    return False
