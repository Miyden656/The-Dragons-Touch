"""Bracket and table-fit pressure analysis.

Round 6 cleanup goal:
- Keep bracket pressure separate from strategy identity and cut recommendations.
- Produce structured pressure notes that cuts/reports can consume later.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from deck_helper.analysis.role_tags import CardRoleEntry, RoleAnalysisSummary

@dataclass(slots=True)
class BracketPressureCard:
    card_name: str
    quantity: int
    pressure_type: str
    reason: str

@dataclass(slots=True)
class BracketAnalysisSummary:
    estimated_bracket: str
    pressure_level: str
    pressure_cards: list[BracketPressureCard] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    role_pressure_counts: Counter[str] = field(default_factory=Counter)


def classify_bracket_pressure_card(entry: CardRoleEntry) -> BracketPressureCard | None:
    tags = set(entry.detected_roles)
    if "high_bracket_pressure" in tags:
        return BracketPressureCard(entry.card_name, entry.quantity, "High bracket pressure", "Role tags indicate a high-power/table-fit pressure card.")
    if "fast_mana" in tags:
        return BracketPressureCard(entry.card_name, entry.quantity, "Fast mana pressure", "Fast mana can raise speed and table expectations.")
    if "efficient_tutor" in tags or "combo_tutor" in tags:
        return BracketPressureCard(entry.card_name, entry.quantity, "Tutor pressure", "Efficient tutors increase consistency and can raise bracket expectations.")
    if "free_interaction" in tags or "free_counterspell" in tags:
        return BracketPressureCard(entry.card_name, entry.quantity, "Free interaction pressure", "Free interaction is a higher-power signal and should be disclosed in pregame talks.")
    if "bracket_pressure" in tags:
        return BracketPressureCard(entry.card_name, entry.quantity, "Bracket pressure", "This card is a table-fit modifier, not an automatic cut.")
    return None


def estimate_bracket_from_pressure(role_counts: Counter[str], pressure_count: int) -> tuple[str, str, list[str]]:
    notes: list[str] = []
    high_pressure = role_counts.get("high_bracket_pressure", 0)
    fast_mana = role_counts.get("fast_mana", 0)
    tutors = role_counts.get("efficient_tutor", 0) + role_counts.get("combo_tutor", 0)
    free_interaction = role_counts.get("free_interaction", 0) + role_counts.get("free_counterspell", 0)
    combo_possible = role_counts.get("combo_piece_possible", 0)

    if high_pressure >= 4 or (fast_mana >= 3 and tutors >= 3 and combo_possible >= 2):
        notes.append("Pressure profile resembles optimized/high-power play. Do not call this cEDH unless pilot intent and full list support that label.")
        return "Bracket 4 pressure likely", "high", notes
    if pressure_count >= 4 or high_pressure >= 2 or tutors >= 3:
        notes.append("Several cards create table-fit pressure. This is a pregame discussion point before it is a cut recommendation.")
        return "Bracket 3–4 pressure possible", "medium", notes
    if pressure_count >= 1:
        notes.append("A small number of pressure cards are present. Track them separately from strategy and cuts.")
        return "Bracket 3 pressure possible", "low", notes
    notes.append("No major bracket-pressure signals were found by the current checkpoint heuristics.")
    return "Bracket 2–3 casual/upgraded range possible", "none", notes


def build_bracket_analysis(role_summary: RoleAnalysisSummary) -> BracketAnalysisSummary:
    pressure_cards: list[BracketPressureCard] = []
    pressure_counts: Counter[str] = Counter()
    for entry in role_summary.card_roles:
        pressure_entry = classify_bracket_pressure_card(entry)
        if pressure_entry:
            pressure_cards.append(pressure_entry)
            pressure_counts[pressure_entry.pressure_type] += entry.quantity

    estimated_bracket, pressure_level, notes = estimate_bracket_from_pressure(role_summary.role_counts, len(pressure_cards))
    notes.append("Bracket pressure is not primary strategy evidence and is not an automatic cut by itself.")
    return BracketAnalysisSummary(
        estimated_bracket=estimated_bracket,
        pressure_level=pressure_level,
        pressure_cards=pressure_cards,
        notes=notes,
        role_pressure_counts=pressure_counts,
    )
