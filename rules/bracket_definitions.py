"""Commander bracket definitions — runtime-consumable rule data (v1.6.1 Phase 5).

WHY THIS FILE EXISTS
--------------------
Before v1.6.1 the bracket policy was hard-coded in `if bracket_num == 1:` /
`elif bracket_num == 2:` chains inside `build_from_collection/bracket_filter.py`.
When the Commander bracket guidance changes (which it has been doing every
6-12 months since 2024), you had to find and patch each branch, hope you
caught them all, and keep the prose in `rules/bracket_rules.md` in sync.

This module is the single source of truth for what each bracket allows /
disallows / boosts / penalizes. The filter at `build_from_collection/
bracket_filter.py` reads from here. The `.md` file remains the human-readable
companion that explains the WHY in prose; this file is the WHAT the runtime
consumes.

When the bracket system changes:
  1. Update `BRACKETS` below (and add a test entry in
     `tests/test_bracket_definitions.py`).
  2. Update the corresponding prose in `rules/bracket_rules.md` so they don't
     drift apart.
  3. Run `py -3 tests/run_all.py` to confirm the filter still does the
     right thing.

PUBLIC API
----------
- `BRACKETS`: dict mapping bracket number (1-5) → BracketDefinition. Read-only.
- `get_bracket_definition(label_or_number)`: resolve a bracket label like
  "Bracket 2 — Casual Upgraded" or an int to its BracketDefinition. Returns
  None for "Not Sure Yet" / unrecognized.
- `tags_hard_excluded(label_or_number)`: set of role-tag names that must
  fail the bracket filter.
- `tags_soft_modifier(label_or_number, tags)`: cumulative soft score
  modifier from the bracket's penalize/boost tables.
- `is_precon_friendly_exemption(name)`: True if the card name is on the
  precon-friendly exemption list (used at B2 so Sol Ring / Arcane Signet
  remain legal despite the pressure tag).

POLICY MODEL
------------
Each `BracketDefinition` carries:
- Human-facing metadata: name, intent, expected_turns_before_win,
  game_changer_count_limit.
- `banned_cards_allowed = False` — always False at the bracket-filter layer.
  The custom-mode `allow_banned_cards` flag in the builder is the explicit
  Rule Zero opt-in; brackets themselves NEVER allow banned cards.
- `tags_hard_excluded`: any card whose role-tag set intersects this fails
  the bracket filter.
- `tags_soft_penalty`: each matching tag adds the listed (negative) score.
- `tags_soft_boost`: each matching tag adds the listed (positive) score.

Together these reproduce the v1.5.40 behavior the existing tests assert,
just driven by data instead of branches.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Cards that are precon-friendly even when their role tags flag them as
# bracket pressure. Used at B2 so the staple precon mana support remains
# legal at the upgraded-casual level. Kept lower-cased here.
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


@dataclass(frozen=True, slots=True)
class BracketDefinition:
    """Single bracket's complete runtime policy + human metadata.

    All policy fields default to empty / permissive so that adding a new
    bracket in the future doesn't require updating every existing field
    unless it actually differs.
    """

    number: int
    short_name: str
    full_label: str
    intent: str
    expected_turns_before_win: int | None
    game_changer_count_limit: int | None  # None = unlimited
    # Always False at the bracket-filter layer. The explicit
    # allow_banned_cards flag in the builder is the only path that may pass
    # banned cards, and that's a custom / Rule Zero escape hatch, not a
    # bracket allowance.
    banned_cards_allowed: bool = False
    # Tags that any matching card fails the bracket filter on.
    tags_hard_excluded: frozenset[str] = field(default_factory=frozenset)
    # Tags that ALL must be present on a card for it to fail (used for the
    # "combo_piece_possible + win_condition" B2 rule). Each tuple is an
    # AND-group; the card fails if its tags are a superset of ANY tuple.
    tag_combinations_hard_excluded: tuple[frozenset[str], ...] = field(default_factory=tuple)
    # Tag-pair AND groups that fail (e.g. ritual+fast_mana at B2).
    # If a card carries every tag in any tuple it fails.
    tag_pair_hard_excluded: tuple[frozenset[str], ...] = field(default_factory=tuple)
    # Per-tag soft penalty (negative score).
    tags_soft_penalty: dict[str, float] = field(default_factory=dict)
    # Per-tag soft boost (positive score).
    tags_soft_boost: dict[str, float] = field(default_factory=dict)
    # Apply the precon-friendly name exemption when filtering. True for B2.
    apply_precon_friendly_exemptions: bool = False
    # Short prose summary used in the markdown report.
    filter_summary: str = ""


# ---------------------------------------------------------------------------
# Bracket 1 — Exhibition / Low Power / Precon-friendly
# ---------------------------------------------------------------------------
BRACKET_1 = BracketDefinition(
    number=1,
    short_name="Exhibition / Low Power",
    full_label="Bracket 1 — Low Power / Precon-Friendly",
    intent=(
        "Highly thematic, expressive, ultra-casual decks. Theme over power. "
        "Win is not the primary goal. Long, low-pressure games expected."
    ),
    expected_turns_before_win=9,
    game_changer_count_limit=0,
    tags_hard_excluded=frozenset({
        "bracket_pressure",
        "high_bracket_pressure",
        "fast_mana",
        "ritual",
        "efficient_tutor",
        "free_interaction",
        "combo_protection",
    }),
    filter_summary=(
        "Bracket 1 filter: excluded fast mana, rituals, efficient tutors, "
        "free interaction, and combo-protection cards. Precon-style power level."
    ),
)


# ---------------------------------------------------------------------------
# Bracket 2 — Core / Casual Upgraded
# ---------------------------------------------------------------------------
BRACKET_2 = BracketDefinition(
    number=2,
    short_name="Core / Casual Upgraded",
    full_label="Bracket 2 — Casual Upgraded",
    intent=(
        "Low-pressure, social Commander decks that are functional but not "
        "heavily optimized. Coherent plans, telegraphed wins, considerate play."
    ),
    expected_turns_before_win=8,
    game_changer_count_limit=0,
    tags_hard_excluded=frozenset({
        "high_bracket_pressure",
        "free_interaction",
        "efficient_tutor",
        "combo_protection",
    }),
    # A card that says "you win the game" via combo (e.g., Thassa's Oracle
    # with an empty library) carries BOTH combo_piece_possible AND
    # win_condition. Either tag alone is allowed at B2; the pair isn't.
    tag_combinations_hard_excluded=(
        frozenset({"combo_piece_possible", "win_condition"}),
    ),
    # "Double-ritual" style fast mana (ritual+fast_mana on same card) fails B2;
    # plain fast_mana like Sol Ring (precon-friendly) passes the name exemption.
    tag_pair_hard_excluded=(
        frozenset({"ritual", "fast_mana"}),
    ),
    apply_precon_friendly_exemptions=True,
    filter_summary=(
        "Bracket 2 filter: precon-friendly exemptions kept (Sol Ring etc.), "
        "but free interaction, efficient tutors, combo-protection, and "
        "double-ritual fast mana were excluded."
    ),
)


# ---------------------------------------------------------------------------
# Bracket 3 — Upgraded / Strong Casual
# ---------------------------------------------------------------------------
BRACKET_3 = BracketDefinition(
    number=3,
    short_name="Upgraded / Strong Casual",
    full_label="Bracket 3 — Strong Casual",
    intent=(
        "Tuned casual Commander decks. Strong synergy, higher card quality, "
        "more interaction, some Game Changers (up to ~3), proactive and "
        "reactive gameplay, big turns from accrued resources."
    ),
    expected_turns_before_win=6,
    game_changer_count_limit=3,
    # B3 has no hard tag exclusions; bracket pressure is allowed but soft-
    # penalized so non-pressure picks win ties.
    tags_soft_penalty={
        "high_bracket_pressure": 3.0,
        "free_interaction": 1.5,
        "efficient_tutor": 1.5,
        "combo_protection": 1.0,
    },
    filter_summary=(
        "Bracket 3: no hard filter, but bracket-pressure cards "
        "(free counters, efficient tutors, Game Changers) were deprioritized "
        "in card scoring."
    ),
)


# ---------------------------------------------------------------------------
# Bracket 4 — Optimized / High Power
# ---------------------------------------------------------------------------
BRACKET_4 = BracketDefinition(
    number=4,
    short_name="Optimized / High Power",
    full_label="Bracket 4 — High Power",
    intent=(
        "High-powered Commander decks: fast, lethal, consistent, optimized. "
        "Many Game Changers, strong tutors, efficient combos, explosive "
        "starts. Not necessarily tuned to the cEDH metagame."
    ),
    expected_turns_before_win=4,
    game_changer_count_limit=None,  # unlimited
    tags_soft_boost={
        "bracket_pressure": 0.5,
        "high_bracket_pressure": 1.0,
    },
    filter_summary="Bracket 4: all cards allowed; mild boost for efficient pieces.",
)


# ---------------------------------------------------------------------------
# Bracket 5 — cEDH / Competitive
# ---------------------------------------------------------------------------
BRACKET_5 = BracketDefinition(
    number=5,
    short_name="cEDH / Competitive",
    full_label="Bracket 5 — cEDH / Competitive",
    intent=(
        "Competitive Commander. Built to win as efficiently as possible "
        "within the Commander banned list and the known cEDH metagame. "
        "Fast mana, dense interaction, free spells, efficient tutors, "
        "compact combo wins. Tight sequencing. Games may end any turn."
    ),
    expected_turns_before_win=None,
    game_changer_count_limit=None,  # unlimited
    tags_soft_boost={
        "fast_mana": 2.5,
        "ritual": 1.5,
        "free_interaction": 2.5,
        "efficient_tutor": 2.0,
        "combo_protection": 1.5,
        "high_bracket_pressure": 1.5,
        "bracket_pressure": 0.5,
    },
    filter_summary=(
        "Bracket 5 (cEDH): strongly preferred fast mana, free interaction, "
        "efficient tutors, and rituals."
    ),
)


BRACKETS: dict[int, BracketDefinition] = {
    1: BRACKET_1,
    2: BRACKET_2,
    3: BRACKET_3,
    4: BRACKET_4,
    5: BRACKET_5,
}


def bracket_number_from_label(label: str | int | None) -> int:
    """Coerce a bracket label or int to a 1..5 number, or 0 for unset.

    Accepts:
      - int 1..5
      - "Bracket 1 — Low Power / Precon-Friendly" / similar full labels
      - "Not Sure Yet" / "" / None
    """
    if label is None:
        return 0
    if isinstance(label, int):
        return label if 1 <= label <= 5 else 0
    text = str(label).strip().lower()
    if not text:
        return 0
    if "not sure" in text or "not selected" in text:
        return 0
    for n in (1, 2, 3, 4, 5):
        if f"bracket {n}" in text:
            return n
    return 0


def get_bracket_definition(label_or_number: str | int | None) -> BracketDefinition | None:
    """Return the BracketDefinition for a label or number, or None for unset."""
    n = bracket_number_from_label(label_or_number)
    return BRACKETS.get(n)


def tags_hard_excluded(label_or_number: str | int | None) -> frozenset[str]:
    """Return the simple-tag hard-exclusion set for the bracket.

    Does NOT include the tag_combinations_hard_excluded or
    tag_pair_hard_excluded — those have AND semantics and are checked by the
    filter directly. Use this for "is this single tag a bracket fail?" probes.
    """
    bracket = get_bracket_definition(label_or_number)
    return bracket.tags_hard_excluded if bracket else frozenset()


def is_card_blocked_by_tag_combos(
    bracket: BracketDefinition,
    tags: frozenset[str],
) -> bool:
    """True if the card's tag set is a superset of any blocked combination."""
    for combo in bracket.tag_combinations_hard_excluded:
        if combo.issubset(tags):
            return True
    return False


