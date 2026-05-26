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

@dataclass(slots=True)
class ReplaceabilityEntry:
    card_name: str
    quantity: int
    score: int
    cut_confidence: str
    cut_type: str
    reasons: list[str] = field(default_factory=list)
    protected: bool = False

def _confidence_from_score(score: int, protected: bool) -> str:
    if protected:
        return "Low"
    if score >= 8:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"

def _protected_label(tags: set[str], plan_entry: CardPlanFitEntry | None) -> str:
    if plan_entry and plan_entry.supports_primary:
        return "Protected primary-plan support"
    if plan_entry and plan_entry.supports_secondary:
        return "Protected secondary-plan support"
    if tags & {"commander_protection", "commander_defined_support"}:
        return "Protected commander-engine support"
    if tags & INFRASTRUCTURE_TAGS:
        return "Protected infrastructure"
    if tags & HIGH_PRESSURE_TAGS:
        return "Context-dependent keep"
    if tags & SYNERGY_TAGS:
        return "Context-dependent keep"
    return "Playtest-only watch card"

def _cut_type_from_reasons(reasons: list[str], tags: set[str], plan_entry: CardPlanFitEntry | None, protected: bool) -> str:
    if protected:
        return _protected_label(tags, plan_entry)

    joined = " ".join(reasons).lower()

    if tags & HIGH_PRESSURE_TAGS:
        return "Possible Bracket Pressure Cut"
    if "manual" in joined or tags & LOW_IMPACT_REVIEW_TAGS:
        return "Possible Manual Review"
    if not tags or tags == {"manual_review"}:
        return "Possible Role-Uncertain Cut"
    if "redundant" in joined:
        return "Possible Redundancy Cut"
    if "role-balance" in joined or "overfilled" in joined:
        return "Possible Role-Balance Cut"
    if "wrong shell" in joined:
        return "Possible Wrong-Shell Card"
    if "off-plan" in joined or "low-synergy" in joined:
        return "Possible Off-Plan Cut"
    return "Possible Low-Impact Cut"
