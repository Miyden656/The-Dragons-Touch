"""Bracket-aware card filtering for Bin B deck building (v1.5.40).

The Build Setup Panel captures the user's bracket preference (1-5). Previously
the deck builder ignored it — Bracket 1 and Bracket 5 produced identically-shaped
decks from a given collection. This module fixes that by:

1. **Hard filter** — `is_card_allowed_in_bracket()` rejects cards that simply
   shouldn't appear at the chosen bracket (no Game Changers in B1, no fast mana
   beyond Sol Ring at B1, etc.). Filtered cards never enter the pool.

2. **Soft score modifier** — `score_modifier_for_bracket()` nudges card scores
   up or down based on bracket. At B5 (cEDH), fast mana / free interaction /
   efficient tutors get a score boost so they're preferred. At B3, they pass
   the hard filter but are slightly deprioritized.

The role tags `bracket_pressure`, `high_bracket_pressure`, `fast_mana`,
`free_interaction`, `efficient_tutor`, `ritual`, `combo_protection`,
`combo_piece_possible`, and `win_condition` come from
`analysis/role_tags.py` — this module reads them but does not own them.

Boundaries:
- This is a deck-building filter only.
- It does NOT change the main deck report's analysis behavior.
- It does NOT add new tags to cards.
- Bracket "Not Sure Yet" means no filtering (all cards pass).
"""
from __future__ import annotations

from typing import Iterable


# Card names that are precon-friendly even though their role tags would
# otherwise flag them as bracket pressure. These pass the B2 filter so a
# precon-style deck can still include them.
PRECON_FRIENDLY_EXEMPTIONS: frozenset[str] = frozenset({
    "sol ring",
    "arcane signet",
    "command tower",
    "exotic orchard",
    "fellwar stone",
    "mind stone",
    "thought vessel",
    "commander's sphere",
    "cultivate",
    "kodama's reach",
    "rampant growth",
    "swords to plowshares",
    "path to exile",
    "counterspell",
    "go for the throat",
    "generous gift",
    "beast within",
})


def bracket_to_int(bracket_label: str | None) -> int:
    """Parse the bracket label to a 1-5 number, or 0 if unset / not-sure.

    Accepts the labels emitted by build_from_collection.philosophy_bracket_preferences:
        "Not Sure Yet"
        "Bracket 1 — Low Power / Precon-Friendly"
        "Bracket 2 — Casual Upgraded"
        "Bracket 3 — Strong Casual"
        "Bracket 4 — High Power"
        "Bracket 5 — cEDH / Competitive"
    """
    if not bracket_label:
        return 0
    text = str(bracket_label).lower()
    if "not sure" in text or "not selected" in text:
        return 0
    for n in (1, 2, 3, 4, 5):
        if f"bracket {n}" in text:
            return n
    return 0


def is_card_allowed_in_bracket(
    card_tags: Iterable[str],
    card_name: str,
    bracket_label: str | None,
) -> bool:
    """Hard filter: return False if the card is banned at the chosen bracket.

    Bracket 1 — Low Power / Precon-Friendly:
        Rejects every `bracket_pressure` and `high_bracket_pressure` tag.
        (Even Sol Ring / Arcane Signet, which is the precon-friendly definition.)

    Bracket 2 — Casual Upgraded:
        Allows precon-friendly cards by name exemption (Sol Ring etc.).
        Rejects free_interaction, efficient_tutor, combo_protection,
        and "you win the game" combo enablers.

    Bracket 3 — Strong Casual:
        Allows everything. Soft penalty applied via score_modifier_for_bracket.

    Bracket 4 — High Power and Bracket 5 — cEDH:
        Allows everything.

    Bracket 0 — "Not Sure Yet":
        Allows everything (no filtering).
    """
    bracket_num = bracket_to_int(bracket_label)
    if bracket_num <= 0:
        return True  # No bracket chosen → no filtering.

    tags = set(card_tags or ())
    name_lc = (card_name or "").lower()

    if bracket_num == 1:
        # Strict: no pressure cards at all.
        if "bracket_pressure" in tags or "high_bracket_pressure" in tags:
            return False
        if "fast_mana" in tags or "ritual" in tags:
            return False
        if "efficient_tutor" in tags or "free_interaction" in tags:
            return False
        if "combo_protection" in tags:
            return False
        return True

    if bracket_num == 2:
        # Allow precon-friendly cards by name even if their tags say pressure.
        if name_lc in PRECON_FRIENDLY_EXEMPTIONS:
            return True
        # Exclude high pressure and the obvious upgrade-bracket pieces.
        if "high_bracket_pressure" in tags:
            return False
        if "free_interaction" in tags:
            return False
        if "efficient_tutor" in tags:
            return False
        if "combo_protection" in tags:
            return False
        if "ritual" in tags and "fast_mana" in tags:
            return False
        # Cards that "win the game" outright via combo: also exclude at B2.
        if "combo_piece_possible" in tags and "win_condition" in tags:
            return False
        return True

    # B3 / B4 / B5: no hard exclusion — use the score modifier.
    return True


