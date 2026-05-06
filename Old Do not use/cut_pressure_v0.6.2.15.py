"""Deck-size and cut-pressure summary helpers.

Patch Batch 4 cleanup:
- Keep required legality cuts separate from optional tuning.
- Avoid forcing weak advice when confident candidates are insufficient.
- Make build-up mode explicitly addition-first.
"""

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


def _confident_cut_candidates(entries: list[ReplaceabilityEntry]) -> list[ReplaceabilityEntry]:
    return [
        entry for entry in entries
        if entry.score >= 4
        and not entry.protected
        and entry.cut_confidence in {"Medium", "High"}
        and not entry.cut_type.startswith("Protected")
    ]


def build_cut_pressure_summary(deck_card_count: int, runtime_config: RuntimeConfig, replaceability_entries: list[ReplaceabilityEntry]) -> CutPressureSummary:
    required_cuts = max(0, deck_card_count - 100)
    short_cards = max(0, 100 - deck_card_count)
    cut_config = runtime_config.cut_depth_config or {}
    optional_cut_target = int(cut_config.get("optional_cut_target", 5) or 0)
    cut_mode = str(cut_config.get("mode", "normal"))
    notes: list[str] = []

    if runtime_config.review_direction == "build_up":
        # Build-up reports may still include optional optimization language in the
        # user-guided prompt, but the code should not produce cut pressure first.
        optional_cut_target = 0 if deck_card_count <= 100 else optional_cut_target

    if deck_card_count > 100:
        status = "Over 100 — required cuts needed"
        notes.append(f"Deck is over Commander size by {required_cuts} card(s). Required cuts are mandatory for legality.")
        notes.append("Required cuts are legality fixes first; optional tuning should be treated separately.")
        confident = _confident_cut_candidates(replaceability_entries)
        if len(confident) < required_cuts:
            notes.append("Confident cut candidates are fewer than required cuts; remaining cuts should be manual review instead of forced bad advice.")
    elif deck_card_count < 100:
        status = "Under 100 — addition-first"
        notes.append(f"Deck is short {short_cards} card(s). Prioritize additions before cuts unless the user is intentionally rebuilding.")
        optional_cut_target = 0
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
