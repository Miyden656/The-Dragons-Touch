"""Political archetype view.

Consumes: political_summary (PoliticalArchetypeSummary from
analysis/political_archetypes.py). Surfaces the engine's Section-3 political read
— primary/secondary political archetype, supporting packages, table dependency,
salt/reputation risk, and the political warnings — so the model coaches the deck
as a political plan on verified detection rather than inventing one.

Reads defensively only; never recomputes or invents.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_int, as_list, as_str, attr, truncate

_DETECTED_LIMIT = 8
_EXAMPLE_LIMIT = 6


def _archetype_view(d: Any) -> dict:
    return {
        "name": as_str(attr(d, "name")),
        "section": as_str(attr(d, "section")),
        "axis": as_str(attr(d, "axis")),
        "role": as_str(attr(d, "role")),
        "confidence": as_str(attr(d, "confidence"), "low"),
        "commander_support": as_str(attr(d, "commander_support"), "none"),
        "incentive_present": bool(attr(d, "incentive_present", False)),
        "protection_present": bool(attr(d, "protection_present", False)),
        "payoff_present": bool(attr(d, "payoff_present", False)),
        "inevitability_present": bool(attr(d, "inevitability_present", False)),
        "evidence": [as_str(e) for e in as_list(attr(d, "evidence"))][:6],
        "example_cards": [as_str(c) for c in as_list(attr(d, "example_cards")) if as_str(c)][:_EXAMPLE_LIMIT],
        "replacement_categories": [as_str(r) for r in as_list(attr(d, "replacement_categories")) if as_str(r)],
    }


def build_political_view(political_summary: Any) -> tuple[dict, dict]:
    """Return (view, truncation_notes)."""
    drops: dict[str, int] = {}

    primary = attr(political_summary, "primary")
    secondary = attr(political_summary, "secondary")

    detected_raw = as_list(attr(political_summary, "detected"))
    detected, dropped = truncate(detected_raw, _DETECTED_LIMIT)
    if dropped:
        drops["political.detected"] = dropped

    view = {
        "is_political": bool(attr(political_summary, "is_political", False)),
        "primary": _archetype_view(primary) if primary is not None else None,
        "secondary": _archetype_view(secondary) if secondary is not None else None,
        "detected": [_archetype_view(d) for d in detected],
        "table_dependency": as_str(attr(political_summary, "table_dependency"), "low"),
        "salt_risk": as_str(attr(political_summary, "salt_risk"), "low"),
        "reputation_modifier": as_str(attr(political_summary, "reputation_modifier"), "none"),
        "political_density": as_int(attr(political_summary, "political_density")),
        "confidence": as_str(attr(political_summary, "confidence"), "low"),
        "warnings": [as_str(w) for w in as_list(attr(political_summary, "warnings")) if as_str(w)],
        "cut_guidance": _cut_guidance_view(attr(political_summary, "cut_guidance")),
    }
    return view, drops


def _cut_guidance_view(cut_guidance: Any) -> dict:
    """§3.49 generic political cut rules, as plain string lists."""
    cg = cut_guidance if isinstance(cut_guidance, dict) else {}
    out: dict[str, list[str]] = {}
    for key in ("do_not_auto_cut", "raise_cut_pressure"):
        items = [as_str(i) for i in as_list(cg.get(key)) if as_str(i)]
        if items:
            out[key] = items
    return out
