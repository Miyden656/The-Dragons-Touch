"""Multiplayer / pod-value analysis signal.

WHY THIS EXISTS
---------------
The v1.6 six-signal scoring chain (role tags -> strategy -> bracket -> cuts ->
replacements) analyses *deck construction* and is essentially format-agnostic.
It never asks the Commander-specific question: "you are one of four players, the
game is long, and value math is different." A board wipe that answers three
opponents at once is not weighted above single-target removal that trades 1-for-1
against one of three threats; instant-speed interaction is not counted; table-wide
clocks are not distinguished from single-target ones; nothing reads how big a
target the deck paints (archenemy risk) or how it rebuilds after a sweeper.

This module fills that gap WITHOUT touching the v1.6 chain. It is purely additive:

- It does NOT add tags to ``analysis/role_tags.py`` (that would perturb strategy
  scoring, e.g. ``pillowfort`` already feeds the Control archetype). It reads the
  existing ``role_counts`` plus the shared political signal profile.
- The political signals (goad / pillowfort / instant-speed) come from the single
  shared scanner ``analysis/political_signals.py`` — this module does NOT scan
  oracle text itself, so there is one source of truth for political detection.
- It runs AFTER the existing chain and only reads its outputs, so the engine's
  pre-existing analysis is byte-identical with or without this module.

It produces VERIFIED pod facts (counts + qualitative bands), never advice. The AI
layer interprets these grounded numbers; it does not invent them.

Design reference: ``rules/section_3_strategic_board_politics.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from analysis.political_signals import build_political_signal_profile

# Existing role tags this module reads (all produced by role_tags.py today).
_INTERACTION_ROLES = {"targeted_removal", "counterspell", "board_wipe"}
_TABLE_WIDE_ROLES = {
    "table_damage",
    "group_slug",
    "lifedrain_payoff",
    "punisher",
    "draw_punisher",
}
_THREAT_ROLES = {
    "combo_piece_possible",
    "win_condition",
    "fast_mana",
    "free_interaction",
    "high_bracket_pressure",
    "bracket_pressure",
    "extra_combat",
}


@dataclass(slots=True)
class MultiplayerValueSummary:
    """Engine-verified 4-player pod facts. Counts are by deck copy (quantity)."""

    # --- Interaction profile (the core "value math differs at 4 players" read).
    sweeper_count: int = 0
    spot_removal_count: int = 0
    counterspell_count: int = 0
    total_interaction: int = 0
    instant_speed_interaction_count: int = 0
    interaction_reach_band: str = "narrow"  # wide | balanced | narrow | none

    # --- Table reach: can the deck close on three opponents or just one?
    table_wide_pressure_count: int = 0
    single_target_pressure_count: int = 0
    reach_band: str = "none"  # table_wide | mixed | single_target | none

    # --- Political presence (combat redirection / deterrence).
    goad_count: int = 0
    pillowfort_count: int = 0
    political_presence_band: str = "none"  # none | light | moderate | strong

    # --- Archenemy / threat profile: how big a target does this paint?
    threat_density: int = 0
    archenemy_risk_band: str = "low"  # low | medium | high

    # --- Board-wipe resilience: how fast does it rebuild after a sweeper?
    creature_count: int = 0
    recursion_count: int = 0
    protection_count: int = 0
    creature_reliance_band: str = "low"  # low | moderate | high
    wipe_resilience_band: str = "resilient"  # fragile | moderate | resilient

    # --- Rollups for humans + the AI layer.
    facts: list[str] = field(default_factory=list)
    example_cards: dict[str, list[str]] = field(default_factory=dict)
    confidence: str = "medium"


def _count(role_counts: Any, tag: str) -> int:
    try:
        return int(role_counts.get(tag, 0) or 0)
    except Exception:
        return 0


# Political signal tags (from analysis/political_signals.py) that together mean
# "this card deters attacks on the pilot" — i.e. pillowfort presence.
_PILLOWFORT_TAGS = {"attack_tax", "combat_prevention", "fort_protection"}


def _band_interaction(sweepers: int, spot: int, counters: int) -> str:
    total = sweepers + spot + counters
    if total == 0:
        return "none"
    # "wide" = the deck can answer a developed multiplayer board (real sweeper
    # coverage), not just pick off one threat at a time.
    if sweepers >= 3:
        return "wide"
    if sweepers >= 1 and total >= 5:
        return "balanced"
    return "narrow"


def _band_reach(table_wide: int, single_target: int) -> str:
    if table_wide == 0 and single_target == 0:
        return "none"
    if table_wide >= 3:
        return "table_wide"
    if table_wide >= 1:
        return "mixed"
    return "single_target"


def _band_political(goad: int, pillowfort: int) -> str:
    total = goad + pillowfort
    if total == 0:
        return "none"
    if total >= 5:
        return "strong"
    if total >= 3:
        return "moderate"
    return "light"


def _band_archenemy(threat_density: int) -> str:
    if threat_density >= 7:
        return "high"
    if threat_density >= 3:
        return "medium"
    return "low"


def _band_creature_reliance(creatures: int) -> str:
    if creatures >= 25:
        return "high"
    if creatures >= 12:
        return "moderate"
    return "low"


def _band_wipe_resilience(reliance: str, recursion: int, protection: int) -> str:
    cushion = recursion + protection
    if reliance == "high":
        if cushion >= 6:
            return "moderate"
        return "fragile"
    if reliance == "moderate":
        return "moderate" if cushion < 3 else "resilient"
    return "resilient"


def build_multiplayer_summary(
    role_summary: Any,
    command_zone: Any = None,
    bracket_summary: Any = None,
    scryfall_lookup: dict | None = None,
    *,
    political_profile: Any = None,
) -> MultiplayerValueSummary:
    """Compute verified 4-player pod facts from existing engine outputs.

    Political signals (goad / pillowfort / instant-speed) are read from the shared
    ``political_signals`` profile — passed in by build_analysis_context so it is
    computed once, or built here on demand so this function still stands alone.

    All arguments are read defensively: missing / None inputs degrade to safe
    defaults rather than raising, mirroring the ai/context safe-access posture.
    """
    role_counts = getattr(role_summary, "role_counts", None) or {}
    type_counts = getattr(role_summary, "type_counts", None) or {}
    card_roles = list(getattr(role_summary, "card_roles", None) or [])

    if political_profile is None:
        political_profile = build_political_signal_profile(role_summary, command_zone, scryfall_lookup)
    pol_counts = getattr(political_profile, "counts", None) or {}
    pol_by_card = getattr(political_profile, "signals_by_card", None) or {}

    sweepers = _count(role_counts, "board_wipe")
    spot = _count(role_counts, "targeted_removal")
    counters = _count(role_counts, "counterspell")
    total_interaction = sweepers + spot + counters

    # goad comes straight from the shared political scanner (quantity-weighted).
    goad = _count(pol_counts, "goad")

    # Single pass over card entries for the things role_counts can't tell us:
    # instant-speed interaction, table-wide vs single-target clocks, distinct
    # threat cards, and pillowfort (via the shared political signals per card).
    instant_speed = 0
    table_wide_cards: dict[str, int] = {}
    single_target_cards: dict[str, int] = {}
    threat_cards: dict[str, int] = {}
    pillowfort = 0
    examples: dict[str, list[str]] = {
        "sweepers": [],
        "table_wide_pressure": [],
        "goad": [],
        "pillowfort": [],
        "threats": [],
    }

    for entry in card_roles:
        roles = set(getattr(entry, "detected_roles", None) or [])
        name = getattr(entry, "card_name", "") or ""
        qty = int(getattr(entry, "quantity", 1) or 1)
        type_line = (getattr(entry, "type_line", "") or "").lower()
        pol_sigs = set(pol_by_card.get(name, ()))

        # Instant-speed interaction: an interaction card that can act on others'
        # turns — Instant by type, or flagged instant-speed by the shared scanner.
        if roles & _INTERACTION_ROLES:
            if "instant" in type_line or "instant_speed_interaction" in pol_sigs:
                instant_speed += qty

        if "board_wipe" in roles and len(examples["sweepers"]) < 6:
            examples["sweepers"].append(name)

        if roles & _TABLE_WIDE_ROLES:
            table_wide_cards[name] = qty
            if len(examples["table_wide_pressure"]) < 6:
                examples["table_wide_pressure"].append(name)
        elif "damage_payoff" in roles:
            single_target_cards[name] = qty

        if roles & _THREAT_ROLES:
            threat_cards[name] = qty
            if len(examples["threats"]) < 6:
                examples["threats"].append(name)

        if "goad" in pol_sigs and len(examples["goad"]) < 6:
            examples["goad"].append(name)
        if pol_sigs & _PILLOWFORT_TAGS:
            pillowfort += qty
            if len(examples["pillowfort"]) < 6:
                examples["pillowfort"].append(name)

    table_wide_count = sum(table_wide_cards.values())
    single_target_count = sum(single_target_cards.values())

    # Threat density blends distinct threat cards with the bracket signal's own
    # pressure-card list (read defensively; absent -> 0).
    bracket_pressure_cards = getattr(bracket_summary, "pressure_cards", None) or []
    threat_density = sum(threat_cards.values()) + len(bracket_pressure_cards)

    creatures = 0
    try:
        creatures = int(type_counts.get("Creature", 0) or 0)
    except Exception:
        creatures = 0
    recursion = _count(role_counts, "recursion")
    protection = _count(role_counts, "protection")

    interaction_band = _band_interaction(sweepers, spot, counters)
    reach_band = _band_reach(table_wide_count, single_target_count)
    political_band = _band_political(goad, pillowfort)
    archenemy_band = _band_archenemy(threat_density)
    reliance_band = _band_creature_reliance(creatures)
    resilience_band = _band_wipe_resilience(reliance_band, recursion, protection)

    facts = _build_facts(
        sweepers=sweepers,
        spot=spot,
        counters=counters,
        instant_speed=instant_speed,
        total_interaction=total_interaction,
        table_wide=table_wide_count,
        single_target=single_target_count,
        reach_band=reach_band,
        goad=goad,
        pillowfort=pillowfort,
        political_band=political_band,
        archenemy_band=archenemy_band,
        creatures=creatures,
        reliance_band=reliance_band,
        recursion=recursion,
        protection=protection,
        resilience_band=resilience_band,
    )

    confidence = "low" if not card_roles else ("medium" if scryfall_lookup else "low")

    return MultiplayerValueSummary(
        sweeper_count=sweepers,
        spot_removal_count=spot,
        counterspell_count=counters,
        total_interaction=total_interaction,
        instant_speed_interaction_count=instant_speed,
        interaction_reach_band=interaction_band,
        table_wide_pressure_count=table_wide_count,
        single_target_pressure_count=single_target_count,
        reach_band=reach_band,
        goad_count=goad,
        pillowfort_count=pillowfort,
        political_presence_band=political_band,
        threat_density=threat_density,
        archenemy_risk_band=archenemy_band,
        creature_count=creatures,
        recursion_count=recursion,
        protection_count=protection,
        creature_reliance_band=reliance_band,
        wipe_resilience_band=resilience_band,
        facts=facts,
        example_cards={k: v for k, v in examples.items() if v},
        confidence=confidence,
    )


def _build_facts(**k: Any) -> list[str]:
    """Plain, grounded factual observations the AI can reason from. No advice."""
    facts: list[str] = []

    if k["sweepers"]:
        facts.append(
            f"Board wipes: {k['sweepers']} - each can answer all three opponents' "
            "boards at once (sweepers scale up in a 4-player pod)."
        )
    else:
        facts.append(
            "Board wipes: 0 - a wide opposing board must be answered one threat at "
            "a time, which is slower against three opponents."
        )
    facts.append(
        f"Single-target removal: {k['spot']}; counterspells: {k['counters']} - in a "
        "4-player pod each trades 1-for-1 against one of three opponents."
    )
    if k["total_interaction"]:
        facts.append(
            f"Instant-speed interaction: {k['instant_speed']} of {k['total_interaction']} "
            "interaction cards can act on opponents' turns."
        )

    if k["reach_band"] == "table_wide":
        facts.append(
            f"Table-wide pressure sources: {k['table_wide']} - the deck can pressure "
            "all opponents at once rather than racing one at a time."
        )
    elif k["reach_band"] == "mixed":
        facts.append(
            f"Pressure is mixed: {k['table_wide']} table-wide source(s) plus "
            f"{k['single_target']} single-target source(s)."
        )
    elif k["reach_band"] == "single_target":
        facts.append(
            f"Pressure is single-target only ({k['single_target']} source(s)) - "
            "closing on three opponents means racing them sequentially."
        )

    if k["political_band"] == "none":
        facts.append(
            "No goad or pillowfort detected - few tools to redirect combat away "
            "from you or deter attacks in a multiplayer game."
        )
    else:
        facts.append(
            f"Political tools: {k['goad']} goad, {k['pillowfort']} pillowfort/attack-"
            f"deterrent ({k['political_band']} presence)."
        )

    facts.append(
        f"Archenemy / threat density: {k['archenemy_band']} - informs how much "
        "focused removal this deck is likely to attract across the table."
    )

    facts.append(
        f"Board-wipe resilience: {k['resilience_band']} (creatures: {k['creatures']}, "
        f"recursion: {k['recursion']}, protection: {k['protection']}) - pods run more "
        "sweepers than 1v1, so rebuild speed matters."
    )
    return facts
