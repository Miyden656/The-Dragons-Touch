"""Replaceability scoring for possible cut review.

Round 6 cleanup goal:
- Rank review candidates by replaceability, not raw card quality.
- Keep the output cautious: possible cuts are not guaranteed cuts.

Patch Batch 4 cleanup:
- Do not let basic infrastructure become off-theme cut pressure too easily.
- Reduce overuse of "Possible Off-Theme Cut".
- Give protected entries keep-oriented labels so protected sections do not read like cut lists.
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
    "extra_land_play", "fixing", "mana_fixing", "evasion",
}

# Strategy and package cards are context-sensitive. They should usually become
# manual/playtest review before becoming confident off-theme cuts.
SYNERGY_TAGS = {
    "token_maker", "creature_token_maker", "copy_token_maker", "sacrifice_outlet",
    "recursion", "reanimation", "graveyard_enabler", "self_mill", "discard_outlet",
    "landfall", "lands_matter", "landfall_support", "lands_matter_support",
    "spell_payoff", "noncreature_spell_payoff", "tribal_payoff", "typal_payoff",
    "typal_support", "typal_density", "typal_density_piece", "tribal_dependency",
    "dragon_typal", "dragon_copy_value", "copy_clone_value", "blink_flicker", "blink",
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


def _initial_flag_from_reasons(reasons: list[str], tags: set[str]) -> str:
    joined = " ".join(reasons).lower()
    if tags & HIGH_PRESSURE_TAGS:
        return "Possible Bracket Pressure Cut"
    if "off-plan" in joined or "low-synergy" in joined:
        return "Possible Off-Plan Review"
    if "manual" in joined or tags & LOW_IMPACT_REVIEW_TAGS:
        return "Possible Manual Review"
    if "infrastructure" in joined:
        return "Possible Role-Balance Review"
    if not tags or tags == {"manual_review"}:
        return "Possible Role-Uncertain Review"
    return "Possible Low-Impact Review"


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


def _is_functional_infrastructure(tags: set[str]) -> bool:
    return bool(tags & INFRASTRUCTURE_TAGS)


def _is_context_synergy(tags: set[str]) -> bool:
    return bool(tags & SYNERGY_TAGS)


def _has_meaningful_plan_support(plan_entry: CardPlanFitEntry | None) -> bool:
    if not plan_entry:
        return False
    return plan_entry.supports_primary or plan_entry.supports_secondary or plan_entry.plan_fit in {
        "Support / infrastructure",
        "Commander / command-zone engine",
        "Primary plan support",
        "Secondary plan support",
    }


def build_replaceability_review(
    card_roles: list[CardRoleEntry],
    plan_fit_summary: PlanFitSummary,
    protected_cards: list[ProtectedCardEntry],
) -> list[ReplaceabilityEntry]:
    plan_fit_by_name: dict[str, CardPlanFitEntry] = {entry.card_name: entry for entry in plan_fit_summary.entries}
    protected_names = {entry.card_name for entry in protected_cards if entry.protection_level in {"core", "high", "medium"}}
    entries: list[ReplaceabilityEntry] = []

    for role_entry in card_roles:
        tags = set(role_entry.detected_roles)
        plan_entry = plan_fit_by_name.get(role_entry.card_name)
        score = 0
        reasons: list[str] = []
        protected = role_entry.card_name in protected_names
        is_infrastructure = _is_functional_infrastructure(tags)
        is_context_synergy = _is_context_synergy(tags)
        has_plan_support = _has_meaningful_plan_support(plan_entry)

        # Protection and positive plan fit should strongly reduce cut pressure.
        if protected:
            score -= 6
            reasons.append("Protected/core or strong plan-support card; do not treat as a normal cut.")
        if plan_entry and plan_entry.supports_primary:
            score -= 5
            reasons.append("Supports primary strategy.")
        elif plan_entry and plan_entry.supports_secondary:
            score -= 2
            reasons.append("Supports secondary strategy.")

        # Off-plan pressure should not hit infrastructure/synergy cards as hard.
        if plan_entry and plan_entry.possible_off_plan:
            if is_infrastructure:
                score += 1
                reasons.append("Initial flag: possible off-plan, but this card fills a Commander infrastructure role.")
            elif is_context_synergy:
                score += 3
                reasons.append("Possible off-plan or low-synergy, but this card has context-dependent synergy tags and should be reviewed carefully.")
            else:
                score += 6
                reasons.append("Possible off-plan or low-synergy based on current primary/secondary strategy read.")

        if "manual_review" in tags:
            score += 1 if (is_infrastructure or is_context_synergy or has_plan_support) else 2
            reasons.append("Manual-review card or role-uncertain card.")

        if tags & HIGH_PRESSURE_TAGS:
            score += 2
            reasons.append("Bracket pressure; review for table fit, not automatic cut.")

        if is_infrastructure:
            score -= 2 if has_plan_support else 1
            reasons.append("Fills infrastructure role; cut only if overfilled or replaced by a better role match.")

        if is_context_synergy:
            score -= 2
            reasons.append("Has synergy/engine tags that may be important in context.")

        if not tags or tags == {"manual_review"}:
            score += 4
            reasons.append("No clear parsed role beyond manual review.")

        cut_type = _cut_type_from_reasons(reasons, tags, plan_entry, protected)

        # Protected entries should read like keep guidance even if the report formatter
        # still uses a generic "Cut type" label.
        if protected:
            initial_flag = _initial_flag_from_reasons(reasons, tags)
            protected_label = _protected_label(tags, plan_entry)
            reasons = [
                f"Protected Label: {protected_label}",
                f"Initial flag: {initial_flag}",
                "Final verdict: Not currently a cut. Keep unless playtesting or user intent says otherwise.",
            ] + [reason for reason in reasons if not reason.startswith("Initial flag:")][:2]

        entries.append(ReplaceabilityEntry(
            card_name=role_entry.card_name,
            quantity=role_entry.quantity,
            score=score,
            cut_confidence=_confidence_from_score(score, protected),
            cut_type=cut_type,
            reasons=reasons or ["No special cut/protection reason detected."],
            protected=protected,
        ))

    return sorted(entries, key=lambda entry: entry.score, reverse=True)
