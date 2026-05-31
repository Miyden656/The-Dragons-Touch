"""Strategy view.

Consumes: strategy_summary (StrategySummary), plan_fit_summary (PlanFitSummary).
Surfaces the detected plan, confidence, supporting cards, and off-plan cards so
the model explains the deck instead of inventing a strategy.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_list, as_str, attr, card_name_of, truncate

_CANDIDATE_LIMIT = 6
_SYNERGY_LIMIT = 20
_OFF_PLAN_LIMIT = 20


def build_strategy_view(strategy_summary: Any, plan_fit_summary: Any) -> tuple[dict, dict]:
    """Return (view, truncation_notes)."""
    drops: dict[str, int] = {}

    candidates_raw = as_list(attr(strategy_summary, "candidates"))
    candidates, dropped = truncate(candidates_raw, _CANDIDATE_LIMIT)
    if dropped:
        drops["strategy.candidates"] = dropped

    synergy_raw = as_list(attr(plan_fit_summary, "strong_synergy_cards"))
    synergy, dropped = truncate(synergy_raw, _SYNERGY_LIMIT)
    if dropped:
        drops["strategy.strong_synergy_cards"] = dropped

    off_plan_raw = as_list(attr(plan_fit_summary, "possible_off_plan_cards"))
    off_plan, dropped = truncate(off_plan_raw, _OFF_PLAN_LIMIT)
    if dropped:
        drops["strategy.possible_off_plan_cards"] = dropped

    view = {
        "primary_strategy": as_str(attr(strategy_summary, "primary_strategy"), "Undetermined"),
        "secondary_strategy": as_str(attr(strategy_summary, "secondary_strategy")),
        "confidence": as_str(attr(strategy_summary, "confidence"), "unknown"),
        "warnings": [as_str(w) for w in as_list(attr(strategy_summary, "warnings"))],
        "synergy_packages": [as_str(p) for p in as_list(attr(strategy_summary, "core_synergy_packages"))],
        "candidates": [_candidate(c) for c in candidates],
        "strong_synergy_cards": [card_name_of(c) for c in synergy if card_name_of(c)],
        "possible_off_plan_cards": [_off_plan(c) for c in off_plan],
    }
    return view, drops


def _candidate(c: Any) -> dict:
    return {
        "name": as_str(attr(c, "name")),
        "score": attr(c, "score"),
        "layer": as_str(attr(c, "layer")),
        "commander_support": as_str(attr(c, "commander_support")),
        "gate_passed": bool(attr(c, "gate_passed", False)),
    }


def _off_plan(c: Any) -> dict:
    return {
        "card": card_name_of(c),
        "reasons": [as_str(r) for r in as_list(attr(c, "reasons"))][:3],
    }
