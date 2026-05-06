"""Replacement category and role-need helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from analysis.strategy_scoring import StrategySummary

@dataclass(slots=True)
class ReplacementNeedSummary:
    priority_categories: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def build_replacement_need_summary(role_counts: Counter[str], strategy_summary: StrategySummary, deck_card_count: int) -> ReplacementNeedSummary:
    categories: list[str] = []
    notes: list[str] = []

    if deck_card_count < 100:
        missing = 100 - deck_card_count
        categories.append("Build / complete deck to 100")
        categories.append("Addition: reach 100 cards before cutting")
        notes.append(f"Deck is short {missing} card(s); prioritize additions before cuts unless intentionally rebuilding.")

    if role_counts.get("ramp", 0) < 8:
        categories.append("More ramp")
    if role_counts.get("card_draw", 0) + role_counts.get("card_advantage", 0) < 8:
        categories.append("More card draw")
    if role_counts.get("targeted_removal", 0) < 5:
        categories.append("More targeted removal")
    if role_counts.get("board_wipe", 0) < 2:
        categories.append("More board wipes")
    if role_counts.get("protection", 0) < 3:
        categories.append("More protection")

    primary = strategy_summary.primary_strategy.lower()
    if "aristocrats" in primary or "sacrifice" in primary:
        categories.extend(["More sacrifice outlets", "More token production", "More recursion"])
    if "landfall" in primary or "lands" in primary:
        categories.extend(["More lands", "More land ramp", "More extra land drops", "More land recursion"])
    if "tokens" in primary:
        categories.extend(["More token production", "More combat finishers", "More protection"])
    if "spellslinger" in primary:
        categories.extend(["More instant/sorcery density", "More card selection", "More spell payoff"])
    if "typal" in primary:
        categories.extend(["More tribal density", "More typal payoff", "More on-type creatures"])
    if "toughness" in primary or "defender" in primary:
        categories.extend(["More toughness-matters payoffs", "More defender support"])

    # Preserve order while removing duplicates.
    seen: set[str] = set()
    deduped = []
    for category in categories:
        if category not in seen:
            deduped.append(category)
            seen.add(category)

    if not deduped:
        notes.append("No urgent generic replacement category was detected by the checkpoint heuristics.")
    else:
        notes.append("Replacement categories are role needs, not exact card recommendations yet.")

    return ReplacementNeedSummary(priority_categories=deduped[:12], notes=notes)
