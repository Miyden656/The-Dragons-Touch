"""Tribal fidelity scoring boost for typal commanders (v1.6.2 Phase C).

WHY THIS FILE EXISTS
--------------------
During the v1.6.1 audit, a real Ghalta dinosaur-typal build pulled 29
creatures but only 2 were Dinosaurs. The other 27 were generic green
creatures whose scores happened to be high. The deck builder's existing
scoring chain (strategy fit + commander amplifier + persona + combo)
rewards CARD ROLE TAGS but doesn't directly reward tribal MATCH.

This module fixes that gap: when the commander is a Legendary Creature
with a clear creature subtype (Dragon, Dinosaur, Rabbit, etc.), cards
that share that subtype get an explicit score boost during pool
selection. Cards that don't share are unaffected, so typal-adjacent
strategies (Dragon Voltron, Dinosaur Ramp) still pick supporting
noncreature spells correctly.

DESIGN NOTES
------------
- Detection extracts ALL creature subtypes from the commander's type line.
  A small UNIVERSAL_CLASS_TYPES set is excluded — these are subtype words
  that appear on many creatures across tribes (Elder, Avatar) and would
  give false positives.
- "Race" and "class" types are not distinguished here. For Knight typal,
  Knight should match; for Wizard typal, Wizard should match. We trust
  that the commander's subtype list reflects the deck's intended tribe.
- Cards that share MORE subtypes get a stronger boost. A single shared
  subtype gives the default boost; multiple shared subtypes scale up
  with diminishing returns.
- The boost is applied AFTER all other scoring signals so it nudges
  selection toward on-tribe creatures without overwriting the commander
  amplifier or persona bias.

PUBLIC API
----------
- extract_commander_tribes(card)   -> set[str]
- extract_card_tribes(card)        -> set[str]
- shared_tribes(card_a, card_b)    -> set[str]
- tribal_fidelity_boost(commander_tribes, card_tribes,
                        default_boost=2.5) -> float
- describe_tribal_match(commander_tribes, card_tribes) -> str
"""
from __future__ import annotations

from typing import Any


# Creature subtype words that show up across many tribes and would create
# false positives if treated as tribal matches. Elder appears on many
# Elder Dragons, Elder Elementals, Elder Dinosaurs etc. — sharing 'Elder'
# alone isn't a tribal signal.
UNIVERSAL_CLASS_TYPES: frozenset[str] = frozenset({
    "elder",
    "avatar",
    "token",
    "legend",  # rare, but just in case
})


# Per-extra-shared-tribe boost beyond the first. Diminishing returns so a
# multi-type creature (e.g., "Elf Wizard" in an Elf+Wizard combined deck)
# doesn't completely dominate.
EXTRA_TRIBE_MULTIPLIER: float = 0.5


def _extract_subtypes_from_type_line(type_line: str) -> set[str]:
    """Pull lower-case creature subtypes from a type line.

    Handles MDFC / split cards via '//'. Subtypes are the words after the
    em-dash on a creature face. For example:
      'Legendary Creature — Elder Dinosaur' -> {'elder', 'dinosaur'}
      'Creature — Goblin Warrior' -> {'goblin', 'warrior'}
    """
    if not type_line:
        return set()
    subtypes: set[str] = set()
    for face in str(type_line).split("//"):
        face = face.strip()
        if "—" not in face:
            continue
        # Only look at creature faces; tribal subtypes only apply to creatures.
        before_dash, after_dash = face.split("—", 1)
        if "Creature" not in before_dash:
            continue
        for word in after_dash.strip().split():
            word_clean = word.strip().lower().rstrip(",.;:")
            if word_clean:
                subtypes.add(word_clean)
    return subtypes


def extract_commander_tribes(card: dict[str, Any] | None) -> set[str]:
    """Return the tribal-relevant creature subtypes from a commander card.

    Strips universal class-type words (Elder, Avatar, etc.) so they don't
    create false tribal matches.
    """
    raw = _extract_subtypes_from_type_line(
        str(card.get("type_line") or "") if isinstance(card, dict) else ""
    )
    return raw - UNIVERSAL_CLASS_TYPES


def extract_card_tribes(card: dict[str, Any] | None) -> set[str]:
    """Return all creature subtypes from a card.

    Keeps universal class-type words because, e.g., an 'Elder Dinosaur'
    card legitimately is an Elder; we just don't want to use 'Elder' as
    the matching key on the commander side.
    """
    return _extract_subtypes_from_type_line(
        str(card.get("type_line") or "") if isinstance(card, dict) else ""
    )


def shared_tribes(
    commander_tribes: set[str],
    card_tribes: set[str],
) -> set[str]:
    """Return the set of tribes shared between commander and a 99 card."""
    if not commander_tribes or not card_tribes:
        return set()
    return commander_tribes & card_tribes


def tribal_fidelity_boost(
    commander_tribes: set[str],
    card_tribes: set[str],
    *,
    default_boost: float = 2.5,
) -> float:
    """Return the score boost for a card based on tribal overlap.

    - 0 shared tribes: 0.0 boost.
    - 1 shared tribe: default_boost.
    - N shared tribes: default_boost * (1 + (N-1) * EXTRA_TRIBE_MULTIPLIER).
      So 2 shared tribes = 1.5 x default, 3 shared = 2.0 x, etc.

    The boost is applied per CARD (not per copy) and is intended to be added
    on top of the existing scoring chain. With default_boost=2.5 the boost is
    comparable to a "Strategy fit" tag overlap (3.0) so on-tribe creatures
    compete with strategy-aligned noncreatures for slots.
    """
    shared = shared_tribes(commander_tribes, card_tribes)
    n = len(shared)
    if n == 0:
        return 0.0
    return default_boost * (1.0 + (n - 1) * EXTRA_TRIBE_MULTIPLIER)


def describe_tribal_match(
    commander_tribes: set[str],
    card_tribes: set[str],
) -> str:
    """Return a short human-readable description of the tribal overlap.

    Used as a why-tag suffix in the report so the user can see why a card
    was preferred. Returns an empty string for no overlap.
    """
    shared = shared_tribes(commander_tribes, card_tribes)
    if not shared:
        return ""
    # Title-case the tribe names for display ("dragon" -> "Dragon").
    pretty = sorted(t.title() for t in shared)
    return "Tribal fit (" + ", ".join(pretty) + ")"