def score_modifier_for_bracket(
    card_tags: Iterable[str],
    bracket_label: str | None,
) -> float:
    """Soft score modifier applied to a card's selection priority by bracket.

    Returns 0.0 at lower brackets (their hard filter already handled it),
    a small penalty at B3 (lets pressure cards slip in but late),
    a mild boost at B4, and a strong boost at B5 (cEDH preference for
    fast mana, free interaction, efficient tutors, rituals).
    """
    bracket_num = bracket_to_int(bracket_label)
    if bracket_num <= 0:
        return 0.0

    tags = set(card_tags or ())

    if bracket_num == 1 or bracket_num == 2:
        # Hard filter already removed problem cards; nothing left to nudge.
        return 0.0

    if bracket_num == 3:
        # Allow pressure but soft-penalize so non-pressure picks win ties.
        penalty = 0.0
        if "high_bracket_pressure" in tags:
            penalty -= 3.0
        if "free_interaction" in tags:
            penalty -= 1.5
        if "efficient_tutor" in tags:
            penalty -= 1.5
        if "combo_protection" in tags:
            penalty -= 1.0
        return penalty

    if bracket_num == 4:
        # Mild boost for efficient pieces; competitive players want them.
        boost = 0.0
        if "bracket_pressure" in tags:
            boost += 0.5
        if "high_bracket_pressure" in tags:
            boost += 1.0
        return boost

    if bracket_num == 5:
        # cEDH: strongly prefer fast mana / free counterspells / efficient tutors.
        boost = 0.0
        if "fast_mana" in tags:
            boost += 2.5
        if "ritual" in tags:
            boost += 1.5
        if "free_interaction" in tags:
            boost += 2.5
        if "efficient_tutor" in tags:
            boost += 2.0
        if "combo_protection" in tags:
            boost += 1.5
        if "high_bracket_pressure" in tags:
            boost += 1.5
        if "bracket_pressure" in tags:
            boost += 0.5
        return boost

    return 0.0


def bracket_filter_summary(bracket_label: str | None) -> str:
    """Human-readable line describing what filtering will apply for the bracket."""
    n = bracket_to_int(bracket_label)
    if n == 0:
        return "No bracket filter applied — all collection cards eligible."
    if n == 1:
        return (
            "Bracket 1 filter: excluded fast mana, rituals, efficient tutors, "
            "free interaction, and combo-protection cards. Precon-style power level."
        )
    if n == 2:
        return (
            "Bracket 2 filter: precon-friendly exemptions kept (Sol Ring etc.), "
            "but free interaction, efficient tutors, combo-protection, and "
            "double-ritual fast mana were excluded."
        )
    if n == 3:
        return (
            "Bracket 3: no hard filter, but bracket-pressure cards "
            "(free counters, efficient tutors, Game Changers) were deprioritized "
            "in card scoring."
        )
    if n == 4:
        return "Bracket 4: all cards allowed; mild boost for efficient pieces."
    if n == 5:
        return (
            "Bracket 5 (cEDH): strongly preferred fast mana, free interaction, "
            "efficient tutors, and rituals."
        )
    return "No bracket filter applied."
