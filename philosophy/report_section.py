"""Philosophy Guide report-section formatter for The Dragon's Touch.

Version: v1.1.5

This module turns a PhilosophyProfile/runtime philosophy context into a reusable
markdown section for reports and prompts.

Important boundary:
- This module does not wire itself into report generation.
- This module does not change deck analysis behavior.
- This module does not apply cut pressure.
- This module does not modify UI behavior.

It only formats the philosophy guide section.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .philosophy_profile import PhilosophyProfile
from .persona_opening import get_persona_opening_mission
from .runtime_config_mapping import (
    RuntimePhilosophyContext,
    context_from_profile,
    context_from_runtime_config,
)


def _clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _is_named_enabled(persona_context: Mapping[str, Any]) -> bool:
    return bool(persona_context.get("named_guide_enabled") and persona_context.get("guide_name"))


def _guidance_paragraph(context: RuntimePhilosophyContext) -> str:
    profile = context.profile
    lens = context.lens_definition
    persona = context.persona_context

    selected_lens = _clean_text(profile.selected_lens, "Balanced / Unknown")
    short_guidance = _clean_text(persona.get("short_guidance"))
    parent = _clean_text(lens.get("parent_philosophy"), profile.parent_philosophy)
    primary_question = _clean_text(lens.get("primary_question"), persona.get("primary_question", ""))

    if selected_lens == "Balanced / Unknown":
        return (
            "No specific philosophy was selected, so this report uses a balanced exploratory lens. "
            "It should avoid strong assumptions, map the deck's natural direction, and flag cards "
            "that may need more user intent before they are judged harshly."
        )

    if _is_named_enabled(persona):
        guide_name = _clean_text(persona.get("guide_name"))
        guide_role = _clean_text(persona.get("guide_role"), "Guide")
        if short_guidance:
            return (
                f"{guide_name} guides this review through the {guide_role} lens. "
                f"{short_guidance} The review should still preserve legality, strategy, user constraints, "
                f"budget, bracket, and combo tolerance."
            )
        return (
            f"{guide_name} guides this review through the {guide_role} lens. "
            f"The main question is: {primary_question} "
            f"The review should still preserve legality, strategy, user constraints, budget, bracket, and combo tolerance."
        )

    if short_guidance:
        return (
            f"This review uses the {selected_lens} lens without a named guide. "
            f"{short_guidance} The review should still preserve legality, strategy, user constraints, "
            f"budget, bracket, and combo tolerance."
        )

    return (
        f"This review uses the {selected_lens} lens without a named guide. "
        f"The parent philosophy is {parent}, and the main question is: {primary_question} "
        f"The review should still preserve legality, strategy, user constraints, budget, bracket, and combo tolerance."
    )


def format_persona_opening(
    context: RuntimePhilosophyContext,
    *,
    include_pilot_authority: bool = True,
) -> str:
    """Format the player-facing persona opening greeting.

    This is the "Hey, I'm <guide>, let me guide you through your deck" line the
    normal report opens with. It is deterministic and presentation-only: the guide
    name/role come from the persona registry, the voiced mission line from
    persona_opening, and the pilot-authority reassurance is a fixed reminder that
    the user's intent — not the lens — has the final say.

    When the named-guide toggle is off, the greeting falls back to a lens-framed
    intro ("I'll guide this review through the <lens> lens.") so it still reads as a
    first-person guide rather than a developer banner.
    """
    persona = context.persona_context
    lens = _clean_text(context.profile.selected_lens, "Balanced / Unknown")
    mission = get_persona_opening_mission(lens)

    guide_name = _clean_text(persona.get("guide_name"))
    guide_role = _clean_text(persona.get("guide_role"))

    if guide_name:
        role_phrase = f"your {guide_role}" if guide_role else "your guide"
        intro = f"Hey, I'm {guide_name}, {role_phrase} for this review."
    else:
        intro = f"I'll guide this review through the {lens} lens."

    lines = [f"{intro} {mission}".strip()]
    if include_pilot_authority:
        lines.append("")
        lines.append(
            "> You stay in charge here — everything below is a review suggestion, and "
            "your stated intent and pet cards win whenever they conflict with this lens."
        )
    return "\n".join(lines).rstrip() + "\n"


def format_persona_opening_from_profile(
    profile: PhilosophyProfile,
    *,
    include_pilot_authority: bool = True,
) -> str:
    """Format the persona opening from an existing PhilosophyProfile."""
    return format_persona_opening(
        context_from_profile(profile),
        include_pilot_authority=include_pilot_authority,
    )


def format_persona_opening_from_runtime_config(
    config: Optional[Mapping[str, Any]],
    *,
    include_pilot_authority: bool = True,
) -> str:
    """Format the persona opening directly from runtime/UI config data."""
    return format_persona_opening(
        context_from_runtime_config(config),
        include_pilot_authority=include_pilot_authority,
    )


def format_philosophy_guide_section(
    context: RuntimePhilosophyContext,
    *,
    heading_level: int = 2,
    include_intensity: bool = False,
    include_notes: bool = False,
) -> str:
    """Format the Philosophy Guide section as markdown.

    Parameters
    ----------
    context:
        A RuntimePhilosophyContext from v1.1.4.
    heading_level:
        Markdown heading level. Defaults to 2, producing "## Philosophy Guide".
    include_intensity:
        If True, include the profile intensity.
    include_notes:
        If True, include pilot notes when present.

    Returns
    -------
    str
        A standalone markdown section.
    """
    level = max(1, min(int(heading_level), 6))
    heading = "#" * level

    profile = context.profile
    lens = context.lens_definition
    persona = context.persona_context

    selected_lens = _clean_text(profile.selected_lens, "Balanced / Unknown")
    parent = _clean_text(lens.get("parent_philosophy"), profile.parent_philosophy)
    primary_question = _clean_text(lens.get("primary_question"), persona.get("primary_question", ""))
    guide_role = _clean_text(persona.get("guide_role"), lens.get("guide_role", ""))

    lines = [
        f"{heading} Philosophy Guide",
        "",
        f"**Selected Lens:** {selected_lens}",
    ]

    if _is_named_enabled(persona):
        lines.append(f"**Guide:** {_clean_text(persona.get('guide_name'))}")

    if guide_role:
        lines.append(f"**Guide Role:** {guide_role}")

    lines.append(f"**Parent Philosophy:** {parent}")

    if primary_question:
        lines.append(f"**Primary Question:** {primary_question}")

    if include_intensity:
        lines.append(f"**Intensity:** {profile.intensity}")

    if include_notes and profile.pilot_notes:
        lines.append(f"**Pilot Notes:** {profile.pilot_notes}")

    lines.extend(["", _guidance_paragraph(context)])

    return "\n".join(lines).rstrip() + "\n"


def format_philosophy_guide_section_from_profile(
    profile: PhilosophyProfile,
    *,
    heading_level: int = 2,
    include_intensity: bool = False,
    include_notes: bool = False,
) -> str:
    """Format the guide section from an existing PhilosophyProfile."""
    return format_philosophy_guide_section(
        context_from_profile(profile),
        heading_level=heading_level,
        include_intensity=include_intensity,
        include_notes=include_notes,
    )


def format_philosophy_guide_section_from_runtime_config(
    config: Optional[Mapping[str, Any]],
    *,
    heading_level: int = 2,
    include_intensity: bool = False,
    include_notes: bool = False,
) -> str:
    """Format the guide section directly from runtime/UI config data."""
    return format_philosophy_guide_section(
        context_from_runtime_config(config),
        heading_level=heading_level,
        include_intensity=include_intensity,
        include_notes=include_notes,
    )


def philosophy_guide_section_preview(config: Optional[Mapping[str, Any]] = None) -> str:
    """Small convenience helper for manual preview/testing."""
    return format_philosophy_guide_section_from_runtime_config(config or {})
