"""Curated per-strategy role-tag profiles (Item 6 Phase B, v1.5.45).

WHY THIS MODULE EXISTS
----------------------
The 249-profile strategy index at strategy_knowledge/index/strategy_profile_index.latest.json
was built from prose markdown source files. The index extractor pulls the same
generic 17-tag list for every single profile:

    ['artifacts', 'board_wipe', 'card_draw', 'combat', 'combo', 'counters',
     'enchantments', 'graveyard', 'lifegain', 'protection', 'ramp', 'recursion',
     'removal', 'sacrifice', 'spells', 'tokens', 'tribal']

That means the Build Setup Panel's strategy selector was cosmetic for the
deckbuilder — Storm vs Voltron vs Combo all produced the same Strategy bucket.
Worse, the generic `ramp` and `protection` tags caused the bucket classifier to
slurp mana rocks and equipment-protection into Strategy bucket, leaving Ramp
0/10 and Protection 0/3 across every build.

This module ships hand-curated role_tag sets for the ~45 most-used strategies.
Each set is strategy-DEFINING (what makes Voltron Voltron) and intentionally
omits generic utility tags (ramp / card_draw / protection) UNLESS the strategy
is itself one of those (e.g., Ramp / Big Mana legitimately wants ramp tags as
its Strategy bucket).

WIRING
------
strategy_knowledge/strategy_selector_catalog.py:role_tags_for_display_name
consults STRATEGY_ROLE_TAG_PROFILES first, falls back to the index, falls back
to the legacy ARCHETYPE_DEFINITIONS. Strategies not in this dict keep their
existing placeholder behavior (no regression for niche/fringe/emergent).

BOUNDARIES
----------
- Card-side tags come from analysis/role_tags.py vocabulary. New tags should
  be added there first; this module references existing tags only.
- Each set should be ~5-15 tags. Smaller = sharper selection; larger = blends
  with utility buckets.
- Strategies not in this dict fall through to the generic 17-tag default.
"""
from __future__ import annotations


# -----------------------------------------------------------------------------
# Macro Archetypes (Layer 01) — all 9 profiles covered
# -----------------------------------------------------------------------------
_MACRO: dict[str, set[str]] = {
    "Aggro": {
        "combat_synergy", "attack_trigger_payoff", "go_tall_support",
        "anthem", "equipment_synergy", "haste", "evasion_support",
    },
    "Combo": {
        # v1.5.46: Combo's defining tags are combo pieces + tutors + win cond.
        # No utility-bucket tag conflicts.
        "combo_piece_possible", "win_condition", "efficient_tutor", "tutor",
        "free_interaction", "spell_recursion_possible", "fast_mana", "ritual",
        "graveyard_enabler",
    },
    "Control": {
        # v1.5.46: Control IS its utility — counterspells/wipes/removal/draw
        # ARE the strategy. Keep utility tags here intentionally.
        "counterspell", "board_wipe", "targeted_removal", "free_interaction",
        "card_advantage", "card_draw", "card_selection",
    },
    "Engine / Synergy Value": {
        # v1.5.46: dropped card_draw — Engine strategy is about etb/ltb/synergy,
        # not Card Draw bucket. Draw spells should land in Card Draw bucket.
        "synergy_piece", "card_advantage", "etb_value",
        "trigger_amplifier", "etb_amplifier",
    },
    "Midrange / Value": {
        # v1.5.46: dropped card_draw and targeted_removal — Midrange wants those
        # spells in Card Draw/Removal buckets, not Strategy bucket. Defining
        # tags are value engines (etb/ltb), card advantage, sticky bodies.
        "card_advantage", "etb_value", "ltb_value", "synergy_piece",
        "high_toughness",
    },
    "Ramp / Big Mana": {
        # v1.5.46: Ramp/Big Mana IS ramp — keep ramp/mana_rock/etc. as defining.
        "ramp", "mana_rock", "mana_dork", "mana_source", "mana_doubler",
        "extra_land_play", "big_mana_payoff", "mana_sink", "fast_mana",
    },
    "Stax / Prison": {
        # v1.5.46: Stax IS its utility — tax/slug/board_wipe/counterspell.
        "tax_effect", "group_slug", "pillowfort", "counterspell", "board_wipe",
        "hatebears",
    },
    "Tempo": {
        # v1.5.46: dropped targeted_removal — Tempo wants single-target removal
        # in the Removal bucket, not Strategy bucket. Counterspells stay because
        # Tempo's signature is "tempo via counters."
        "counterspell", "evasion_support",
        "attack_trigger_payoff", "card_selection", "free_interaction",
    },
    "Toolbox": {
        "tutor", "efficient_tutor", "toolbox_support", "card_advantage",
        "synergy_piece", "recursion",
    },
}


