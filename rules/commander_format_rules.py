"""Commander format rules — runtime-consumable rule data (v1.6.1 Phase 6).

WHY THIS FILE EXISTS
--------------------
Commander deck construction has a small but important set of format-defining
rules — deck size, the singleton rule, the basic-land exception, color
identity, which card types are legal at all, which special command-zone
texts grant commander legality. Before v1.6.1 these were scattered across
`legality/commander_legality.py`, `commander_discovery/eligibility.py`,
`legality/companion_rules.py`, plus inline string-checks in the UI layer.
When the rules change (Doctor's Companion, Friends Forever, new Background
mechanics, Universes Beyond reprints), there was no single place to update.

This module is the single source of truth for the deck-construction rules.
The runtime modules import constants and helpers from here; the .md files
in this directory are the prose companions explaining the WHY in plain
language. Update both together when the rules change.

WHAT THIS MODULE COVERS
-----------------------
- Deck size (100 cards) and what counts toward it
- Singleton rule + basic-land exception + "any number of cards named X" exception
- Color identity definition
- Command-zone rules:
    * Basic legendary creature
    * Planeswalker that says "can be your commander"
    * Partner / Partner with X
    * Background / Choose a Background
    * Friends Forever
    * Doctor's Companion / The Doctor
- Format-disallowed card types (Conspiracy / Phenomenon / Plane / Scheme /
  Vanguard) — Scryfall already marks these legalities.commander=not_legal,
  but the names are listed here for documentation + dev-mode warnings
- Silver-border / acorn / un-cards (`border_color="silver"`) — same handling
- Companion is NOT a commander (it's a sideboard/wishboard concept) — flagged
  for manual review by the eligibility layer

WHAT THIS MODULE DOES NOT COVER
-------------------------------
- The banned list itself. That's `legality/build_legality_gate.py` reading
  Scryfall's `legalities.commander` field. We don't hard-code names here.
- Full partner-pairing validation. Detection is here; pair-validity logic
  stays in `legality/commander_legality.py`.
- Companion deck-building restrictions (Jegantha can-only-use-mana etc.).
  That's `legality/companion_rules.py`.
- The bracket policy — that's `rules/bracket_definitions.py`.

PUBLIC API
----------
Constants:
    COMMANDER_DECK_SIZE                    : int = 100
    SINGLETON_RULE                         : str (human-readable description)
    SINGLETON_EXEMPT_TYPES                 : tuple of type-line substrings
    COMMAND_ZONE_RULE_*                    : str rule identifiers
    COMMAND_ZONE_RULE_TEXT_PATTERNS        : dict[rule_id, list[str]]
    FORMAT_DISALLOWED_TYPES                : tuple of disallowed type-line substrings
    FORMAT_DISALLOWED_BORDER_COLORS        : tuple
    FORMAT_DISALLOWED_FRAME_EFFECTS        : tuple

Helpers:
    is_commander_deck_size_legal(deck_size) -> bool
    is_basic_land_singleton_exempt(card)    -> bool
    detect_command_zone_rules(card)         -> list[str]
    is_partner(card)                        -> bool
    is_partner_with(card)                   -> tuple[bool, str | None]
    is_background_card(card)                -> bool
    is_choose_a_background_commander(card)  -> bool
    is_friends_forever(card)                -> bool
    is_doctors_companion(card)              -> bool
    is_the_doctor(card)                     -> bool
    is_planeswalker_commander(card)         -> bool
    is_format_disallowed_card(card)         -> tuple[bool, str]
    is_silver_border_or_acorn(card)         -> bool
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Deck construction
# ---------------------------------------------------------------------------

COMMANDER_DECK_SIZE: int = 100
"""A legal Commander deck contains exactly 100 cards including the commander(s).

