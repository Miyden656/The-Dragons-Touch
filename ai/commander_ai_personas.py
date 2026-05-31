"""Persona prompt rendering.

This is a thin adapter: it turns the engine's persona data (the philosophy_context
dict, already serialized into CommanderAIContext.persona) into an instruction block
for the model. It does NOT define persona behavior — the engine's
deck_building_philosophies module owns the 18 profiles and their protect/review/
replacement bias. We only present that bias to the model.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_list, as_str


def render_persona_block(persona: dict | None) -> str:
    """Render the PERSONA instruction block from a persona view dict.

    Tolerant of a missing/partial persona: falls back to a neutral 'balanced' frame
    so assembly never fails.
    """
    persona = persona or {}
    label = as_str(persona.get("label"), "Balanced / Unknown")
    guide_name = as_str(persona.get("guide_name"))
    guide_role = as_str(persona.get("guide_role"), "Guide")
    core_question = as_str(persona.get("core_question"), "What does this deck want to do?")
    rules = as_str(persona.get("rules_summary"))
    protect = _bias_line(persona.get("protect_bias"))
    review = _bias_line(persona.get("review_bias"))
    prefer = _bias_line(persona.get("replacement_bias"))

    guide_intro = f"{guide_name} — {guide_role}" if guide_name else guide_role

    lines = [
        "## Persona (deck-building philosophy)",
        f"Lens: {label}",
        f"Guide frame: {guide_intro}",
        f"Core question: {core_question}",
    ]
    if rules:
        lines.append(f"How to apply this lens: {rules}")
    lines.append("")
    lines.append("Let this lens shape your priorities (not just your wording):")
    if protect:
        lines.append(f"- Protect / lower cut pressure for: {protect}.")
    if review:
        lines.append(f"- Review more carefully / question: {review}.")
    if prefer:
        lines.append(f"- Prefer recommendations that support: {prefer}.")
    lines.append(
        "- Pilot override: the user's stated intent and any user-named pet cards beat "
        "this lens when they conflict."
    )
    lines.append(
        "- Introduce the guide/lens briefly once, then act as a practical deck reviewer "
        "— do not role-play the guide as a character."
    )
    return "\n".join(lines)


def _bias_line(values: Any, limit: int = 6) -> str:
    items = [as_str(v) for v in as_list(values) if as_str(v)]
    return ", ".join(items[:limit])
