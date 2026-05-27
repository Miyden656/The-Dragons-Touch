"""Philosophy / persona bias for Bin B deck builder (Item 4 v1.5.42).

Each of the 18 Sub-philosophy / persona choices in the Build Setup Panel maps
to a small "what this player values" bias profile — a set of role-tag score
modifiers that nudge the deck builder toward picks that fit the persona.

This makes Battlecruiser-mode decks visibly different from Combo Builder decks
and Efficiency Optimizer decks built from the same collection + commander +
strategy. Without it, the previous behavior was: same deck regardless of
philosophy choice.

Modifier scale matches the bracket filter scoring (~ 0.5 to 2.5 per tag) so
no single signal overwhelms the others.

Boundaries:
- This is selection bias only. It does NOT change role tags or color identity.
- Modifiers are additive on top of strategy + bracket + commander-text scoring.
- "No Persona / Not Sure Yet" returns an empty bias (no modifier).
"""
from __future__ import annotations

from typing import Iterable


# Persona name → {role_tag: score_modifier}. Positive = prefer; negative = avoid.
# Persona names match the display labels emitted by
# build_from_collection.philosophy_bracket_preferences.SUB_PHILOSOPHY_OPTIONS
# AFTER the persona suffix is stripped (e.g. "Engine Builder — Brad / Bria"
# matches the key "Engine Builder").
PERSONA_BIAS: dict[str, dict[str, float]] = {
    # ---- Timmy / Tammy (big moments, splashy effects) -----------------------
    "Big Moment": {
        "win_condition": +2.5,
        "finisher_or_payoff": +2.0,
        "big_mana_payoff": +1.5,
        "mana_sink": +1.0,
        "board_wipe": +1.0,
        "high_toughness": +0.5,
        "efficient_tutor": -1.0,
        "fast_mana": -0.5,
    },
    "Big Creature / Stompy": {
        "voltron": +2.0,
        "go_tall_support": +2.0,
        "equipment_synergy": +1.5,
        "high_toughness": +1.0,
        "protection": +1.5,
        "evasion_support": +1.0,
        "anthem": +0.5,
        "token_maker": -0.5,
    },
    "Theme / Vibe": {
        "typal_density_piece": +1.5,
        "tribal_payoff": +1.5,
        "enchantment": +1.0,
        "aura_synergy": +1.0,
        "synergy_piece": +0.5,
        "fast_mana": -1.0,
        "efficient_tutor": -1.0,
    },
    "Pet Card": {
        "protection": +2.0,
        "recursion": +1.5,
        "graveyard_enabler": +1.0,
        "synergy_piece": +0.5,
    },
    "Let Me Do My Thing": {
        "protection": +2.0,
        "pillowfort": +2.0,
        "ramp": +1.0,
        "mana_rock": +0.5,
        "group_slug": -1.5,
        "table_damage": -1.0,
        "draw_punisher": -1.0,
    },
    "Battlecruiser": {
        "win_condition": +2.0,
        "big_mana_payoff": +1.5,
        "board_wipe": +1.5,
        "finisher_or_payoff": +1.5,
        "anthem": +1.0,
        "efficient_tutor": -1.0,
        "fast_mana": -1.0,
        "counterspell": -0.5,
    },

    # ---- Johnny / Jenny (engines, combos, novelty) --------------------------
    "Engine Builder": {
        "trigger_amplifier": +2.0,
        "copy_amplifier": +1.5,
        "etb_amplifier": +1.5,
        "commander_payoff_amplifier": +2.0,
        "synergy_piece": +1.0,
        "card_advantage": +1.0,
        "etb_value": +1.0,
        "blink_flicker": +0.5,
    },
    "Commander Exploiter": {
        # Lets the commander-text amplifier pass do most of the work, but
        # additionally rewards trigger/copy doublers and synergy density.
        "trigger_amplifier": +2.5,
        "copy_amplifier": +2.0,
        "etb_amplifier": +2.0,
        "commander_payoff_amplifier": +2.5,
        "synergy_piece": +1.0,
    },
    "Weird Card Rescuer": {
        # No strong negative weights — let unusual cards float up.
        "synergy_piece": +0.5,
        "manual_review": +0.5,
        "fast_mana": -1.0,
        "efficient_tutor": -1.0,
    },
    "Theme Mechanic Inventor": {
        "spell_payoff": +1.5,
        "mutate": +1.5,
        "mutate_payoff": +1.5,
        "counter_synergy": +1.0,
        "synergy_piece": +1.0,
        "trigger_amplifier": +1.0,
    },
    "Self-Imposed Constraint Builder": {
        "synergy_piece": +1.0,
        "typal_density_piece": +1.0,
        "tribal_payoff": +1.0,
        "spell_payoff": +0.5,
    },
    "Combo Builder": {
        "combo_piece_possible": +2.5,
        "win_condition": +2.0,
        "efficient_tutor": +2.0,
        "tutor": +1.5,
        "free_interaction": +1.0,
        "protection": +1.0,
    },

    # ---- Spike (consistency, optimization, competitive) ---------------------
    "Consistency Maximizer": {
        "tutor": +2.0,
        "efficient_tutor": +1.5,
        "card_draw": +1.5,
        "card_advantage": +1.5,
        "card_selection": +1.5,
    },
    "Efficiency Optimizer": {
        "fast_mana": +2.0,
        "efficient_tutor": +1.5,
        "mana_rock": +1.0,
        "ramp": +1.0,
        "ritual": +1.0,
        "free_interaction": +1.0,
    },
    "Curve and Mana Discipline": {
        "ramp": +2.0,
        "mana_rock": +1.5,
        "mana_dork": +1.5,
        "mana_source": +1.0,
        "extra_land_play": +1.0,
        "high_toughness": -0.5,
    },
    "Competitive Closer": {
        "win_condition": +2.5,
        "combo_piece_possible": +2.0,
        "efficient_tutor": +2.0,
        "tutor": +1.5,
        "free_interaction": +1.5,
        "fast_mana": +1.0,
    },
    "Power-Level Calibrator": {
        # Defers to the bracket filter — modest preference for bracket-pressure
        # cards so the build hits the player's chosen power ceiling.
        "bracket_pressure": +0.5,
    },
    "Interaction Controller": {
        "targeted_removal": +2.0,
        "counterspell": +2.0,
        "board_wipe": +1.5,
        "free_interaction": +1.5,
        "protection": +1.0,
        "recursion": +0.5,
    },
}


