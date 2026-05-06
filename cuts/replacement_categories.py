"""Replacement category and role-need helpers.

Patch Batch 4 cleanup:
- Replacement needs should be based on role gaps relative to the deck plan, not
  generic Commander defaults only.
- Avoid misleading categories like more board wipes in proactive creature decks
  unless the shortage is severe.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from analysis.strategy_scoring import StrategySummary


@dataclass(slots=True)
class ReplacementNeedSummary:
    priority_categories: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _add(categories: list[str], *values: str) -> None:
    for value in values:
        if value and value not in categories:
            categories.append(value)


def _is_proactive_creature_strategy(primary: str) -> bool:
    primary = primary.lower()
    return any(token in primary for token in [
        "typal", "token", "go-wide", "go-tall", "combat", "stompy", "creature", "mutate",
        "equipment", "voltron", "counters",
    ])


def _is_control_or_slow_setup_strategy(primary: str, secondary: str) -> bool:
    joined = f"{primary} {secondary}".lower()
    return any(token in joined for token in ["control", "superfriends", "pillowfort", "slow alternate", "stax"])


def build_replacement_need_summary(role_counts: Counter[str], strategy_summary: StrategySummary, deck_card_count: int) -> ReplacementNeedSummary:
    categories: list[str] = []
    notes: list[str] = []
    primary = strategy_summary.primary_strategy.lower()
    secondary = strategy_summary.secondary_strategy.lower()
    land_count = role_counts.get("land", 0)
    ramp_count = role_counts.get("ramp", 0) + role_counts.get("land_ramp", 0)
    draw_count = role_counts.get("card_draw", 0) + role_counts.get("card_advantage", 0)
    removal_count = role_counts.get("targeted_removal", 0) + role_counts.get("repeatable_removal", 0)
    wipe_count = role_counts.get("board_wipe", 0)
    protection_count = role_counts.get("protection", 0) + role_counts.get("commander_protection", 0)

    if deck_card_count < 100:
        missing = 100 - deck_card_count
        _add(categories, "Build / complete deck to 100", "Addition: reach 100 cards before cutting")
        notes.append(f"Deck is short {missing} card(s); prioritize additions before cuts unless intentionally rebuilding.")

    # Generic role gaps, with more context-sensitive thresholds.
    if ramp_count < 8:
        _add(categories, "More ramp")
    if draw_count < 8:
        _add(categories, "More card draw")
    if removal_count < 5:
        _add(categories, "More targeted removal")

    if wipe_count < 2:
        if _is_control_or_slow_setup_strategy(primary, secondary):
            _add(categories, "More board wipes")
        elif _is_proactive_creature_strategy(primary) and wipe_count == 0:
            _add(categories, "More table-stabilizing interaction")
            notes.append("Proactive creature decks may prefer asymmetrical wipes, protection, or flexible interaction over generic board wipes.")
        elif not _is_proactive_creature_strategy(primary):
            _add(categories, "More board wipes")

    if protection_count < 3:
        _add(categories, "More protection")

    # Strategy-aware categories.
    if "aristocrats" in primary or "sacrifice" in primary:
        _add(categories, "More sacrifice outlets", "More token production", "More recursion", "More death payoffs")

    if "landfall" in primary or "lands" in primary:
        if land_count < 38 and deck_card_count >= 100:
            _add(categories, "More lands")
        _add(categories, "More land ramp", "More extra land drops", "More land recursion", "More landfall payoff")

    if "dragon typal" in primary:
        if role_counts.get("dragon_typal", 0) < 25:
            _add(categories, "More Dragon density")
        _add(categories, "More Dragon payoff", "More copy-token payoff", "More commander protection")

    elif "typal" in primary:
        if role_counts.get("typal_density_piece", 0) < 28:
            _add(categories, "More typal density")
        _add(categories, "More typal payoff", "More on-type role players")

    if "token combat" in primary or "tokens" in primary:
        _add(categories, "More token production", "More combat finishers", "More board protection")

    if "go-wide-go-tall" in primary or "go-tall" in primary or "combat" in primary:
        _add(categories, "More combat payoff", "More evasion/trample", "More protection")

    if "spellslinger" in primary:
        _add(categories, "More instant/sorcery density", "More card selection", "More spell payoff")

    if "mutate" in primary or "creature stack" in primary:
        _add(categories, "More mutate enablers", "More mutate payoff", "More protection for stacked creatures")

    if "graveyard" in primary:
        _add(categories, "More graveyard setup", "More recursion", "More protection from graveyard hate")

    if "draw-punisher" in primary or "wheels" in primary or "group slug" in primary:
        _add(categories, "More draw-punisher payoff", "More wheel effects", "More table-damage protection")

    if "toughness" in primary or "defender" in primary:
        _add(categories, "More toughness-matters payoffs", "More defender support")

    if not categories:
        notes.append("No urgent generic replacement category was detected by the checkpoint heuristics.")
    else:
        notes.append("Replacement categories are role needs, not exact card recommendations yet.")

    return ReplacementNeedSummary(priority_categories=categories[:12], notes=notes)
