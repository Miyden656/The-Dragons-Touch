"""Possible cut review builder."""

from __future__ import annotations

from dataclasses import dataclass, field

from deck_helper.cuts.cut_pressure import CutPressureSummary
from deck_helper.cuts.replaceability import ReplaceabilityEntry

@dataclass(slots=True)
class PossibleCutReviewSummary:
    required_cut_candidates: list[ReplaceabilityEntry] = field(default_factory=list)
    optional_cut_candidates: list[ReplaceabilityEntry] = field(default_factory=list)
    manual_review_candidates: list[ReplaceabilityEntry] = field(default_factory=list)
    playtest_first_candidates: list[ReplaceabilityEntry] = field(default_factory=list)
    protected_from_cut: list[ReplaceabilityEntry] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def build_possible_cut_review(cut_pressure: CutPressureSummary, replaceability_entries: list[ReplaceabilityEntry]) -> PossibleCutReviewSummary:
    available = [entry for entry in replaceability_entries if not entry.protected]
    protected = [entry for entry in replaceability_entries if entry.protected]
    confident = [entry for entry in available if entry.score >= 4 and entry.cut_confidence in {"Medium", "High"}]
    manual = [entry for entry in available if 1 <= entry.score < 4 or entry.cut_type == "Possible Manual Review"]
    playtest = [entry for entry in available if entry.score <= 0 and entry.cut_confidence == "Low"]

    required: list[ReplaceabilityEntry] = []
    optional: list[ReplaceabilityEntry] = []
    notes: list[str] = ["These are review candidates, not guaranteed cuts."]

    if cut_pressure.required_cuts > 0:
        required = confident[:cut_pressure.required_cuts]
        if len(required) < cut_pressure.required_cuts:
            notes.append(f"Only {len(required)} confident required cut candidate(s) found for {cut_pressure.required_cuts} required cut(s). Remaining cuts need manual review.")
        optional = confident[cut_pressure.required_cuts:cut_pressure.required_cuts + cut_pressure.optional_cut_target]
    elif cut_pressure.short_cards > 0:
        notes.append("Deck is under 100 cards; no required cut candidates are produced in this checkpoint.")
    else:
        optional = confident[:cut_pressure.optional_cut_target]

    return PossibleCutReviewSummary(
        required_cut_candidates=required,
        optional_cut_candidates=optional,
        manual_review_candidates=manual[:10],
        playtest_first_candidates=playtest[:8],
        protected_from_cut=protected[:12],
        notes=notes,
    )
