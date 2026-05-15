#!/usr/bin/env python3
"""v0.8.6.2.2-dev — core combo matching logic.

Scope guard: matcher split only; no behavior changes, no API calls, no app integration.
"""

from __future__ import annotations

from typing import Any

from .models import CollectionIndex, DeckData, MatchResult, MatchSummary
from .normalization import normalize_card_name, is_subset_identity

def combo_must_be_commander_satisfied(combo: dict[str, Any], deck: DeckData) -> bool:
    required = combo.get("must_be_commander_card_names") or []
    if not required:
        return True
    normalized_commanders = deck.normalized_commanders
    for name in required:
        if normalize_card_name(name) not in normalized_commanders:
            return False
    return True

def combo_card_names(combo: dict[str, Any]) -> list[str]:
    names = combo.get("card_names") or []
    if names:
        return [str(name) for name in names]
    cards = combo.get("cards") or []
    return [str(card.get("name")) for card in cards if isinstance(card, dict) and card.get("name")]

def match_deck_to_combo_index(
    deck: DeckData,
    combo_index: dict[str, Any],
    *,
    commander_identity: set[str] | None,
    collection: CollectionIndex | None = None,
    include_spoilers: bool = False,
    strict_color_identity: bool = True,
    hide_invalid_must_be_commander: bool = True,
) -> MatchSummary:
    """Find complete and one-card-away combos for one deck."""
    summary = MatchSummary()
    deck_cards = deck.normalized_all_cards
    collection = collection or CollectionIndex()

    for combo in combo_index.get("combos", []):
        summary.scanned_combos += 1

        if combo.get("spoiler", False) and not include_spoilers:
            summary.skipped_spoiler += 1
            continue

        if strict_color_identity and commander_identity is not None:
            if not is_subset_identity(combo.get("identity"), commander_identity):
                summary.skipped_color_identity += 1
                continue

        if hide_invalid_must_be_commander and not combo_must_be_commander_satisfied(combo, deck):
            summary.skipped_must_be_commander += 1
            continue

        names = combo_card_names(combo)
        if not names:
            summary.skipped_unusable_shape += 1
            continue

        normalized_combo_cards = [normalize_card_name(name) for name in names]
        missing = [name for name, normalized in zip(names, normalized_combo_cards) if normalized not in deck_cards]

        if not missing:
            summary.complete_combos.append(MatchResult(combo=combo, missing_card_names=[]))
        elif len(missing) == 1:
            missing_sources = {
                missing_card: collection.find_sources(missing_card)
                for missing_card in missing
            }
            summary.one_card_away_combos.append(
                MatchResult(
                    combo=combo,
                    missing_card_names=missing,
                    collection_sources_by_missing_card=missing_sources,
                )
            )

    return summary

