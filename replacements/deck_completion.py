"""Deck completion helpers for underfilled/build-up reviews.

Round 7 cleanup goal:
- Keep addition-first logic separate from cut-pressure logic.
- Produce structured completion notes that reports/prompts can reuse.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analysis.strategy_scoring import StrategySummary
from config import RuntimeConfig
from cuts.replacement_categories import ReplacementNeedSummary
from parsing.deck_parser import ParsedDeck


@dataclass(slots=True)
class DeckCompletionSummary:
    cards_needed: int
    build_up_mode: str
    build_up_label: str
    addition_first: bool
    priority_categories: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def build_deck_completion_summary(
    parsed_deck: ParsedDeck,
    runtime_config: RuntimeConfig,
    strategy_summary: StrategySummary,
    replacement_needs: ReplacementNeedSummary,
) -> DeckCompletionSummary:
    cards_needed = max(0, 100 - parsed_deck.deck_card_count)
    build_up_config = runtime_config.build_up_config or {}
    build_up_mode = str(build_up_config.get("mode", "not_applicable"))
    build_up_label = str(build_up_config.get("label", "Not applicable"))
    addition_first = cards_needed > 0 or runtime_config.review_direction == "build_up"
    notes: list[str] = []

    if cards_needed > 0:
        notes.append(f"Deck is short {cards_needed} card(s); prioritize additions before cuts unless intentionally rebuilding.")
    if runtime_config.review_direction == "build_up":
        notes.append(f"Build-up workflow active: {build_up_label}.")
    if strategy_summary.primary_strategy and strategy_summary.primary_strategy != "Manual Review / Primary Uncertain":
        notes.append(f"Additions should reinforce the current strategy read: {strategy_summary.primary_strategy}.")

    priority_categories = list(replacement_needs.priority_categories)
    if cards_needed > 0 and "Build / complete deck to 100" not in priority_categories:
        priority_categories.insert(0, "Build / complete deck to 100")

    return DeckCompletionSummary(
        cards_needed=cards_needed,
        build_up_mode=build_up_mode,
        build_up_label=build_up_label,
        addition_first=addition_first,
        priority_categories=priority_categories[:12],
        notes=notes,
    )