For partner / background / Friends Forever / Doctor's Companion pairings,
both pieces still count toward the 100 — you have one commander partnership
that occupies 2 of the 100 slots. The remaining 98 cards form the 99.
"""

COMMANDER_DECK_SIZE_INCLUDES_COMMANDER: bool = True

SINGLETON_RULE: str = (
    "A Commander deck may include no more than one copy of any card with a "
    "given English name, except basic lands and cards whose oracle text "
    "explicitly says 'a deck can have any number of cards named ...' or "
    "'a deck can have up to N cards named ...'."
)


SINGLETON_EXEMPT_TYPES: tuple[str, ...] = (
    "Basic Land",
    "Basic Snow Land",
    # Note: "Basic" alone catches both Basic Land and Basic Snow Land; the
    # tuple here is the human-readable list. The detector below substring-matches
    # "Basic" + "Land" on the type line.
)


# ---------------------------------------------------------------------------
# Color identity
# ---------------------------------------------------------------------------

COLOR_IDENTITY_RULE: str = (
    "A card's color identity is its colors plus the colors of any mana "
    "symbols in its rules text and mana cost. Hybrid and Phyrexian mana "
    "symbols count as both/all relevant colors. A card may only appear in "
    "a Commander deck whose commander's combined color identity contains "
    "every color in the card's color identity. Colorless cards (color "
    "identity = {}) are legal in every deck. The five colors are W, U, B, "
    "R, G."
)


# ---------------------------------------------------------------------------
# Command-zone rules — which cards may serve as commanders
# ---------------------------------------------------------------------------

COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE = "basic_legendary_creature"
"""Any Legendary Creature is a legal commander by default."""

COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER = "planeswalker_commander"
"""A Planeswalker whose rules text explicitly says it can be your commander.
Examples: Daretti, Scrap Savant (Commander version); the original five
planeswalkers from CMR; etc.
"""

COMMAND_ZONE_RULE_PARTNER = "partner"
"""Two legendary creatures with the keyword Partner may share the command zone.
Either may pair with any other generic Partner."""

COMMAND_ZONE_RULE_PARTNER_WITH = "partner_with"
"""A legendary creature with 'Partner with [Name]' may only pair with that
specific named partner."""

COMMAND_ZONE_RULE_BACKGROUND = "background"
"""A Background is an enchantment that pairs with a legendary creature that has
'Choose a Background'."""

COMMAND_ZONE_RULE_CHOOSE_BACKGROUND = "choose_a_background"
"""A legendary creature with 'Choose a Background' may pair with any Background."""

COMMAND_ZONE_RULE_FRIENDS_FOREVER = "friends_forever"
"""Two legendary creatures with Friends Forever may share the command zone."""

COMMAND_ZONE_RULE_DOCTORS_COMPANION = "doctors_companion"
"""A legendary creature with Doctor's Companion may pair with a card with the
'Time Lord Doctor' or 'Doctor' creature type. (Distinct from the Modern
Horizons companion rule.)"""

COMMAND_ZONE_RULE_DOCTOR = "doctor"
"""A creature with the Doctor / Time Lord Doctor subtype that may be the
'Doctor' half of a Doctor's Companion pair."""


COMMAND_ZONE_RULE_TEXT_PATTERNS: dict[str, tuple[str, ...]] = {
    # Lower-cased substring patterns the eligibility scanner looks for in
    # combined oracle/type text. Patterns are intentionally tight to avoid
    # false positives from cards that merely mention these words.
    COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER: (
        "can be your commander",
    ),
    COMMAND_ZONE_RULE_PARTNER: (
        "partner",
    ),
    COMMAND_ZONE_RULE_PARTNER_WITH: (
        "partner with",
    ),
    COMMAND_ZONE_RULE_CHOOSE_BACKGROUND: (
        "choose a background",
    ),
    COMMAND_ZONE_RULE_FRIENDS_FOREVER: (
        "friends forever",
    ),
    COMMAND_ZONE_RULE_DOCTORS_COMPANION: (
        "doctor's companion",
        "doctors companion",  # apostrophe-stripped variant
    ),
}


# ---------------------------------------------------------------------------
# Format-disallowed cards
# ---------------------------------------------------------------------------

FORMAT_DISALLOWED_TYPES: tuple[str, ...] = (
    "Conspiracy",
    "Phenomenon",
    "Plane",
    "Scheme",
    "Vanguard",
    "Card",  # "Card" type appears on outside-the-game items; never main deck.
    "Hero",  # Hero cards (Theros challenge decks) are not Commander legal.
    "Stickers",  # Sticker sheets are sideboard-only in Unfinity legal play.
    "Attraction",  # Attractions need a separate Attraction deck mechanic.
    "Contraption",  # Unstable Contraptions are not Commander legal.
    "Dungeon",  # Dungeons are not deck cards; they're tracked-state objects.
)