def is_card_blocked_by_tag_pairs(
    bracket: BracketDefinition,
    tags: frozenset[str],
) -> bool:
    """True if the card's tag set is a superset of any blocked tag pair."""
    for pair in bracket.tag_pair_hard_excluded:
        if pair.issubset(tags):
            return True
    return False


def tags_soft_modifier(
    label_or_number: str | int | None,
    tags: frozenset[str] | set[str],
) -> float:
    """Return cumulative soft score modifier for the card at this bracket.

    Negative = bracket-pressure penalty (B3). Positive = bracket boost (B4/B5).
    Zero for B1/B2 (their hard filter already removed problem cards) and for
    unset / not-sure-yet.
    """
    bracket = get_bracket_definition(label_or_number)
    if not bracket:
        return 0.0
    total = 0.0
    tag_set = frozenset(tags or ())
    for tag, penalty in bracket.tags_soft_penalty.items():
        if tag in tag_set:
            total -= penalty
    for tag, boost in bracket.tags_soft_boost.items():
        if tag in tag_set:
            total += boost
    return total


def is_precon_friendly_exemption(card_name: str | None) -> bool:
    """True if the card name is on the precon-friendly exemption list."""
    if not card_name:
        return False
    return card_name.strip().lower() in PRECON_FRIENDLY_EXEMPTIONS


def filter_summary_for_bracket(label_or_number: str | int | None) -> str:
    """One-line human summary of what filtering applies for this bracket."""
    bracket = get_bracket_definition(label_or_number)
    if not bracket:
        return "No bracket filter applied — all collection cards eligible."
    return bracket.filter_summary or f"{bracket.full_label}: no filter summary defined."
