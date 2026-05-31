"""Bracket / power-level view.

Consumes: bracket_summary (BracketAnalysisSummary), runtime_config (for the
user's intended bracket). Surfaces the engine's estimate and pressure cards so
the model never invents a power-level assessment.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_list, as_str, attr, truncate

_PRESSURE_LIMIT = 15


def build_bracket_view(bracket_summary: Any, runtime_config: Any) -> tuple[dict, dict]:
    drops: dict[str, int] = {}
    pressure_raw = as_list(attr(bracket_summary, "pressure_cards"))
    pressure, dropped = truncate(pressure_raw, _PRESSURE_LIMIT)
    if dropped:
        drops["bracket.pressure_cards"] = dropped

    view = {
        "estimated_bracket": as_str(attr(bracket_summary, "estimated_bracket"), "Unknown"),
        "intended_bracket": as_str(attr(runtime_config, "intended_bracket"), "Not specified"),
        "pressure_level": as_str(attr(bracket_summary, "pressure_level"), "Unknown"),
        "concerns": [as_str(n) for n in as_list(attr(bracket_summary, "notes"))],
        "pressure_cards": [
            {
                "card": as_str(attr(p, "card_name")),
                "pressure_type": as_str(attr(p, "pressure_type")),
                "reason": as_str(attr(p, "reason")),
            }
            for p in pressure
            if as_str(attr(p, "card_name"))
        ],
    }
    return view, drops