# -----------------------------------------------------------------------------
# Mechanical Themes (Layer 02) — top 20 most-used
# -----------------------------------------------------------------------------
_MECHANICAL: dict[str, set[str]] = {
    "+1/+1 Counters": {
        "counter_synergy", "synergy_piece", "go_tall_support", "proliferate",
        "anthem",
    },
    "Aristocrats": {
        "sacrifice_outlet", "free_sacrifice_outlet", "death_trigger_payoff",
        "sacrifice_payoff", "lifedrain_payoff", "token_maker", "recursion",
    },
    "Artifact Synergy": {
        "artifact_payoff", "artifact_token_synergy", "mana_rock",
        "treasure_synergy", "equipment_synergy", "sacrifice_outlet",
    },
    "Auras": {
        "aura_synergy", "enchantment", "go_tall_support", "anthem",
    },
    "Blink / Flicker": {
        "blink_flicker", "etb_value", "etb_amplifier", "trigger_amplifier",
        "synergy_piece",
    },
    "Enchantress": {
        "aura_synergy", "enchantment", "card_draw", "card_advantage",
        "synergy_piece", "anthem",
    },
    "Equipment": {
        "equipment_synergy", "go_tall_support", "anthem",
        "attack_trigger_payoff", "combat_synergy",
    },
    "Extra Combat": {
        "extra_combat", "combat_synergy", "attack_trigger_payoff",
        "go_tall_support", "win_condition",
    },
    "Go-Tall Combat": {
        "go_tall_support", "anthem", "evasion_support", "combat_synergy",
        "voltron",
    },
    "Go-Wide Combat": {
        "token_maker", "anthem", "combat_synergy", "attack_trigger_payoff",
        "evasion_support",
    },
    "Graveyard Matters": {
        "graveyard_enabler", "recursion", "self_mill", "discard_outlet",
        "spell_recursion_possible", "synergy_piece",
    },
    "Landfall / Lands Matter": {
        "landfall", "landfall_payoff", "lands_matter", "extra_land_play",
        "ramp", "mana_source", "mana_infrastructure",
    },
    "Lifedrain": {
        "lifedrain_payoff", "damage_payoff", "table_damage", "lifegain_payoff",
    },
    "Lifegain": {
        "lifegain_payoff", "lifedrain_payoff", "food_synergy", "synergy_piece",
    },
    "Mill": {
        "self_mill", "mill", "graveyard_enabler", "recursion", "card_advantage",
    },
    "Reanimator": {
        "recursion", "graveyard_enabler", "self_mill", "discard_outlet",
        "big_moment_enabler", "cheat_into_play",
    },
    "Spellslinger": {
        "spell_payoff", "noncreature_spell_payoff", "cast_trigger",
        "copy_amplifier", "card_draw", "card_selection", "magecraft",
    },
    "Storm": {
        "spell_payoff", "ritual", "cast_trigger", "copy_amplifier",
        "mana_sink", "combo_piece_possible", "fast_mana", "win_condition",
    },
    "Tokens": {
        "token_maker", "anthem", "attack_trigger_payoff", "combat_synergy",
        "synergy_piece", "sacrifice_payoff",
    },
    "Voltron": {
        "equipment_synergy", "aura_synergy", "go_tall_support",
        "anthem", "evasion_support", "combat_synergy", "voltron",
    },
}


# -----------------------------------------------------------------------------
# Typal/Tribal Themes (Layer 04) — top 9 most-used
# Note: All typal strategies share core tribal tags. Per-creature-type tags
# are added where the role_tags.py vocabulary supports them (currently
# dragon_typal is the only per-type tag).
# -----------------------------------------------------------------------------
_TRIBAL_CORE: set[str] = {
    "tribal_payoff", "typal_density_piece", "tribal_dependency",
    "creature_type_present",
}

