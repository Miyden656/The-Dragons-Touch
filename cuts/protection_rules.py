"""Replaceability scoring for possible cut review.

Round 6 cleanup goal:
- Rank review candidates by replaceability, not raw card quality.
- Keep the output cautious: possible cuts are not guaranteed cuts.

Patch Batch 4 cleanup:
- Do not let basic infrastructure become off-theme cut pressure too easily.
- Reduce overuse of "Possible Off-Theme Cut".
- Give protected entries keep-oriented labels so protected sections do not read like cut lists.

v0.6.6.2:
- Apply small philosophy-aware optional-cut nudges.
- Do not override legality, required cuts, protected cards, or pilot intent.
- Keep all philosophy adjustments visible in the reasons list.

v0.6.6.2.1:
- Improve philosophy-bias visibility and trigger/copy-amplifier support.
- Track when bias was evaluated, applied, or missed for diagnostics.
- Preserve philosophy-adjustment reasons when cards move to protected/watch status.

v0.6.6.2.2:
- Count unique adjusted cards separately from total bias hits.
- Suppress review-pressure wording on protected mana-base infrastructure.

v0.6.6.3:
- Improve protected/watch-card language when philosophy bias changes a verdict.
- Use clearer Initial flag / Philosophy adjustment / Final verdict / Why this matters / Review instruction wording.

v0.6.6.3.1:
- Ensure Why this matters and Review instruction fields are surfaced in normal report output.
- Strip old raw v0.6.6.2.2 final-verdict wording from philosophy adjustment text.

v0.6.6.6 lock note:
- Make Balanced / Unknown more neutral before v0.6.6 lock.
- Suppress Balanced philosophy notes on normal infrastructure, primary-plan support, and context-synergy cards.
- Suppress philosophy bias on normal mana-base infrastructure.
- Require stronger evidence for broad Commander Exploiter, Engine Builder, and Power-Level Calibrator aliases.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analysis.plan_fit import CardPlanFitEntry, PlanFitSummary
from analysis.role_tags import CardRoleEntry
from cuts.protected_cards import ProtectedCardEntry

HIGH_PRESSURE_TAGS = {"bracket_pressure", "high_bracket_pressure", "game_changer"}

# Cards with these roles are functional infrastructure first. They can still be
# reviewed when the role is overfilled, but they should not become off-theme cuts
# only because they are not part of the narrow archetype label.
INFRASTRUCTURE_TAGS = {
    "ramp", "land_ramp", "mana_rock", "mana_dork", "mana_source", "cost_reducer",
    "card_draw", "repeatable_card_draw", "card_advantage", "card_selection", "tutor",
    "targeted_removal", "repeatable_removal", "board_wipe", "counterspell", "stack_interaction",
    "protection", "commander_protection", "board_protection", "recursion", "land_recursion",
    "extra_land_play", "land_aura_ramp", "enchant_land_ramp", "mana_infrastructure", "fixing", "mana_fixing", "evasion",
}

# Strategy and package cards are context-sensitive. They should usually become
# manual/playtest review before becoming confident off-theme cuts.
SYNERGY_TAGS = {
    "token_maker", "creature_token_maker", "copy_token_maker", "sacrifice_outlet",
    "recursion", "reanimation", "graveyard_enabler", "self_mill", "discard_outlet",
    "landfall", "lands_matter", "landfall_support", "lands_matter_support",
    "spell_payoff", "noncreature_spell_payoff", "tribal_payoff", "typal_payoff",
    "typal_support", "typal_density", "typal_density_piece", "tribal_dependency",
    "dragon_typal", "dragon_copy_value", "copy_clone_value", "copy_amplifier", "trigger_amplifier", "etb_amplifier", "commander_payoff_amplifier", "big_moment_enabler", "cheat_into_play", "blink_flicker", "blink",
    "etb_value", "ETB_synergy", "toughness_payoff", "defender_payoff",
    "death_trigger_payoff", "aristocrat_payoff", "counter_synergy", "go_tall_support",
    "combat_synergy", "attack_trigger_payoff", "equipment_synergy", "artifact_combat",
    "attachment_synergy", "win_condition", "win_condition_possible", "combo_piece_possible",
}

LOW_IMPACT_REVIEW_TAGS = {"manual_review", "minor_package_card", "manual_review_package_card"}
HIGH_PRESSURE_TAGS = {"bracket_pressure", "high_bracket_pressure", "game_changer"}
INFRASTRUCTURE_TAGS = {
    "ramp", "land_ramp", "mana_rock", "mana_dork", "mana_source", "cost_reducer",
    "card_draw", "repeatable_card_draw", "card_advantage", "card_selection", "tutor",
    "targeted_removal", "repeatable_removal", "board_wipe", "counterspell", "stack_interaction",
    "protection", "commander_protection", "board_protection", "recursion", "land_recursion",
    "extra_land_play", "land_aura_ramp", "enchant_land_ramp", "mana_infrastructure", "fixing", "mana_fixing", "evasion",
}
SYNERGY_TAGS = {
    "token_maker", "creature_token_maker", "copy_token_maker", "sacrifice_outlet",
    "recursion", "reanimation", "graveyard_enabler", "self_mill", "discard_outlet",
    "landfall", "lands_matter", "landfall_support", "lands_matter_support",
    "spell_payoff", "noncreature_spell_payoff", "tribal_payoff", "typal_payoff",
    "typal_support", "typal_density", "typal_density_piece", "tribal_dependency",
    "dragon_typal", "dragon_copy_value", "copy_clone_value", "copy_amplifier", "trigger_amplifier", "etb_amplifier", "commander_payoff_amplifier", "big_moment_enabler", "cheat_into_play", "blink_flicker", "blink",
    "etb_value", "ETB_synergy", "toughness_payoff", "defender_payoff",
    "death_trigger_payoff", "aristocrat_payoff", "counter_synergy", "go_tall_support",
    "combat_synergy", "attack_trigger_payoff", "equipment_synergy", "artifact_combat",
    "attachment_synergy", "win_condition", "win_condition_possible", "combo_piece_possible",
}
LOW_IMPACT_REVIEW_TAGS = {"manual_review", "minor_package_card", "manual_review_package_card"}

def _format_protected_watch_reasons(
    reasons: list[str],
    tags: set[str],
    plan_entry: CardPlanFitEntry | None,
    role_entry: CardRoleEntry,
    philosophy_context: dict | None,
) -> list[str]:
    """Build clearer protected/watch-card language for v0.6.6.3.1."""
    initial_flag = _initial_flag_from_reasons(reasons, tags)
    protected_label = _protected_label(tags, plan_entry)

    # v0.6.6.3.1: keep score-adjustment text separate from verdict text.
    # Older v0.6.6.2.2 wording sometimes included "final philosophy verdict"
    # inside the philosophy adjustment line; do not surface that raw versioned
    # text in the final report.
    philosophy_reasons = [
        reason for reason in reasons
        if "philosophy" in reason.lower() and "final philosophy verdict" not in reason.lower()
    ]
    verdict_reasons = [reason for reason in reasons if "final philosophy verdict" in reason.lower()]
    excluded_reasons = set(philosophy_reasons + verdict_reasons)
    other_reasons = [
        reason for reason in reasons
        if not str(reason).startswith("Initial flag:") and reason not in excluded_reasons
    ]

    if philosophy_reasons:
        adjustment_text = "; ".join(_clean_philosophy_reason(reason) for reason in philosophy_reasons[:2])
    else:
        adjustment_text = "No philosophy score change was needed; normal protection/context rules kept this from being treated as a cut."

    if verdict_reasons:
        final_verdict = "Not currently a cut. Treat as a playtest-only watch card unless playtesting or explicit pilot intent says otherwise."
    else:
        final_verdict = "Not currently a cut. Keep unless playtesting or explicit pilot intent says otherwise."

    return [
        f"Protected Label: {protected_label}",
        f"Initial flag: {initial_flag}",
        f"Philosophy adjustment: {adjustment_text}",
        f"Final verdict: {final_verdict}",
        f"Why this matters: {_watch_card_why_this_matters(tags, protected_label, philosophy_context)}",
        f"Review instruction: {_watch_card_review_instruction(tags, protected_label, initial_flag, philosophy_context)}",
    ] + [f"Supporting note: {reason}" for reason in other_reasons[:2] if reason]

def _is_functional_infrastructure(tags: set[str]) -> bool:
    return bool(tags & INFRASTRUCTURE_TAGS)

def _is_land_aura_ramp(tags: set[str]) -> bool:
    return bool(tags & {"land_aura_ramp", "enchant_land_ramp"})

def _is_context_synergy(tags: set[str]) -> bool:
    return bool(tags & SYNERGY_TAGS)

def _is_mana_base_infrastructure(tags: set[str]) -> bool:
    """Return True for lands that are primarily mana-base infrastructure.

    v0.6.6.2.2: Philosophy review pressure should not add confusing
    generic-goodstuff notes to protected duals/fetches/fixing lands. Lands can
    still be reviewed by normal mana-base logic elsewhere, but the philosophy
    bias layer should not imply that a normal fixing land is a Commander
    Exploiter problem.
    """
    return "land" in tags and "mana_source" in tags

def _has_meaningful_plan_support(plan_entry: CardPlanFitEntry | None) -> bool:
    if not plan_entry:
        return False
    return plan_entry.supports_primary or plan_entry.supports_secondary or plan_entry.plan_fit in {
        "Support / infrastructure",
        "Commander / command-zone engine",
        "Primary plan support",
        "Secondary plan support",
    }
