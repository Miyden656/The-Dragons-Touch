"""Philosophy prompt / AI handoff injection helpers for The Dragon's Touch.

Version: v1.1.10

This module formats philosophy context into a safe AI handoff block that can be
included in generated prompts.

Important boundary:
- This module does not change deck analysis behavior.
- This module does not choose cuts.
- This module does not score cards.
- This module does not recommend exact replacement cards.
- This module does not modify existing prompt generation by itself.
- This module only returns prompt text or payload dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .cut_language import get_cut_pressure_language_from_runtime_config
from .protected_language import get_protected_card_language_from_runtime_config
from .replacement_language import get_replacement_direction_language_from_runtime_config
from .report_section import format_philosophy_guide_section_from_runtime_config
from .runtime_config_mapping import context_from_runtime_config, runtime_config_to_report_context


PHILOSOPHY_HANDOFF_TITLE = "Philosophy / Persona Guidance"


@dataclass(frozen=True)
class PhilosophyPromptInjection:
    """Structured prompt-injection payload for AI handoff generation."""

    handoff_block: str
    guide_section: str
    boundary_block: str
    language_hints: str
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handoff_block": self.handoff_block,
            "guide_section": self.guide_section,
            "boundary_block": self.boundary_block,
            "language_hints": self.language_hints,
            "context": dict(self.context),
        }


def build_philosophy_prompt_boundary_block() -> str:
    """Return the universal philosophy boundary block for AI handoffs."""
    return "\n".join(
        [
            "## Philosophy Boundaries",
            "",
            "Use the selected philosophy as a review lens, not as a replacement for deck analysis.",
            "",
            "The philosophy lens may influence:",
            "- report tone",
            "- cut-pressure explanations",
            "- protected-card explanations",
            "- replacement-direction explanations",
            "- how tradeoffs are framed",
            "",
            "The philosophy lens must not override:",
            "- Commander legality",
            "- color identity",
            "- deck size rules",
            "- required cuts",
            "- commander identity",
            "- strategy detection",
            "- user-declared constraints",
            "- bracket / table-power goals",
            "- budget limits",
            "- combo tolerance",
            "- collection-only restrictions",
            "",
            "Strategy tells The Dragon's Touch what the deck is trying to do.",
            "Philosophy tells The Dragon's Touch how the pilot wants that deck to be judged, protected, challenged, and guided.",
        ]
    ).rstrip() + "\n"


def build_philosophy_prompt_language_hints(
    config: Optional[Mapping[str, Any]] = None,
    *,
    include_cut_hint: bool = True,
    include_protected_hint: bool = True,
    include_replacement_hint: bool = True,
) -> str:
    """Return philosophy-aware language hints for the selected runtime config."""
    lines = [
        "## Philosophy-Aware Language Hints",
        "",
        "Use these as phrasing guidance only. Do not treat them as card-evaluation results.",
    ]

    if include_cut_hint:
        lines.extend(
            [
                "",
                "**Cut-pressure phrasing:**",
                get_cut_pressure_language_from_runtime_config(config, "standard"),
            ]
        )

    if include_protected_hint:
        lines.extend(
            [
                "",
                "**Protected-card phrasing:**",
                get_protected_card_language_from_runtime_config(config, "standard"),
            ]
        )

    if include_replacement_hint:
        lines.extend(
            [
                "",
                "**Replacement-direction phrasing:**",
                get_replacement_direction_language_from_runtime_config(config, "standard"),
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def build_philosophy_prompt_context_summary(config: Optional[Mapping[str, Any]] = None) -> str:
    """Return a compact plain-text summary of the selected philosophy context."""
    runtime_context = context_from_runtime_config(config)
    profile = runtime_context.profile
    lens = runtime_context.lens_definition
    persona = runtime_context.persona_context

    lines = [
        "## Selected Philosophy Context",
        "",
        f"- Selected Lens: {profile.selected_lens}",
        f"- Parent Philosophy: {profile.parent_philosophy}",
        f"- Guide Role: {persona.get('guide_role') or lens.get('guide_role')}",
        f"- Primary Question: {persona.get('primary_question') or lens.get('primary_question')}",
    ]

    if persona.get("guide_name"):
        lines.append(f"- Guide: {persona.get('guide_name')}")
    else:
        lines.append("- Guide: None / named guide disabled")

    lines.append(f"- Intensity: {profile.intensity}")

    if profile.pilot_notes:
        lines.append(f"- Pilot Notes: {profile.pilot_notes}")

    if profile.protected_cards:
        lines.append("- User-Protected Cards: " + ", ".join(profile.protected_cards))

    if profile.declared_constraints:
        lines.append("- Declared Constraints: " + "; ".join(profile.declared_constraints))

    if profile.combo_tolerance:
        lines.append(f"- Combo Tolerance: {profile.combo_tolerance}")

    if profile.budget_note:
        lines.append(f"- Budget Note: {profile.budget_note}")

    if profile.table_power_note:
        lines.append(f"- Table Power / Bracket Note: {profile.table_power_note}")

    return "\n".join(lines).rstrip() + "\n"


def build_philosophy_handoff_block(
    config: Optional[Mapping[str, Any]] = None,
    *,
    include_guide_section: bool = True,
    include_context_summary: bool = True,
    include_boundaries: bool = True,
    include_language_hints: bool = True,
) -> str:
    """Build the full philosophy handoff block for generated AI prompts."""
    parts = [f"# {PHILOSOPHY_HANDOFF_TITLE}"]

    if include_context_summary:
        parts.append(build_philosophy_prompt_context_summary(config).rstrip())

    if include_guide_section:
        parts.append(
            format_philosophy_guide_section_from_runtime_config(
                config,
                heading_level=2,
                include_intensity=True,
                include_notes=True,
            ).rstrip()
        )

    if include_boundaries:
        parts.append(build_philosophy_prompt_boundary_block().rstrip())

    if include_language_hints:
        parts.append(build_philosophy_prompt_language_hints(config).rstrip())

    return "\n\n".join(parts).rstrip() + "\n"


def build_philosophy_prompt_injection(
    config: Optional[Mapping[str, Any]] = None,
    *,
    include_language_hints: bool = True,
) -> PhilosophyPromptInjection:
    """Build a structured philosophy prompt-injection payload."""
    guide_section = format_philosophy_guide_section_from_runtime_config(
        config,
        heading_level=2,
        include_intensity=True,
        include_notes=True,
    )
    boundary_block = build_philosophy_prompt_boundary_block()
    language_hints = (
        build_philosophy_prompt_language_hints(config)
        if include_language_hints
        else ""
    )
    handoff_block = build_philosophy_handoff_block(
        config,
        include_guide_section=True,
        include_context_summary=True,
        include_boundaries=True,
        include_language_hints=include_language_hints,
    )

    return PhilosophyPromptInjection(
        handoff_block=handoff_block,
        guide_section=guide_section,
        boundary_block=boundary_block,
        language_hints=language_hints,
        context=runtime_config_to_report_context(config),
    )


def append_philosophy_handoff_to_prompt(
    prompt_text: str,
    config: Optional[Mapping[str, Any]] = None,
    *,
    position: str = "top",
    delimiter: str = "\n\n---\n\n",
) -> str:
    """Return prompt text with philosophy handoff content inserted.

    This function is pure: it does not read or write prompt files.
    """
    source = str(prompt_text or "")
    handoff = build_philosophy_handoff_block(config).rstrip()
    normalized_position = str(position or "top").strip().lower().replace("-", "_").replace(" ", "_")

    if normalized_position in {"top", "before", "start"}:
        return f"{handoff}{delimiter}{source}".rstrip() + "\n"

    if normalized_position in {"bottom", "after", "end"}:
        return f"{source.rstrip()}{delimiter}{handoff}\n" if source.strip() else handoff + "\n"

    raise ValueError("position must be one of: top, bottom")


def build_philosophy_prompt_preview(config: Optional[Mapping[str, Any]] = None) -> str:
    """Convenience helper for manual prompt-preview testing."""
    return build_philosophy_handoff_block(config)


def prompt_injection_status() -> Dict[str, Any]:
    """Return a status object for smoke tests and diagnostics."""
    return {
        "version": "v1.1.10",
        "feature": "Prompt / AI Handoff Philosophy Injection",
        "integration_status": "prompt_helper_only",
        "runtime_behavior_changed": False,
        "writes_prompt_files": False,
        "changes_deck_analysis": False,
        "changes_cut_logic": False,
        "changes_replacement_logic": False,
        "recommends_exact_cards": False,
    }
