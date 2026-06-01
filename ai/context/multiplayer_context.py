"""Multiplayer / pod-value view.

Consumes: multiplayer_summary (MultiplayerValueSummary from
analysis/multiplayer_signal.py). Surfaces the engine's verified 4-player pod
facts — interaction reach, table reach, political presence, archenemy risk, and
board-wipe resilience — so the model reasons about the pod on real numbers
instead of inventing them.

Like the other context builders, it ONLY reads (defensively) from the object the
engine already produced; it never recomputes or invents.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_int, as_list, as_str, attr, truncate

_FACTS_LIMIT = 12
_EXAMPLE_LIMIT = 6


def build_multiplayer_view(multiplayer_summary: Any) -> tuple[dict, dict]:
    """Return (view, truncation_notes)."""
    drops: dict[str, int] = {}

    facts_raw = [as_str(f) for f in as_list(attr(multiplayer_summary, "facts")) if as_str(f)]
    facts, dropped = truncate(facts_raw, _FACTS_LIMIT)
    if dropped:
        drops["multiplayer.facts"] = dropped

    examples_raw = attr(multiplayer_summary, "example_cards") or {}
    examples: dict[str, list[str]] = {}
    if isinstance(examples_raw, dict):
        for key, names in examples_raw.items():
            capped = [as_str(n) for n in as_list(names) if as_str(n)][:_EXAMPLE_LIMIT]
            if capped:
                examples[as_str(key)] = capped

    view = {
        "interaction": {
            "sweepers": as_int(attr(multiplayer_summary, "sweeper_count")),
            "spot_removal": as_int(attr(multiplayer_summary, "spot_removal_count")),
            "counterspells": as_int(attr(multiplayer_summary, "counterspell_count")),
            "total": as_int(attr(multiplayer_summary, "total_interaction")),
            "instant_speed": as_int(attr(multiplayer_summary, "instant_speed_interaction_count")),
            "reach_band": as_str(attr(multiplayer_summary, "interaction_reach_band"), "none"),
        },
        "table_reach": {
            "table_wide_sources": as_int(attr(multiplayer_summary, "table_wide_pressure_count")),
            "single_target_sources": as_int(attr(multiplayer_summary, "single_target_pressure_count")),
            "band": as_str(attr(multiplayer_summary, "reach_band"), "none"),
        },
        "politics": {
            "goad": as_int(attr(multiplayer_summary, "goad_count")),
            "pillowfort": as_int(attr(multiplayer_summary, "pillowfort_count")),
            "presence": as_str(attr(multiplayer_summary, "political_presence_band"), "none"),
        },
        "archenemy": {
            "threat_density": as_int(attr(multiplayer_summary, "threat_density")),
            "risk_band": as_str(attr(multiplayer_summary, "archenemy_risk_band"), "low"),
        },
        "resilience": {
            "creatures": as_int(attr(multiplayer_summary, "creature_count")),
            "recursion": as_int(attr(multiplayer_summary, "recursion_count")),
            "protection": as_int(attr(multiplayer_summary, "protection_count")),
            "creature_reliance": as_str(attr(multiplayer_summary, "creature_reliance_band"), "low"),
            "wipe_resilience": as_str(attr(multiplayer_summary, "wipe_resilience_band"), "resilient"),
        },
        "facts": facts,
        "example_cards": examples,
        "confidence": as_str(attr(multiplayer_summary, "confidence"), "low"),
    }
    return view, drops
