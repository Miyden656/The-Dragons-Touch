"""Strategy-aware creature density band for Build-From-Collection (v1.6.1 Phase 3).

WHY THIS FILE EXISTS
--------------------
Before v1.6.1 the deck builder had no notion of "how many creatures should this
deck contain". The Strategy bucket (target 25) plus Flex (target 7) could
absorb 25-32 creatures for any strategy, even spellslinger/control/combo. User
feedback: even typal decks felt creature-over-tilted.

This module defines, per strategy archetype, a CreatureBand (floor / target /
ceiling) that the builder consults when filling Strategy + Flex slots. The
builder enforces the ceiling during normal fills and only relaxes it when the
collection genuinely can't fill 100 cards without exceeding it (in which case
the report says so).

The bands are intentionally a bit tighter than the typical online "X creature"
guidance because the user reported decks tilting heavy across the board.
Adjust band values here — they are the single tuning surface for this concern.

DENSITY CATEGORIES
------------------
CREATURE_HEAVY  — typal / tribal / aristocrats / tokens / blink / reanimator /
                  combat / go-wide. floor 22, target 26, ceiling 30.
CREATURE_MID    — value-midrange / lifegain / landfall / +1/+1 counters / ramp /
                  hatebears. floor 18, target 22, ceiling 26.
CREATURE_LITE   — Voltron / equipment / control / spellslinger / combo / stax /
                  pillowfort / group hug. floor 12, target 16, ceiling 20.
DEFAULT         — no strategy chosen or strategy doesn't match any band.
                  floor 16, target 22, ceiling 28.

These counts INCLUDE the commander (who is almost always a creature). The
builder accounts for that when comparing.

WHY NOT HARDER LIMITS?
----------------------
The ceiling is the practical lever — under it, deck-builder pressure (Strategy
bucket size, Flex selection) shapes the deck. Above it the builder skips
creature picks until something noncreature is available. The floor is purely
diagnostic — surfaces "your collection was thin on Dragons-the-creature; deck
has 24 creatures, target band 26-30, floor 22 still met."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


CATEGORY_CREATURE_HEAVY = "creature_heavy"
CATEGORY_CREATURE_MID = "creature_mid"
CATEGORY_CREATURE_LITE = "creature_lite"
CATEGORY_DEFAULT = "creature_default"


@dataclass(frozen=True, slots=True)
class CreatureBand:
    """Floor / target / ceiling counts for total deck creatures (incl. commander)."""

    category: str
    floor: int
    target: int
    ceiling: int
    rationale: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "floor": self.floor,
            "target": self.target,
            "ceiling": self.ceiling,
            "rationale": self.rationale,
        }


BAND_CREATURE_HEAVY = CreatureBand(
    category=CATEGORY_CREATURE_HEAVY,
    floor=22,
    target=26,
    ceiling=30,
    rationale=(
        "Typal / aristocrats / blink / reanimator / go-wide / combat-damage "
        "strategies need a creature density to function, but past ~30 creatures "
        "the deck starves on noncreature ramp, draw, removal, and protection."
    ),
)

BAND_CREATURE_MID = CreatureBand(
    category=CATEGORY_CREATURE_MID,
    floor=18,
    target=22,
    ceiling=26,
    rationale=(
        "Value-midrange / lifegain / landfall / +1/+1 counter / ramp shells "
        "want a normal creature suite — enough threats and ETB value to apply "
        "pressure without crowding the noncreature engine slots."
    ),
)

BAND_CREATURE_LITE = CreatureBand(
    category=CATEGORY_CREATURE_LITE,
    floor=12,
    target=16,
    ceiling=20,
    rationale=(
        "Voltron / equipment / control / spellslinger / combo / stax / "
        "pillowfort shells lean on spells, equipment, or a small payoff "
        "creature suite. Too many creatures dilutes the engine."
    ),
)

BAND_DEFAULT = CreatureBand(
    category=CATEGORY_DEFAULT,
    floor=16,
    target=22,
    ceiling=28,
    rationale=(
        "No strategy was picked (or the picked strategy didn't match a "
        "known band). Conservative mid-range default — keeps creatures from "
        "drowning out noncreature support but doesn't force a creature deck "
        "into a control shape."
    ),
)


# Tag-based detection. These are the role-tag names produced by
# analysis/role_tags.py. We classify by whichever band a strategy's tags
# match most strongly. A strategy can pull from BOTH heavy and lite (e.g.,
# Reanimator-Combo); the resolver favors the stronger signal but the test
# suite documents the chosen behavior so re-tuning is easy.
_HEAVY_TAGS: frozenset[str] = frozenset({
    "tribal_payoff",
    "tribal_dependency",
    "typal_density_piece",
    "typal_payoff",
    "typal_enabler",
    "creature_type_present",
    "token_maker",
    "sacrifice_outlet",
    "free_sacrifice_outlet",
    "death_trigger_payoff",
    "sacrifice_payoff",
    "blink_flicker",
    "etb_amplifier",
    "etb_value",
    "ltb_value",
    "extra_combat",
    "combat_synergy",
    "attack_trigger_payoff",
    "go_tall_support",
    "creature_combo_value",
    "mutate",
    "mutate_payoff",
})

_LITE_TAGS: frozenset[str] = frozenset({
    "equipment_synergy",
    "aura_synergy",
    "counterspell",
    "board_wipe",
    "spell_payoff",
    "noncreature_spell_payoff",
    "cast_trigger",
    "cast_copy_synergy",
    "spell_recursion_possible",
    "combo_piece_possible",
    "win_condition",
    "free_interaction",
    "combo_protection",
    "efficient_tutor",
    "ritual",
    "wheel",
    "forced_draw",
    "group_slug",
    "punisher",
    "draw_punisher",
})

_MID_TAGS: frozenset[str] = frozenset({
    "ramp",
    "mana_rock",
    "mana_doubler",
    "mana_source",
    "extra_land_play",
    "landfall",
    "landfall_payoff",
    "lands_matter",
    "lifegain_payoff",
    "lifedrain_payoff",
    "counter_synergy",  # +1/+1 counters
    "toughness_payoff",
    "defender_payoff",
    "high_toughness",
    "artifact_payoff",
    "artifact_token_synergy",
})


# Label-keyword detection — used when no curated tags are available for the
# selected strategy. Each keyword set is lower-case, whole-word fragments.
# The matcher splits the strategy label on non-alphanumeric chars and tests
# each token against these sets.
_HEAVY_LABEL_KEYWORDS: frozenset[str] = frozenset({
    "typal", "tribal", "aristocrats", "aristocrat", "tokens", "token",
    "go-wide", "wide", "swarm", "reanimator", "graveyard-creatures",
    "blink", "flicker", "etb", "combat", "voltron-creature",
    "dragons", "elves", "goblins", "vampires", "zombies", "merfolk",
    "knights", "soldiers", "humans", "wizards", "sliver", "slivers",
    "elder", "dinosaurs", "dinos", "spirits", "cats", "demons", "angels",
})

_LITE_LABEL_KEYWORDS: frozenset[str] = frozenset({
    "voltron", "equipment", "auras", "aura", "control", "spellslinger",
    "spells", "combo", "stax", "pillowfort", "group", "hug", "groupslug",
    "prison", "lock", "storm", "wheel", "wheels", "mill", "infect",
    "cedh", "competitive",
})

_MID_LABEL_KEYWORDS: frozenset[str] = frozenset({
    "ramp", "bigmana", "lands", "landfall", "lifegain", "midrange",
    "value", "counters", "+1/+1", "hatebears", "artifacts", "treasures",
    "tempo",
})


def _tokenize_label(label: str) -> list[str]:
    """Lower-case, non-alphanumeric-split tokens from a strategy label."""
    if not label:
        return []
    out: list[str] = []
    buf: list[str] = []
    for ch in str(label).lower():
        if ch.isalnum() or ch == "+" or ch == "/":
            buf.append(ch)
        else:
            if buf:
                out.append("".join(buf))
                buf = []
    if buf:
        out.append("".join(buf))
    return out


def classify_creature_band(
    *,
    strategy_tags: Iterable[str] | None = None,
    primary_strategy_label: str = "",
    secondary_strategy_label: str = "",
) -> CreatureBand:
    """Pick a CreatureBand from the chosen strategy.

    Tag-driven first (more reliable since the strategy_role_tag_profiles
    catalog backs it). Falls back to label keyword matching when tags are
    empty or unrecognised, then to DEFAULT.

    The resolver is intentionally simple: count tag overlaps with the heavy
    / lite / mid families. Highest wins. Ties prefer the lighter band so a
    creature-themed strategy that ALSO uses combos doesn't blow past the
    ceiling. The user's "across the board" complaint motivated that choice.
    """
    tags = {str(tag).lower() for tag in (strategy_tags or []) if tag}

    heavy_hits = len(tags & _HEAVY_TAGS)
    lite_hits = len(tags & _LITE_TAGS)
    mid_hits = len(tags & _MID_TAGS)

    if heavy_hits or lite_hits or mid_hits:
        # Tag-based classification. Ties go to the lighter band.
        if heavy_hits > lite_hits and heavy_hits > mid_hits:
            return BAND_CREATURE_HEAVY
        if lite_hits >= heavy_hits and lite_hits >= mid_hits:
            return BAND_CREATURE_LITE
        if mid_hits >= heavy_hits:
            return BAND_CREATURE_MID
        return BAND_CREATURE_HEAVY

    # No tag signal. Fall back to label keyword scan.
    tokens: list[str] = []
    tokens.extend(_tokenize_label(primary_strategy_label))
    tokens.extend(_tokenize_label(secondary_strategy_label))
    token_set = set(tokens)

    heavy_kw = len(token_set & _HEAVY_LABEL_KEYWORDS)
    lite_kw = len(token_set & _LITE_LABEL_KEYWORDS)
    mid_kw = len(token_set & _MID_LABEL_KEYWORDS)

    if heavy_kw == 0 and lite_kw == 0 and mid_kw == 0:
        return BAND_DEFAULT
    if heavy_kw > lite_kw and heavy_kw > mid_kw:
        return BAND_CREATURE_HEAVY
    if lite_kw >= heavy_kw and lite_kw >= mid_kw:
        return BAND_CREATURE_LITE
    return BAND_CREATURE_MID


def is_creature_type_line(type_line: str | None) -> bool:
    """Return True when a card's type_line marks it as a creature.

    Handles MDFC / split / adventure rooms by checking each face. Excludes
    creature LANDS like Treetop Village and Mishra's Factory because while
    they can become creatures, they occupy a land slot and don't change the
    "how many creatures does the deck need" math.
    """
    if not type_line:
        return False
    tl = str(type_line)
    for face in tl.split("//"):
        face_stripped = face.strip()
        if "Creature" in face_stripped and "Land" not in face_stripped:
            return True
    return False


def creature_band_status_label(
    band: CreatureBand,
    actual_creature_count: int,
) -> str:
    """Short human-readable comparison of the actual count to the band."""
    if actual_creature_count < band.floor:
        return (
            f"⚠ below floor — only {actual_creature_count} creatures "
            f"(band {band.floor}-{band.ceiling}, target {band.target}). "
            f"Collection may be thin on creature support for this strategy."
        )
    if actual_creature_count > band.ceiling:
        return (
            f"⚠ above ceiling — {actual_creature_count} creatures "
            f"(band {band.floor}-{band.ceiling}, target {band.target}). "
            f"Builder relaxed the ceiling because the collection was thin "
            f"on noncreature support."
        )
    return (
        f"✓ within band — {actual_creature_count} creatures "
        f"(band {band.floor}-{band.ceiling}, target {band.target})."
    )