FORMAT_DISALLOWED_BORDER_COLORS: tuple[str, ...] = (
    "silver",  # silver-border un-cards
    # Note: "borderless" and "gold" are cosmetic frames on legal cards,
    # not separate legality categories. Only "silver" is the un-card marker.
)


FORMAT_DISALLOWED_FRAME_EFFECTS: tuple[str, ...] = (
    # Most un-set / acorn cards now use the standard "etched" frame and rely
    # on Scryfall's legalities.commander="not_legal" — the border-color check
    # above remains the most reliable signal.
)


# ---------------------------------------------------------------------------
# Companion rule (sideboard concept, NOT a commander)
# ---------------------------------------------------------------------------

COMPANION_IS_NOT_A_COMMANDER: bool = True
"""The 'Companion' mechanic from Ikoria refers to a sideboard/wishboard slot.
In Commander it's used informally: a card with Companion can be played FROM
the command zone if you pay {3}. The card is still the deck's COMMANDER only
if it is a Legendary Creature (most Companions are). The Companion KEYWORD
itself does not grant command-zone legality. Eligibility for a Companion-
named legendary creature follows the Basic Legendary Creature rule.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _combined_text(card: dict[str, Any] | None) -> str:
    """Lower-case combined oracle + type text from card + faces."""
    if not isinstance(card, dict):
        return ""
    parts: list[str] = []
    if card.get("oracle_text"):
        parts.append(str(card.get("oracle_text") or ""))
    if card.get("type_line"):
        parts.append(str(card.get("type_line") or ""))
    for face in card.get("card_faces", []) or []:
        if not isinstance(face, dict):
            continue
        for key in ("oracle_text", "type_line"):
            if face.get(key):
                parts.append(str(face.get(key) or ""))
    return " ".join(" ".join(parts).replace("\n", " ").split()).lower()


def _all_type_lines(card: dict[str, Any] | None) -> list[str]:
    if not isinstance(card, dict):
        return []
    lines: list[str] = []
    if card.get("type_line"):
        lines.append(str(card.get("type_line") or ""))
    for face in card.get("card_faces", []) or []:
        if isinstance(face, dict) and face.get("type_line"):
            lines.append(str(face.get("type_line") or ""))
    return lines


def is_commander_deck_size_legal(deck_size: int) -> bool:
    """True when the deck has exactly 100 cards."""
    return int(deck_size) == COMMANDER_DECK_SIZE


def is_basic_land_singleton_exempt(card: dict[str, Any] | None) -> bool:
    """True if the card is a Basic Land — allowed in any quantity."""
    for tl in _all_type_lines(card):
        if "Basic" in tl and "Land" in tl:
            return True
    return False


def detect_command_zone_rules(card: dict[str, Any] | None) -> list[str]:
    """Return the list of command-zone rules detected on this card.

    A single card can carry multiple rules: e.g., Tymna the Weaver has
    `basic_legendary_creature` + `partner`. A Background-cmdr-pair card
    has both `choose_a_background` + `basic_legendary_creature`. The list
    order follows the COMMAND_ZONE_RULE_* constant order above.
    """
    if not isinstance(card, dict):
        return []

    rules: list[str] = []
    text = _combined_text(card)
    type_text = " ".join(_all_type_lines(card)).lower()

    if "legendary creature" in type_text:
        rules.append(COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE)
    if "planeswalker" in type_text and any(
        p in text for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER]
    ):
        rules.append(COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER)
    # "partner with" must be tested BEFORE generic "partner" because the
    # generic-partner detector also matches "partner with".
    if any(p in text for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_PARTNER_WITH]):
        rules.append(COMMAND_ZONE_RULE_PARTNER_WITH)
    elif any(p in text for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_PARTNER]):
        # Bare "partner" keyword without "partner with [Name]".
        rules.append(COMMAND_ZONE_RULE_PARTNER)
    # Background subtype on the type line.
    if "background" in type_text:
        rules.append(COMMAND_ZONE_RULE_BACKGROUND)
    if any(p in text for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_CHOOSE_BACKGROUND]):
        rules.append(COMMAND_ZONE_RULE_CHOOSE_BACKGROUND)
    if any(p in text for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_FRIENDS_FOREVER]):
        rules.append(COMMAND_ZONE_RULE_FRIENDS_FOREVER)
    if any(p in text for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_DOCTORS_COMPANION]):
        rules.append(COMMAND_ZONE_RULE_DOCTORS_COMPANION)
    if "time lord doctor" in type_text or "— doctor" in type_text:
        rules.append(COMMAND_ZONE_RULE_DOCTOR)
    return rules


def is_partner(card: dict[str, Any] | None) -> bool:
    """True if the card has the bare Partner keyword (not 'Partner with X')."""
    rules = detect_command_zone_rules(card)
    return COMMAND_ZONE_RULE_PARTNER in rules


def is_partner_with(card: dict[str, Any] | None) -> tuple[bool, str | None]:
    """Return (True, partner_name) if the card has 'Partner with <Name>'."""
    if not isinstance(card, dict):
        return False, None
    text = _combined_text(card)
    if "partner with" not in text:
        return False, None
    # Best-effort partner-with name extraction. "Partner with <Name>" usually
    # appears as a keyword block — we return the snippet up to the next period.
    idx = text.find("partner with")
    if idx < 0:
        return True, None
    snippet = text[idx + len("partner with"):].strip()
    # Cut at the first sentence/clause boundary.
    for boundary in (".", "\n", "(", "—"):
        cut = snippet.find(boundary)
        if cut >= 0:
            snippet = snippet[:cut].strip()
    return True, snippet or None


def is_background_card(card: dict[str, Any] | None) -> bool:
    """True if the card is a Background enchantment (the partner half)."""
    type_text = " ".join(_all_type_lines(card)).lower()
    return "background" in type_text


def is_choose_a_background_commander(card: dict[str, Any] | None) -> bool:
    """True if the card has 'Choose a Background' text (the commander half)."""
    text = _combined_text(card)
    return "choose a background" in text


def is_friends_forever(card: dict[str, Any] | None) -> bool:
    """True if the card has the Friends Forever keyword."""
    text = _combined_text(card)
    return "friends forever" in text


def is_doctors_companion(card: dict[str, Any] | None) -> bool:
    """True if the card has Doctor's Companion."""
    text = _combined_text(card)
    return any(
        p in text
        for p in COMMAND_ZONE_RULE_TEXT_PATTERNS[COMMAND_ZONE_RULE_DOCTORS_COMPANION]
    )


