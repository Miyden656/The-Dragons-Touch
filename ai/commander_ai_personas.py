"""Persona prompt rendering.

This is a thin adapter: it turns the engine's persona data (the philosophy_context
dict, already serialized into CommanderAIContext.persona) into an instruction block
for the model. It does NOT define persona behavior — the engine's
deck_building_philosophies module owns the 18 profiles and their protect/review/
replacement bias. We only present that bias to the model.

VOICE is presentation-only and lives in the editable asset ai/prompts/persona_voices.md
(distilled from the design doc): a per-guide lexicon + example sentence + phrases to
avoid, keyed by the engine's canonical persona key. It shapes wording, never priorities
— the protect/review/prefer bias below is the only thing that steers the review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.context.safe_access import as_list, as_str

_VOICE_ASSET_PATH = Path(__file__).resolve().parent / "prompts" / "persona_voices.md"
_VOICE_CACHE: dict[str, dict[str, str]] | None = None


def render_persona_block(persona: dict | None) -> str:
    """Render the PERSONA instruction block from a persona view dict.

    Tolerant of a missing/partial persona: falls back to a neutral 'balanced' frame
    so assembly never fails.
    """
    persona = persona or {}
    key = as_str(persona.get("key"), "balanced_unknown")
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

    lines.extend(_voice_block(key, own_tone, family_tone, family_label))

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


def _load_voice_profiles() -> dict[str, dict[str, str]]:
    """Parse ai/prompts/persona_voices.md into {key: {field: value}}.

    Blocks start with `### key: <key>`; within a block each `Field: value` line is
    captured (Guide / Essence / Vocabulary / Sounds like / Avoid). Cached after first
    read. Any failure (missing/garbled file) degrades to an empty map so the caller
    falls back to the engine tone string — voice is enrichment, never load-bearing.
    """
    global _VOICE_CACHE
    if _VOICE_CACHE is not None:
        return _VOICE_CACHE

    profiles: dict[str, dict[str, str]] = {}
    field_map = {
        "guide": "guide",
        "essence": "essence",
        "vocabulary": "vocabulary",
        "sounds like": "sounds_like",
        "avoid": "avoid",
    }
    try:
        text = _VOICE_ASSET_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        _VOICE_CACHE = profiles
        return profiles

    current_key: str | None = None
    current: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("### key:"):
            if current_key:
                profiles[current_key] = current
            current_key = line[len("### key:"):].strip()
            current = {}
            continue
        if current_key is None or ":" not in line:
            continue
        label, _, value = line.partition(":")
        field = field_map.get(label.strip().lower())
        if field:
            current[field] = value.strip()
    if current_key:
        profiles[current_key] = current

    _VOICE_CACHE = profiles
    return profiles


def _voice_block(key: str, own_tone: str, family_tone: str, family_label: str) -> list[str]:
    """Render the Voice lines for the persona block.

    Prefers the distilled voice profile (lexicon + example + avoid) from the asset,
    blended over the family register the engine supplies. Falls back to the thin
    engine tone-blend when no profile exists for this key."""
    voice = _load_voice_profiles().get(key)
    if not voice:
        line = _voice_line(own_tone, family_tone, family_label)
        return [line] if line else []

    essence = voice.get("essence", "")
    vocabulary = voice.get("vocabulary", "")
    sounds_like = voice.get("sounds_like", "")
    avoid = voice.get("avoid", "")

    lines = ["Voice — how this guide speaks:"]
    if family_tone and family_label and essence:
        lines.append(
            f"- Register: the {family_label} family ({family_tone}); within it, this "
            f"guide's own voice is — {essence}"
        )
    elif family_tone and family_label:
        lines.append(f"- Register: the {family_label} family ({family_tone}).")
    elif essence:
        lines.append(f"- Register: {essence}")
    if vocabulary:
        lines.append(
            f"- Signature vocabulary (weave in naturally; don't force every term): {vocabulary}"
        )
    if sounds_like:
        lines.append(f"- Sounds like: {sounds_like}")
    if avoid:
        lines.append(f"- Avoid sounding like: {avoid}")
    return lines


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