_TYPAL: dict[str, set[str]] = {
    "Dragon Typal": _TRIBAL_CORE | {
        "dragon_typal", "big_moment_enabler", "combat_synergy", "haste",
    },
    "Elf Typal": _TRIBAL_CORE | {
        "ramp", "mana_dork", "anthem",
    },
    "Goblin Typal": _TRIBAL_CORE | {
        "combat_synergy", "attack_trigger_payoff", "anthem", "token_maker",
        "haste",
    },
    "Vampire Typal": _TRIBAL_CORE | {
        "lifedrain_payoff", "lifegain_payoff", "anthem",
    },
    "Zombie Typal": _TRIBAL_CORE | {
        "graveyard_enabler", "recursion", "anthem", "token_maker",
    },
    "Spirit Typal": _TRIBAL_CORE | {
        "anthem", "etb_value", "blink_flicker",
    },
    "Wizard Typal": _TRIBAL_CORE | {
        "spell_payoff", "card_draw", "card_selection",
    },
    "Knight Typal": _TRIBAL_CORE | {
        "anthem", "equipment_synergy", "combat_synergy",
    },
    "Soldier Typal": _TRIBAL_CORE | {
        "anthem", "token_maker", "combat_synergy",
    },
}


# -----------------------------------------------------------------------------
# Strategic / Board Politics (Layer 03) — top 8 most-used
# -----------------------------------------------------------------------------
_STRATEGIC: dict[str, set[str]] = {
    "Forced Combat / Goad": {
        "goad", "forced_combat", "combat_synergy", "attack_trigger_payoff",
        "political_card",
    },
    "Group Hug": {
        # v1.5.46: dropped card_advantage — Group Hug GIVES opponents draws
        # (forced_draw is the key tag). Your own draw should land in Card Draw.
        "forced_draw", "group_hug", "mana_source",
        "pillowfort", "political_card",
    },
    "Group Slug": {
        "group_slug", "table_damage", "damage_payoff", "draw_punisher",
        "punisher",
    },
    "Pillowfort": {
        "pillowfort", "protection", "board_wipe", "counterspell", "group_hug",
    },
    "Politics / Deal-Making": {
        "political_card", "pillowfort", "group_hug", "forced_combat",
        "draw_punisher",
    },
    "Punisher / Choice Punisher": {
        "punisher", "group_slug", "table_damage", "damage_payoff",
        "draw_punisher",
    },
    "Revenge / Retaliation": {
        "damage_payoff", "table_damage", "board_wipe", "recursion",
        "win_condition", "punisher",
    },
    "Political Combo Deterrence": {
        "pillowfort", "combo_protection", "free_interaction", "counterspell",
        "protection",
    },
}


# -----------------------------------------------------------------------------
# Master profile dict
# -----------------------------------------------------------------------------
STRATEGY_ROLE_TAG_PROFILES: dict[str, set[str]] = {
    **_MACRO,
    **_MECHANICAL,
    **_TYPAL,
    **_STRATEGIC,
}


def role_tags_for_strategy(display_name: str) -> set[str] | None:
    """Return curated role tags for a strategy display name.

    Returns None if the strategy isn't in the curated dict (caller should
    fall back to the index / ARCHETYPE_DEFINITIONS). Returns an empty set
    is NOT used as a signal — we always either return a populated set or None.
    """
    if not display_name:
        return None
    text = str(display_name).strip()
    # Strip "[Layer] " prefix if present.
    if text.startswith("[") and "]" in text:
        text = text.split("]", 1)[1].strip()
    if not text or text in ("Not selected yet", "None"):
        return None
    return STRATEGY_ROLE_TAG_PROFILES.get(text)


def profile_count_summary() -> dict[str, int]:
    """Diagnostic: how many curated profiles are loaded, grouped roughly."""
    return {
        "total_curated": len(STRATEGY_ROLE_TAG_PROFILES),
        "macro_archetypes": len(_MACRO),
        "mechanical_themes": len(_MECHANICAL),
        "typal_tribal": len(_TYPAL),
        "strategic_politics": len(_STRATEGIC),
    }
