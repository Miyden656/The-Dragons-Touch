"""Companion rule helpers for The Dragon's Touch.

Patch Batch 7 scope:
- Detect official companion cards in companion/reference zones.
- Validate implemented companion restrictions when a companion is actually detected.
- Provide replacement-filter notes for reports/prompts.

This module intentionally keeps companion logic isolated so later patches can add
more companions without spreading special cases through reports and cut logic.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from data.card_lookup import (
    get_full_oracle_text,
    get_representative_nonland_mana_value,
    has_type_on_any_face,
    normalize_text,
)


OFFICIAL_COMPANION_CARD_NAMES: set[str] = {
    "Gyruda, Doom of Depths",
    "Jegantha, the Wellspring",
    "Kaheera, the Orphanguard",
    "Keruga, the Macrosage",
    "Lurrus of the Dream-Den",
    "Lutri, the Spellchaser",
    "Obosh, the Preypiercer",
    "Umori, the Collector",
    "Yorion, Sky Nomad",
    "Zirda, the Dawnwaker",
}

# Backward-compatible public name used by report/debug helpers.
# Keep this alias so companion-card detection has one source of truth.
COMPANION_CARD_NAMES: set[str] = OFFICIAL_COMPANION_CARD_NAMES


IMPLEMENTED_COMPANION_RULES: set[str] = {
    "keruga, the macrosage",
}


def is_companion_card_name(name: object) -> bool:
    return str(name).strip() in OFFICIAL_COMPANION_CARD_NAMES


def card_has_companion_text(card: dict[str, Any] | None) -> bool:
    if not card:
        return False
    return "companion" in normalize_text(get_full_oracle_text(card))


def find_companion_names(
    card_names: Iterable[str],
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Return official or Scryfall-detected companion names from a list of names."""
    scryfall_lookup = scryfall_lookup or {}
    found: list[str] = []
    seen: set[str] = set()

    for raw_name in card_names:
        name = str(raw_name).strip()
        if not name:
            continue
        card = scryfall_lookup.get(name.lower())
        is_companion = is_companion_card_name(name) or card_has_companion_text(card)
        if is_companion and name.lower() not in seen:
            found.append(name)
            seen.add(name.lower())
    return found


def companion_rule_is_implemented(companion_name: str) -> bool:
    return companion_name.strip().lower() in IMPLEMENTED_COMPANION_RULES


def get_companion_restriction_summary(companion_name: str) -> str:
    key = companion_name.strip().lower()
    if key == "keruga, the macrosage":
        return "Keruga restriction: each nonland card in the starting deck must have mana value 3 or greater."
    return "Companion restriction exists, but this specific companion rule is not fully implemented yet; use manual review."


def get_companion_replacement_filter_note(companion_name: str) -> str:
    key = companion_name.strip().lower()
    if key == "keruga, the macrosage":
        return "Keruga replacement filter: suppress nonland card recommendations with mana value 0, 1, or 2."
    return "Replacement filter: only recommend cards that preserve the confirmed companion restriction; manual review required for this companion."


def _is_land_card(card: dict[str, Any]) -> bool:
    return has_type_on_any_face(card, "Land")


def check_card_against_companion(
    companion_name: str,
    card_name: str,
    card: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return (violation, manual_review) for one card under one companion rule."""
    key = companion_name.strip().lower()

    if not card:
        return None, {
            "companion_name": companion_name,
            "card_name": card_name,
            "reason": "Card was not found in Scryfall, so companion legality needs manual review.",
        }

    if key != "keruga, the macrosage":
        return None, {
            "companion_name": companion_name,
            "card_name": card_name,
            "reason": "This companion restriction is not implemented yet; manual companion-legality review required.",
        }

    if _is_land_card(card):
        return None, None

    mana_value = get_representative_nonland_mana_value(card)
    if mana_value is None:
        return None, {
            "companion_name": companion_name,
            "card_name": card_name,
            "reason": "Could not determine nonland mana value for Keruga companion check.",
        }

    if mana_value < 3:
        return {
            "companion_name": companion_name,
            "card_name": card_name,
            "mana_value": mana_value,
            "reason": "Keruga allows only lands and nonland cards with mana value 3 or greater in the starting deck.",
        }, None

    return None, None
