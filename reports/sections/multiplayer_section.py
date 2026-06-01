"""Multiplayer / Pod Value report section.

Renders the additive 4-player pod-value signal
(analysis/multiplayer_signal.MultiplayerValueSummary, exposed as
context["multiplayer_summary"]) as a human-readable report section.

Self-contained and defensive: a missing/None summary yields an empty string so
the section simply does not appear — it can never break the normal report.
"""

from __future__ import annotations

from typing import Any


def _g(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def build_multiplayer_report_section(context: dict[str, Any]) -> str:
    """Return the '## Multiplayer / Pod Value' markdown, or '' if unavailable."""
    try:
        ms = (context or {}).get("multiplayer_summary")
    except Exception:
        ms = None
    if ms is None:
        return ""

    lines: list[str] = ["", "## Multiplayer / Pod Value", ""]
    lines.append(
        "> Verified 4-player pod facts derived from the deck's role tags. These are "
        "observations, not edits: in a multiplayer game the value of sweepers, "
        "single-target answers, and table-wide pressure differs from 1v1."
    )
    lines.append("")

    # --- Interaction profile ---
    lines.append("### Interaction Profile")
    lines.extend([
        f"- Board wipes (sweepers): {_g(ms, 'sweeper_count', 0)}",
        f"- Single-target removal: {_g(ms, 'spot_removal_count', 0)}",
        f"- Counterspells: {_g(ms, 'counterspell_count', 0)}",
        f"- Total interaction: {_g(ms, 'total_interaction', 0)} "
        f"({_g(ms, 'instant_speed_interaction_count', 0)} instant-speed)",
        f"- Interaction reach: {_g(ms, 'interaction_reach_band', 'none')}",
    ])

    # --- Table reach ---
    lines.append("")
    lines.append("### Table Reach")
    lines.extend([
        f"- Table-wide pressure sources: {_g(ms, 'table_wide_pressure_count', 0)}",
        f"- Single-target pressure sources: {_g(ms, 'single_target_pressure_count', 0)}",
        f"- Closing reach: {_g(ms, 'reach_band', 'none')}",
    ])

    # --- Politics ---
    lines.append("")
    lines.append("### Political Presence")
    lines.extend([
        f"- Goad effects: {_g(ms, 'goad_count', 0)}",
        f"- Pillowfort / attack-deterrents: {_g(ms, 'pillowfort_count', 0)}",
        f"- Overall presence: {_g(ms, 'political_presence_band', 'none')}",
    ])

    # --- Archenemy / resilience ---
    lines.append("")
    lines.append("### Threat Profile & Resilience")
    lines.extend([
        f"- Archenemy / threat density: {_g(ms, 'archenemy_risk_band', 'low')} "
        f"(score {_g(ms, 'threat_density', 0)})",
        f"- Creatures: {_g(ms, 'creature_count', 0)} "
        f"(reliance: {_g(ms, 'creature_reliance_band', 'low')})",
        f"- Recursion: {_g(ms, 'recursion_count', 0)}, "
        f"protection: {_g(ms, 'protection_count', 0)}",
        f"- Board-wipe resilience: {_g(ms, 'wipe_resilience_band', 'resilient')}",
    ])

    # --- Plain-language facts ---
    facts = _g(ms, "facts", []) or []
    if facts:
        lines.append("")
        lines.append("### Pod Notes")
        for fact in facts:
            lines.append(f"- {fact}")

    return "\n".join(lines)
