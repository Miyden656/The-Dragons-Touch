"""Replaceability scoring for possible cut review.

Round 6 cleanup goal:
- Rank review candidates by replaceability, not raw card quality.
- Keep the output cautious: possible cuts are not guaranteed cuts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analysis.plan_fit import CardPlanFitEntry, PlanFitSummary
from analysis.role_tags import CardRoleEntry
from cuts.protected_cards import ProtectedCardEntry

HIGH_PRESSURE_TAGS = {"bracket_pressure", "high_bracket_pressure"}
INFRASTRUCTURE_TAGS = {"ramp", "mana_rock", "mana_dork", "card_draw", "card_advantage", "targeted_removal", "board_wipe", "counterspell", "mana_source"}
SYNERGY_TAGS = {"token_maker", "sacrifice_outlet", "recursion", "landfall", "spell_payoff", "tribal_payoff", "typal_density_piece", "blink_flicker", "etb_value", "toughness_payoff", "defender_payoff", "death_trigger_payoff", "win_condition"}

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


def _cut_type_from_reasons(reasons: list[str], tags: set[str]) -> str:
    joined = " ".join(reasons).lower()
    if "off-plan" in joined or "low-synergy" in joined:
        return "Possible Off-Theme Cut"
    if tags & HIGH_PRESSURE_TAGS:
        return "Possible Bracket Pressure Cut"
    if "redundant" in joined:
        return "Possible Redundancy Cut"
    if "infrastructure" in joined:
        return "Possible Role-Balance Cut"
    if "manual" in joined:
        return "Possible Manual Review"
    return "Possible Low-Impact Cut"


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

        if protected:
            score -= 6
            reasons.append("Protected/core or strong plan-support card; do not treat as a normal cut.")
        if plan_entry and plan_entry.possible_off_plan:
            score += 6
            reasons.append("Possible off-plan or low-synergy based on current primary/secondary strategy read.")
        if plan_entry and plan_entry.supports_primary:
            score -= 5
            reasons.append("Supports primary strategy.")
        elif plan_entry and plan_entry.supports_secondary:
            score -= 2
            reasons.append("Supports secondary strategy.")
        if "manual_review" in tags:
            score += 2
            reasons.append("Manual-review card or role-uncertain card.")
        if tags & HIGH_PRESSURE_TAGS:
            score += 2
            reasons.append("Bracket pressure; review for table fit, not automatic cut.")
        if tags & INFRASTRUCTURE_TAGS and not (plan_entry and plan_entry.supports_primary):
            score -= 1
            reasons.append("Fills infrastructure role; cut only if overfilled or replaced by a better role match.")
        if tags & SYNERGY_TAGS:
            score -= 2
            reasons.append("Has synergy/engine tags that may be important in context.")
        if not tags or tags == {"manual_review"}:
            score += 4
            reasons.append("No clear parsed role beyond manual review.")

        cut_type = _cut_type_from_reasons(reasons, tags)
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
