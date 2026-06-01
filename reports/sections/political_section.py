"""Political / Pod Archetypes report section (Section 3).

Renders the additive political-archetype classification
(analysis/political_archetypes.PoliticalArchetypeSummary, exposed as
context["political_summary"]) using the §3.51 "Political Strategy Read" shape.

Self-contained and defensive: if no summary is present, or the deck is not
political, it returns '' so the section simply does not appear and can never
break the normal report.
"""

from __future__ import annotations

from typing import Any


def _g(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _archetype_line(d: Any) -> str:
    # NOTE: do NOT render "commander support: X" here. The normal report's
    # user-facing postprocessor (user_report_candidate_combo_cleanup) strips that
    # exact phrase as internal scoring jargon, which would leave a dangling comma.
    # Commander support still flows to the AI context via political_context.py.
    name = _g(d, "name", "Unknown")
    section = _g(d, "section", "")
    axis = _g(d, "axis", "")
    conf = _g(d, "confidence", "low")
    bits = f"{name} (sec {section})" if section else f"{name}"
    extra = f" - {axis}" if axis else ""
    return f"{bits}{extra} [confidence: {conf}]"


def build_political_report_section(context: dict[str, Any]) -> str:
    """Return the '## Political / Pod Archetypes' markdown, or '' if not political."""
    try:
        ps = (context or {}).get("political_summary")
    except Exception:
        ps = None
    if ps is None:
        return ""

    primary = _g(ps, "primary")
    detected = _g(ps, "detected", []) or []
    reputation = _g(ps, "reputation_modifier", "none")

    # Only render when there's something political to say.
    if primary is None and reputation == "none" and not detected:
        return ""

    lines: list[str] = ["", "## Political / Pod Archetypes", ""]
    lines.append(
        "> Additive Section-3 political read. This is a PARALLEL classification of "
        "how the deck manipulates the table (incentives, combat direction, "
        "deterrence, punishment) - it does not replace the strategy read above. "
        "Political cards are reviewed differently: do not auto-cut a deterrent or "
        "incentive that meaningfully supports the political plan."
    )
    lines.append("")

    # --- §3.51 Political Strategy Read ---
    secondary = _g(ps, "secondary")
    lines.append("### Political Strategy Read")
    if primary is not None:
        lines.append(f"- Primary political axis: {_archetype_line(primary)}")
    else:
        lines.append("- Primary political axis: none detected (only supporting packages)")
    if secondary is not None:
        lines.append(f"- Secondary political package: {_archetype_line(secondary)}")
    lines.extend([
        f"- Table dependency: {_g(ps, 'table_dependency', 'low')}",
        f"- Salt risk: {_g(ps, 'salt_risk', 'low')}",
        f"- Reputation modifier: {reputation}",
        f"- Political signal density: {_g(ps, 'political_density', 0)}",
    ])

    # --- Primary plan: the §3.54 formula components ---
    if primary is not None:
        lines.append("")
        lines.append("### How the Political Plan Holds Together")
        lines.extend([
            f"- Incentive / deterrence present: {'yes' if _g(primary, 'incentive_present') else 'no'}",
            f"- Protection present: {'yes' if _g(primary, 'protection_present') else 'no'}",
            f"- Payoff present: {'yes' if _g(primary, 'payoff_present') else 'no'}",
            f"- Inevitability / closing present: {'yes' if _g(primary, 'inevitability_present') else 'no'}",
        ])
        examples = _g(primary, "example_cards", []) or []
        if examples:
            lines.append(f"- Example cards: {', '.join(examples)}")

    # --- Supporting packages ---
    support_rows = [
        d for d in detected
        if _g(d, "role") in {"minor_package", "support", "manual_review", "modifier"}
    ]
    if support_rows:
        lines.append("")
        lines.append("### Supporting / Watch Packages")
        for d in support_rows[:8]:
            role = _g(d, "role", "")
            lines.append(f"- [{role}] {_archetype_line(d)}")

    # --- Cut & replacement guidance (§3.49 / §3.50) ---
    cut_guidance = _g(ps, "cut_guidance", {}) or {}
    repl_cats = _g(primary, "replacement_categories", []) if primary is not None else []
    if cut_guidance or repl_cats:
        lines.append("")
        lines.append("### Political Cut & Replacement Guidance")
        lines.append(
            "Political cards are reviewed differently from raw value. This is guidance "
            "for the pilot, not an automatic edit to the cut list above."
        )
        do_not_cut = (cut_guidance.get("do_not_auto_cut") if isinstance(cut_guidance, dict) else None) or []
        if do_not_cut:
            lines.append("- Do NOT auto-cut (when they support the plan):")
            for item in do_not_cut:
                lines.append(f"  - {item}")
        raise_pressure = (cut_guidance.get("raise_cut_pressure") if isinstance(cut_guidance, dict) else None) or []
        if raise_pressure:
            lines.append("- Raise cut pressure on:")
            for item in raise_pressure:
                lines.append(f"  - {item}")
        if repl_cats:
            pname = _g(primary, "name", "the primary archetype")
            lines.append(f"- Replacement categories for {pname} (categories, not specific cards):")
            for item in repl_cats:
                lines.append(f"  - {item}")

    # --- Warnings (§3.52) ---
    warnings = _g(ps, "warnings", []) or []
    if warnings:
        lines.append("")
        lines.append("### Political Warnings")
        for w in warnings:
            lines.append(f"- {w}")

    return "\n".join(lines)
