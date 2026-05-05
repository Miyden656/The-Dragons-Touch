"""Plan-fit classification helpers.

Round 5 cleanup goal:
- Keep card/plan relationship logic separate from raw tags and strategy scoring.
- This module does not make final cut recommendations; it only labels plan fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deck_helper.analysis.role_tags import CardRoleEntry
from deck_helper.analysis.strategy_scoring import ARCHETYPE_DEFINITIONS, StrategySummary

@dataclass(slots=True)
class CardPlanFitEntry:
    card_name: str
    quantity: int
    plan_fit: str
    supports_primary: bool
    supports_secondary: bool
    possible_off_plan: bool
    reasons: list[str] = field(default_factory=list)

@dataclass(slots=True)
class PlanFitSummary:
    entries: list[CardPlanFitEntry]
    strong_synergy_cards: list[CardPlanFitEntry]
    possible_off_plan_cards: list[CardPlanFitEntry]


def get_strategy_tag_set(strategy_name: str) -> set[str]:
    definition = ARCHETYPE_DEFINITIONS.get(strategy_name, {})
    return set(definition.get("anchors", set())) | set(definition.get("payoffs", set())) | set(definition.get("enablers", set()))


def classify_card_plan_fit(card_entry: CardRoleEntry, strategy_summary: StrategySummary) -> CardPlanFitEntry:
    tags = set(card_entry.detected_roles)
    primary_tags = get_strategy_tag_set(strategy_summary.primary_strategy)
    secondary_tags = get_strategy_tag_set(strategy_summary.secondary_strategy)

    supports_primary = bool(tags & primary_tags)
    supports_secondary = bool(tags & secondary_tags)
    reasons: list[str] = []

    if supports_primary:
        overlap = sorted(tags & primary_tags)[:4]
        reasons.append("Supports primary strategy via: " + ", ".join(overlap))
    if supports_secondary:
        overlap = sorted(tags & secondary_tags)[:4]
        reasons.append("Supports secondary strategy via: " + ", ".join(overlap))

    core_role_tags = {
        "ramp", "mana_rock", "mana_dork", "card_draw", "card_advantage", "targeted_removal",
        "board_wipe", "counterspell", "protection", "recursion", "tutor", "mana_source",
    }
    if tags & core_role_tags:
        reasons.append("Fills a generic Commander infrastructure role.")

    if supports_primary:
        plan_fit = "Primary plan support"
    elif supports_secondary:
        plan_fit = "Secondary plan support"
    elif tags & core_role_tags:
        plan_fit = "Support / infrastructure"
    elif "manual_review" in tags:
        plan_fit = "Manual review"
    else:
        plan_fit = "Possible off-plan or low-synergy"

    possible_off_plan = plan_fit == "Possible off-plan or low-synergy"
    if not reasons:
        reasons.append("No clear overlap with the detected primary/secondary strategy tags in this checkpoint.")

    return CardPlanFitEntry(
        card_name=card_entry.card_name,
        quantity=card_entry.quantity,
        plan_fit=plan_fit,
        supports_primary=supports_primary,
        supports_secondary=supports_secondary,
        possible_off_plan=possible_off_plan,
        reasons=reasons,
    )


def build_plan_fit_summary(card_roles: list[CardRoleEntry], strategy_summary: StrategySummary) -> PlanFitSummary:
    entries = [classify_card_plan_fit(entry, strategy_summary) for entry in card_roles]
    strong_synergy_cards = [entry for entry in entries if entry.supports_primary][:12]
    possible_off_plan_cards = [entry for entry in entries if entry.possible_off_plan][:12]
    return PlanFitSummary(
        entries=entries,
        strong_synergy_cards=strong_synergy_cards,
        possible_off_plan_cards=possible_off_plan_cards,
    )
