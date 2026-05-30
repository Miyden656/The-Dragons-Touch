"""Single-card Commander legality gate for the Build-From-Collection path (v1.6.1).

WHY THIS FILE EXISTS
--------------------
Before v1.6.1, the build-from-collection deck builder (full_100_card_draft_builder.py)
only filtered owned cards by color identity and bracket-pressure tags. It NEVER
consulted Scryfall's `legalities.commander` field, which meant a Commander-banned
card (Channel, Recurring Nightmare, Mana Crypt after 2024, etc.) sitting in the
user's collection would land in the generated deck at any bracket.

The deck-review path (legality/commander_legality.py:check_banned_cards) already
knew how to do this — but it operates on a fully-parsed deck, not on a candidate
pool. This module exposes the same legality knowledge as a per-card gate so the
builder can reject banned cards BEFORE they enter the candidate pool.

This module does NOT:
- Re-check the whole deck (that's commander_legality.build_commander_legality_summary).
- Decide bracket fit (that's build_from_collection/bracket_filter.py).
- Decide color identity (that's the builder's own subset check).
- Look at card name strings — it reads structured Scryfall `legalities` only.

Scryfall `legalities.commander` values seen in practice:
    "legal"       — playable in 99
    "not_legal"   — not legal at all (un-cards, conspiracies, schemes, planes,
                    phenomena, vanguards, dexterity cards, attractions if they
                    appear, etc.)
    "banned"      — explicitly banned by the Commander rules committee
    "restricted" — not a Commander concept (Vintage-only) but treated as
                    not-allowed here for safety
    "unknown" / missing — Scryfall data is incomplete; we treat as legal but
                    flag for manual review.

Custom playgroup mode:
    The build path accepts `allow_banned_cards=False` by default. Setting it to
    True lets banned cards through (Rule Zero / house-rules tables). It does NOT
    let "not_legal" cards through — those are functionally not Magic cards in
    a Commander context (no rules text, joke text, requires physical dexterity,
    etc.) and including them would break the deck anyway.
"""
from __future__ import annotations

from typing import Any


# Scryfall legality string values we care about.
LEGALITY_LEGAL = "legal"
LEGALITY_NOT_LEGAL = "not_legal"
LEGALITY_BANNED = "banned"
LEGALITY_RESTRICTED = "restricted"  # Not a Commander value but handled defensively.
LEGALITY_UNKNOWN = "unknown"


# Exclusion reason codes returned by should_exclude_from_commander_build().
# Used by the builder to bucket counters and surface them in the report.
EXCLUDE_REASON_BANNED = "banned"
EXCLUDE_REASON_NOT_LEGAL = "not_legal"
EXCLUDE_REASON_RESTRICTED = "restricted"


def get_commander_legality(card: dict[str, Any] | None) -> str:
    """Return the Scryfall `legalities.commander` value for a card.

    Returns "unknown" when the field is missing — caller decides how to treat that.
    Never raises.
    """
    if not isinstance(card, dict):
        return LEGALITY_UNKNOWN
    legalities = card.get("legalities")
    if not isinstance(legalities, dict):
        return LEGALITY_UNKNOWN
    value = legalities.get("commander")
    if not isinstance(value, str) or not value.strip():
        return LEGALITY_UNKNOWN
    return value.strip().lower()


def is_card_banned_in_commander(card: dict[str, Any] | None) -> bool:
    """True if the card is explicitly banned by the Commander rules committee."""
    return get_commander_legality(card) == LEGALITY_BANNED


def is_card_not_legal_in_commander(card: dict[str, Any] | None) -> bool:
    """True if the card is not a legal Magic card in a Commander context.

    Covers un-cards (silver-border / acorn), conspiracies, schemes, planes,
    phenomena, vanguards, attractions, dexterity cards, contraptions — anything
    Scryfall labels `not_legal` in Commander. These should never appear in a
    Commander deck regardless of house rules.
    """
    return get_commander_legality(card) == LEGALITY_NOT_LEGAL


def is_card_legal_in_commander(card: dict[str, Any] | None) -> bool:
    """True only when Scryfall explicitly says the card is legal in Commander."""
    return get_commander_legality(card) == LEGALITY_LEGAL


def should_exclude_from_commander_build(
    card: dict[str, Any] | None,
    *,
    allow_banned_cards: bool = False,
) -> tuple[bool, str]:
    """Decide whether a single card should be excluded from a normal Commander build.

    Returns (excluded, reason_code) where reason_code is one of:
        ""                  — not excluded
        "banned"             — excluded because Commander-banned
        "not_legal"          — excluded because not legal in Commander at all
        "restricted"         — excluded defensively (rare; Vintage-style data)

    Behavior:
        - "legal" -> not excluded.
        - "banned" -> excluded UNLESS `allow_banned_cards` is True (custom mode).
        - "not_legal" -> always excluded, even in custom mode.
        - "restricted" -> always excluded (defensive; Commander doesn't use
          restricted, but if Scryfall ever marks it we play safe).
        - "unknown" / missing -> NOT excluded. The legality module reports it
          as manual-review elsewhere; we don't drop owned cards on missing data.
    """
    status = get_commander_legality(card)

    if status == LEGALITY_LEGAL:
        return False, ""

    if status == LEGALITY_BANNED:
        if allow_banned_cards:
            return False, ""
        return True, EXCLUDE_REASON_BANNED

    if status == LEGALITY_NOT_LEGAL:
        return True, EXCLUDE_REASON_NOT_LEGAL

    if status == LEGALITY_RESTRICTED:
        return True, EXCLUDE_REASON_RESTRICTED

    # Unknown / missing — don't drop the card. Manual-review surfaces elsewhere.
    return False, ""


def commander_legality_gate_summary(
    *,
    banned_excluded: int,
    not_legal_excluded: int,
    restricted_excluded: int = 0,
    allow_banned_cards: bool = False,
) -> str:
    """One-line human summary of what the legality gate did this build.

    Used by the builder to append to result.notes so the user can see at a
    glance whether the gate fired and how many cards were filtered.
    """
    parts: list[str] = []
    if allow_banned_cards:
        parts.append(
            "Legality gate: CUSTOM MODE — Commander-banned cards were ALLOWED. "
            "This deck does not pass standard Commander legality. Do not bring "
            "it to a normal Commander table without Rule Zero approval."
        )
    else:
        if banned_excluded == 0 and not_legal_excluded == 0 and restricted_excluded == 0:
            parts.append(
                "Legality gate: no Commander-banned or not-legal cards found in "
                "your collection for this commander."
            )
        else:
            chunks: list[str] = []
            if banned_excluded:
                chunks.append(f"{banned_excluded} Commander-banned")
            if not_legal_excluded:
                chunks.append(f"{not_legal_excluded} not-legal-in-Commander")
            if restricted_excluded:
                chunks.append(f"{restricted_excluded} restricted")
            parts.append(
                "Legality gate excluded "
                + ", ".join(chunks)
                + " card(s) from your collection before deck construction."
            )
    return " ".join(parts)
