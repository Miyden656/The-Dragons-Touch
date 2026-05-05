"""Protected-card identification.

Round 6 cleanup goal:
- Separate cards that should not be casually cut from cut scoring.
- Keep protection based on plan/context, not exact card-name hardcoding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deck_helper.analysis.plan_fit import CardPlanFitEntry, PlanFitSummary
from deck_helper.analysis.role_tags import CardRoleEntry
from deck_helper.legality.commander_detection import CommandZoneSummary

PROTECTED_ROLE_TAGS = {
    "commander_protection", "protection", "commander_resource_support",
    "primary_plan_support", "direct_commander_support", "commander_enabler",
    "commander_payoff", "win_condition", "free_sacrifice_outlet",
    "sacrifice_outlet", "recursion", "landfall", "landfall_payoff",
    "typal_density_piece", "tribal_payoff", "toughness_payoff",
    "defender_payoff", "blink_flicker", "spell_payoff", "death_trigger_payoff",
}

CORE_INFRASTRUCTURE_TAGS = {
    "ramp", "mana_rock", "mana_dork", "card_draw", "card_advantage",
    "targeted_removal", "board_wipe", "counterspell", "mana_source",
}

@dataclass(slots=True)
class ProtectedCardEntry:
    card_name: str
    quantity: int
    protection_level: str
    reasons: list[str] = field(default_factory=list)


def build_protected_cards(
    card_roles: list[CardRoleEntry],
    plan_fit_summary: PlanFitSummary,
    command_zone: CommandZoneSummary,
) -> list[ProtectedCardEntry]:
    plan_fit_by_name: dict[str, CardPlanFitEntry] = {entry.card_name: entry for entry in plan_fit_summary.entries}
    protected: list[ProtectedCardEntry] = []
    commander_names = set(command_zone.commander_name_set)

    for role_entry in card_roles:
        tags = set(role_entry.detected_roles)
        reasons: list[str] = []
        level = ""

        if role_entry.card_name in commander_names:
            protected.append(ProtectedCardEntry(role_entry.card_name, role_entry.quantity, "core", ["Command-zone card / commander."]))
            continue

        plan_entry = plan_fit_by_name.get(role_entry.card_name)
        if plan_entry and plan_entry.supports_primary:
            level = "high"
            reasons.append("Supports the detected primary strategy.")
        if tags & PROTECTED_ROLE_TAGS:
            level = level or "medium"
            reasons.append("Has role tags that often represent engine, payoff, protection, or win-condition support: " + ", ".join(sorted(tags & PROTECTED_ROLE_TAGS)[:5]))
        if tags & CORE_INFRASTRUCTURE_TAGS and plan_entry and plan_entry.plan_fit == "Support / infrastructure":
            level = level or "low"
            reasons.append("Fills basic Commander infrastructure; only cut if role balance is overfilled or replacement is clearly better.")

        if level:
            protected.append(ProtectedCardEntry(role_entry.card_name, role_entry.quantity, level, reasons))

    protection_rank = {"core": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(protected, key=lambda entry: (protection_rank.get(entry.protection_level, 9), entry.card_name))
