"""Bracket-aware card filtering for Bin B deck building (v1.6.1 Phase 5).

The Build Setup Panel captures the user's bracket preference (1-5). This
module is the runtime filter the deck builder calls per card; it gives a
"include in pool?" yes/no answer (hard filter) and a soft score modifier so
high-bracket preferences nudge the selection order.

v1.6.1 Phase 5 moved the bracket POLICY DATA out of this file into
`rules/bracket_definitions.py`. That module is now the single source of
truth — when the Commander bracket guidance changes (which it has been
doing every 6-12 months since 2024), update `rules/bracket_definitions.py`
and `rules/bracket_rules.md` together. This file just consumes the data.

The role tags (`bracket_pressure`, `high_bracket_pressure`, `fast_mana`,
`free_interaction`, `efficient_tutor`, `ritual`, `combo_protection`,
`combo_piece_possible`, `win_condition`) come from
`analysis/role_tags.py` — this module reads them but does not own them.

Boundaries:
- This is a deck-building filter only.
- It does NOT change the main deck report's analysis behavior.
- It does NOT add new tags to cards.
- "Bracket 0" / "Not Sure Yet" means no filtering (all cards pass, no score nudge).
- Banned cards are NOT filtered here. The Phase-1 legality gate in
  `legality/build_legality_gate.py` already excluded them BEFORE this filter
  runs, so by the time a card reaches `is_card_allowed_in_bracket` it is
  guaranteed legal in Commander. The custom-mode `allow_banned_cards` flag
  is the only path that bypasses that gate.
"""
from __future__ import annotations

from typing import Iterable

from rules.bracket_definitions import (
    PRECON_FRIENDLY_EXEMPTIONS,
    filter_summary_for_bracket,
    get_bracket_definition,
    is_card_blocked_by_tag_combos,
    is_card_blocked_by_tag_pairs,
    is_precon_friendly_exemption,
    tags_soft_modifier,
    bracket_number_from_label,
)


def bracket_to_int(bracket_label: str | None) -> int:
    """Parse the bracket label to a 1-5 number, or 0 if unset / not-sure.

    Delegates to `rules.bracket_definitions._bracket_number_from_label` so
    label parsing lives in one place.
    """
    return bracket_number_from_label(bracket_label)


def is_card_allowed_in_bracket(
    card_tags: Iterable[str],
    card_name: str,
    bracket_label: str | None,
) -> bool:
    """Hard filter — return False if the card is excluded at the chosen bracket.

    Reads the policy from `rules/bracket_definitions.py`. Three checks per card:

    1. Single-tag hard exclusions (e.g., `high_bracket_pressure` at B2).
    2. Precon-friendly name exemption — if the bracket applies it (B2 only)
       AND the card name is on the exemption list, the card passes regardless
       of single-tag exclusions.
    3. AND-grouped tag exclusions:
       - `tag_combinations_hard_excluded` — e.g., `combo_piece_possible +
         win_condition` at B2.
       - `tag_pair_hard_excluded` — e.g., `ritual + fast_mana` at B2.

    "Bracket 0" (Not Sure Yet) means everything passes.
    """
    bracket = get_bracket_definition(bracket_label)
    if bracket is None:
        return True  # No bracket selected → no filtering.

    tags = frozenset(card_tags or ())

    # 1. Single-tag hard exclusions.
    has_blocked_tag = bool(tags & bracket.tags_hard_excluded)

    # 2. Precon-friendly name exemption — overrides single-tag block at B2.
    if has_blocked_tag and bracket.apply_precon_friendly_exemptions:
        if is_precon_friendly_exemption(card_name):
            has_blocked_tag = False
    if has_blocked_tag:
        return False

    # 3. AND-grouped exclusions (tag combinations and tag pairs).
    if is_card_blocked_by_tag_combos(bracket, tags):
        return False
    if is_card_blocked_by_tag_pairs(bracket, tags):
        return False

    return True


def score_modifier_for_bracket(
    card_tags: Iterable[str],
    bracket_label: str | None,
) -> float:
    """Soft score modifier applied to a card's selection priority by bracket.

    Reads the per-tag penalty / boost values from `rules/bracket_definitions.py`.
    Returns 0.0 at lower brackets (their hard filter already handled it),
    a negative penalty at B3 (lets pressure cards slip in but late), and a
    positive boost at B4/B5.
    """
    return tags_soft_modifier(bracket_label, frozenset(card_tags or ()))


def bracket_filter_summary(bracket_label: str | None) -> str:
    """Human-readable line describing what filtering will apply for the bracket."""
    return filter_summary_for_bracket(bracket_label)
