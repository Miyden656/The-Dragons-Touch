"""Combo view.

Combo awareness is NOT part of the standard analysis dict — the engine writes it
via combo_awareness.main_hook.write_optional_combo_awareness_artifacts as a
separate, opt-in artifact. Phase 3 therefore accepts an optional combo summary
and reports "not run" when it is absent (the honest default), adding an
uncertainty so the model knows not to claim the deck has/lacks combos.

A later phase wires the real DeckComboSummary in. The shape below is forward-
compatible: if a combo object is passed, we extract its findings defensively.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_list, as_str, attr, card_name_of, truncate

_FINDING_LIMIT = 12


def build_combo_view(combo_summary: Any | None) -> tuple[dict, bool]:
    """Return (view, available). available=False means combo awareness wasn't run."""
    if combo_summary is None:
        return (
            {
                "available": False,
                "note": "Combo awareness was not run for this deck. Do not assert the "
                "deck contains or lacks combos based on memory.",
                "findings": [],
            },
            False,
        )

    findings_raw = as_list(
        attr(combo_summary, "findings", attr(combo_summary, "complete_combos"))
    )
    findings, _ = truncate(findings_raw, _FINDING_LIMIT)
    return (
        {
            "available": True,
            "note": "",
            "findings": [_finding(f) for f in findings],
        },
        True,
    )


def _finding(f: Any) -> dict:
    pieces = [card_name_of(p) for p in as_list(attr(f, "pieces", attr(f, "cards")))]
    return {
        "pieces": [p for p in pieces if p],
        "result": as_str(attr(f, "result", attr(f, "produces"))),
        "status": as_str(attr(f, "status")),
    }
