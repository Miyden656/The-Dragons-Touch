"""Deck-size and cut-pressure summary helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from config import RuntimeConfig
from cuts.replaceability import ReplaceabilityEntry

@dataclass(slots=True)
class CutPressureSummary:
    deck_card_count: int
    required_cuts: int
    short_cards: int
    optional_cut_target: int
    cut_mode: str
    status: str
    notes: list[str] = field(default_factory=list)


def build_cut_pressure_summary(deck_card_count: int, runtime_config: RuntimeConfig, replaceability_entries: list[ReplaceabilityEntry]) -> CutPressureSummary:
    required_cuts = max(0, deck_card_count - 100)
    short_cards = max(0, 100 - deck_card_count)
    cut_config = runtime_config.cut_depth_config or {}
    optional_cut_target = int(cut_config.get("optional_cut_target", 5) or 0)
    cut_mode = str(cut_config.get("mode", "normal"))
    notes: list[str] = []

    if deck_card_count > 100:
        status = "Over 100 — required cuts needed"
        notes.append(f"Deck is over Commander size by {required_cuts} card(s). Required cuts are mandatory for legality.")
        confident = [entry for entry in replaceability_entries if entry.score >= 4 and not entry.protected]
        if len(confident) < required_cuts:
            notes.append("Confident cut candidates are fewer than required cuts; remaining cuts should be manual review instead of forced bad advice.")
    elif deck_card_count < 100:
        status = "Under 100 — addition-first"
        notes.append(f"Deck is short {short_cards} card(s). Do not produce required cuts unless the user is intentionally rebuilding.")
        optional_cut_target = 0 if runtime_config.review_direction == "build_up" else optional_cut_target
    else:
        status = "Legal 100-card deck — optional optimization only"
        notes.append("Legal does not mean optimized. Optional cuts are review candidates, not mandatory cuts.")

    if runtime_config.review_direction == "build_up":
        notes.append("Build-up mode is active; prioritize addition/completion needs over cuts.")

    return CutPressureSummary(
        deck_card_count=deck_card_count,
        required_cuts=required_cuts,
        short_cards=short_cards,
        optional_cut_target=optional_cut_target,
        cut_mode=cut_mode,
        status=status,
        notes=notes,
    )