def is_the_doctor(card: dict[str, Any] | None) -> bool:
    """True if the card has the Doctor / Time Lord Doctor creature subtype."""
    type_text = " ".join(_all_type_lines(card)).lower()
    return "time lord doctor" in type_text or "— doctor" in type_text


def is_planeswalker_commander(card: dict[str, Any] | None) -> bool:
    """True if the card is a Planeswalker that says 'can be your commander'."""
    rules = detect_command_zone_rules(card)
    return COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER in rules


def is_format_disallowed_card(card: dict[str, Any] | None) -> tuple[bool, str]:
    """Return (True, reason) if the card is a format-disallowed type.

    Scryfall already marks these `legalities.commander = "not_legal"`, so the
    Phase 1 legality gate handles them at the build path. This helper is for
    documentation and for tools that want to explain WHY a card was excluded
    (e.g., "this is a Conspiracy — sideboard cards only, not main deck").
    """
    if not isinstance(card, dict):
        return False, ""
    for tl in _all_type_lines(card):
        for disallowed in FORMAT_DISALLOWED_TYPES:
            if disallowed in tl:
                return True, (
                    f"Card has type '{disallowed}' which is not legal in main "
                    f"Commander deck construction."
                )
    return False, ""


def is_silver_border_or_acorn(card: dict[str, Any] | None) -> bool:
    """True if Scryfall marks this as a silver-border / un-card.

    These are joke cards (Unhinged, Unglued, Unfinity acorn). They're not
    legal in Commander; Scryfall's legalities.commander already says
    not_legal. This is a documentation helper for tools that want to label
    WHY the card was filtered.
    """
    if not isinstance(card, dict):
        return False
    border = str(card.get("border_color") or "").strip().lower()
    return border in FORMAT_DISALLOWED_BORDER_COLORS


def is_companion_card(card: dict[str, Any] | None) -> bool:
    """True if the card has the Companion mechanic.

    Note: COMPANION IS NOT A COMMANDER. A Companion card may also be a
    Legendary Creature (and so be a legal commander via the basic rule),
    but the Companion keyword itself does NOT grant commander legality.
    Detect-only helper for reports / warnings.
    """
    text = _combined_text(card)
    return "companion" in text and "companion's leash" not in text
