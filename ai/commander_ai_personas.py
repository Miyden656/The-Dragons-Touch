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
    own_tone = as_str(persona.get("tone"))
    family_tone = as_str(persona.get("family_tone"))
    family_label = as_str(persona.get("family_label"))
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

    voice = _voice_line(own_tone, family_tone, family_label)
    if voice:
        lines.append(voice)

    lines.append("")
    lines.append("Let this lens shape BOTH your priorities and your voice:")
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
        "- Speak in this persona's voice (see Voice above) — let it color your wording and "
        "attitude. Stay a practical deck reviewer; don't theatrically role-play a named character."
    )
    return "\n".join(lines)


def _voice_line(own_tone: str, family_tone: str, family_label: str) -> str:
    """Blend the family register with the persona's own tone: 'same family, own
    way of speaking'. Falls back gracefully when either piece is missing."""
    if own_tone and family_tone and family_label:
        return (
            f"Voice: speak in the {family_label} family register ({family_tone}); "
            f"within that, this persona's own voice is {own_tone}."
        )
    if own_tone:
        return f"Voice: speak in a register that is {own_tone}."
    if family_tone:
        return f"Voice: speak in a register that is {family_tone}."
    return ""


def _bias_line(values: Any, limit: int = 6) -> str:
    items = [as_str(v) for v in as_list(values) if as_str(v)]
    return ", ".join(items[:limit])
