"""Commander Game Changers — curated list (v1.6.2 Phase E).

WHY THIS FILE EXISTS
--------------------
The Commander Rules Committee maintains a published list of cards known
as "Game Changers" — high-power staples that signal bracket pressure when
present in a deck. The bracket guidance limits Game Changer count:
  - Bracket 1 (Exhibition):    0 Game Changers
  - Bracket 2 (Core / Casual):  0 Game Changers
  - Bracket 3 (Upgraded):       up to 3
  - Bracket 4 (Optimized):      unlimited (still disclose pregame)
  - Bracket 5 (cEDH):           unlimited

Phase 5 added `game_changer_count_limit` to `rules/bracket_definitions.py`
but had no consumer that actually counted Game Changers in the final deck.
This module is the source list; the builder tallies and the Build
Validation report surfaces the count vs. the bracket's limit.

POLICY
------
- Update GAME_CHANGERS when the RC adds or removes cards from their list.
- Cards are matched by lowercase canonical Scryfall name.
- The list is intentionally curated rather than tag-derived because the
  RC's list is specific (e.g., Demonic Tutor is on it, Worldly Tutor is
  not; Sol Ring is famously NOT on it despite being the most-played
  fast mana in Commander).

PUBLIC API
----------
- GAME_CHANGERS                    : frozenset[str]
- is_game_changer(card_name)        -> bool
- count_game_changers(card_names)   -> int
- game_changer_status(count, limit) -> tuple[str, str]  # (status, message)
"""
from __future__ import annotations

from typing import Iterable


# Curated Game Changers list as of 2025. Lower-case canonical Scryfall name.
# When the Commander Rules Committee updates their list, edit this set and
# the test will catch any regressions.
GAME_CHANGERS: frozenset[str] = frozenset({
    # ----- White -----
    "drannith magistrate",
    "enlightened tutor",
    "serra's sanctum",
    "smothering tithe",
    "trouble in pairs",

    # ----- Blue -----
    "consecrated sphinx",
    "cyclonic rift",
    "expropriate",
    "fierce guardianship",
    "force of will",
    "mana drain",
    "mystic remora",
    "mystical tutor",
    "rhystic study",
    "thassa's oracle",
    "urza, lord high artificer",

    # ----- Black -----
    "ad nauseam",
    "bolas's citadel",
    "demonic tutor",
    "grim tutor",
    "imperial seal",
    "necropotence",
    "opposition agent",
    "tergrid, god of fright // tergrid's lantern",
    "vampiric tutor",
    "yawgmoth, thran physician",

    # ----- Red -----
    "jeska's will",
    "underworld breach",

    # ----- Green -----
    "gaea's cradle",
    "natural order",
    "survival of the fittest",

    # ----- Multicolor / Colorless / Lands -----
    "coalition victory",
    "field of the dead",
    "glacial chasm",
    "jeweled lotus",
    "mana vault",
    "the one ring",
    "the tabernacle at pendrell vale",

    # Note: Sol Ring is NOT on the RC's Game Changer list. Mox Diamond,
    # Mox Opal, Lion's Eye Diamond are debatable — left OFF for now.
    # Crucible of Worlds was discussed but is not currently on the list.
})


def is_game_changer(card_name: str | None) -> bool:
    """Return True when the card name appears on the curated Game Changers list."""
    if not card_name:
        return False
    return card_name.strip().lower() in GAME_CHANGERS


def count_game_changers(card_names: Iterable[str]) -> int:
    """Count distinct Game Changer cards in an iterable of card names."""
    seen: set[str] = set()
    for name in card_names or []:
        norm = (name or "").strip().lower()
        if norm and norm in GAME_CHANGERS and norm not in seen:
            seen.add(norm)
    return len(seen)


def game_changer_status(
    count: int,
    limit: int | None,
) -> tuple[str, str]:
    """Return (status_code, human_message) given a count + bracket limit.

    status_code is one of:
      'ok'         - count <= limit (or limit is None = unlimited)
      'over_limit' - count > limit
      'no_bracket' - limit is None and no bracket selected

    The human message is suitable for the Build Validation report.
    """
    if limit is None:
        if count == 0:
            return "ok", "0 Game Changers in deck (bracket allows unlimited)."
        return "ok", (
            f"{count} Game Changer(s) in deck (bracket allows unlimited; "
            f"still disclose in pregame)."
        )
    if count <= limit:
        return "ok", (
            f"{count} Game Changer(s) in deck (bracket allows up to {limit})."
        )
    over_by = count - limit
    return "over_limit", (
        f"❌ {count} Game Changer(s) in deck but bracket allows only {limit} "
        f"(over by {over_by}). Consider cutting {over_by} or moving to a "
        f"higher bracket."
    )


def list_game_changers_in_deck(card_names: Iterable[str]) -> list[str]:
    """Return the canonical-form names of Game Changers found in the deck.

    Used by the report to show the user which specific cards are tripping
    the count.
    """
    found: list[str] = []
    seen: set[str] = set()
    for name in card_names or []:
        norm = (name or "").strip().lower()
        if norm in GAME_CHANGERS and norm not in seen:
            seen.add(norm)
            # Preserve the original (canonical) name from the deck list.
            found.append(name.strip())
    found.sort()
    return found