def persona_name_from_selector_value(value: str | None) -> str:
    """Extract the bare persona name from a Build Setup Panel selector value.

    Sub-philosophy options look like "Engine Builder — Brad / Bria"; this
    returns just "Engine Builder". Returns "" for empty / "No Persona" / "Not Sure"
    values.
    """
    if not value:
        return ""
    text = str(value).strip()
    if not text or text == "No Persona / Not Sure Yet":
        return ""
    if " — " in text:
        bare = text.split(" — ", 1)[0].strip()
    elif " - " in text:
        bare = text.split(" - ", 1)[0].strip()
    else:
        bare = text
    return bare


def philosophy_score_modifier(
    card_tags: Iterable[str],
    sub_philosophy: str | None,
) -> float:
    """Return the philosophy-bias score modifier for a card.

    Looks up the persona profile in PERSONA_BIAS and sums the per-tag modifiers
    for every tag the card has. Caps the total magnitude at +/- 8.0 so a single
    persona signal can't overwhelm strategy + bracket + commander-text scoring.
    """
    persona = persona_name_from_selector_value(sub_philosophy)
    if not persona:
        return 0.0
    profile = PERSONA_BIAS.get(persona)
    if not profile:
        return 0.0
    tags = set(card_tags or ())
    total = 0.0
    for tag, modifier in profile.items():
        if tag in tags:
            total += modifier
    # Clamp so the persona bias is a nudge, not a takeover.
    if total > 8.0:
        total = 8.0
    elif total < -8.0:
        total = -8.0
    return total


def philosophy_bias_summary(sub_philosophy: str | None) -> str:
    """Human-readable line describing what bias this persona applies."""
    persona = persona_name_from_selector_value(sub_philosophy)
    if not persona:
        return ""
    profile = PERSONA_BIAS.get(persona)
    if not profile:
        return f"Philosophy: {persona} (no specific card-selection bias defined)."
    # List the top boosted + top penalized tags in plain English.
    sorted_items = sorted(profile.items(), key=lambda kv: kv[1], reverse=True)
    boosted = [tag.replace("_", " ") for tag, mod in sorted_items if mod > 0][:5]
    penalized = [tag.replace("_", " ") for tag, mod in sorted_items if mod < 0][:3]
    parts = [f"Philosophy: {persona}"]
    if boosted:
        parts.append("prefers " + ", ".join(boosted))
    if penalized:
        parts.append("avoids " + ", ".join(penalized))
    return " — ".join(parts) + "."
