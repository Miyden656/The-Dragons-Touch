"""Philosophy report integration preview helpers for The Dragon's Touch.

Version: v1.1.9

This module is the first safe report-integration layer for the v1.1 philosophy
system. It produces markdown preview content from runtime config, but does not
wire itself into the real deck report pipeline.

Important boundary:
- This module does not change deck analysis behavior.
- This module does not choose cuts.
- This module does not score cards.
- This module does not recommend exact replacement cards.
- This module does not modify existing report files by itself.
- This module only returns preview markdown or payload dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .cut_language import format_cut_pressure_note_from_runtime_config
from .protected_language import format_protected_card_note_from_runtime_config
from .replacement_language import format_replacement_direction_note_from_runtime_config
from .report_section import format_philosophy_guide_section_from_runtime_config
from .runtime_config_mapping import (
    RuntimePhilosophyContext,
    context_from_runtime_config,
    runtime_config_to_report_context,
)


PREVIEW_SECTION_TITLE = "Philosophy Integration Preview"


@dataclass(frozen=True)
class PhilosophyReportPreview:
    """Structured preview payload for later report integration."""

    context: RuntimePhilosophyContext
    guide_section: str
    language_preview_section: str
    combined_markdown: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "guide_section": self.guide_section,
            "language_preview_section": self.language_preview_section,
            "combined_markdown": self.combined_markdown,
        }


def build_philosophy_language_preview_section(
    config: Optional[Mapping[str, Any]] = None,
    *,
    heading_level: int = 3,
    sample_card_name: str = "Sample Card",
    sample_replacement_role: str = "Replacement Role",
) -> str:
    """Build a preview section showing the three philosophy language pillars.

    This is intentionally a preview. It demonstrates the language that could be
    used by later report wiring without applying it to actual card decisions.
    """
    level = max(1, min(int(heading_level), 6))
    heading = "#" * level

    cut_note = format_cut_pressure_note_from_runtime_config(
        config,
        sample_card_name,
        language_type="standard",
    )
    protected_note = format_protected_card_note_from_runtime_config(
        config,
        sample_card_name,
        language_type="standard",
    )
    replacement_note = format_replacement_direction_note_from_runtime_config(
        config,
        sample_replacement_role,
        language_type="standard",
    )

    lines = [
        f"{heading} {PREVIEW_SECTION_TITLE}",
        "",
        "This preview shows how the selected philosophy lens can phrase report language. It does not change card evaluation, cut decisions, or replacement logic yet.",
        "",
        "**Cut-Pressure Language Preview**",
        "",
        cut_note,
        "",
        "**Protected-Card Language Preview**",
        "",
        protected_note,
        "",
        "**Replacement-Direction Language Preview**",
        "",
        replacement_note,
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_philosophy_report_preview(
    config: Optional[Mapping[str, Any]] = None,
    *,
    guide_heading_level: int = 2,
    preview_heading_level: int = 3,
    include_language_preview: bool = True,
    include_intensity: bool = False,
    include_notes: bool = False,
) -> PhilosophyReportPreview:
    """Build a structured philosophy report preview from runtime config."""
    context = context_from_runtime_config(config)

    guide_section = format_philosophy_guide_section_from_runtime_config(
        config,
        heading_level=guide_heading_level,
        include_intensity=include_intensity,
        include_notes=include_notes,
    )

    language_preview_section = ""
    if include_language_preview:
        language_preview_section = build_philosophy_language_preview_section(
            config,
            heading_level=preview_heading_level,
        )

    combined_parts = [guide_section.rstrip()]
    if language_preview_section:
        combined_parts.append(language_preview_section.rstrip())

    combined_markdown = "\n\n".join(combined_parts).rstrip() + "\n"

    return PhilosophyReportPreview(
        context=context,
        guide_section=guide_section,
        language_preview_section=language_preview_section,
        combined_markdown=combined_markdown,
    )


def build_philosophy_report_preview_markdown(
    config: Optional[Mapping[str, Any]] = None,
    *,
    guide_heading_level: int = 2,
    preview_heading_level: int = 3,
    include_language_preview: bool = True,
    include_intensity: bool = False,
    include_notes: bool = False,
) -> str:
    """Return only the combined markdown preview string."""
    return build_philosophy_report_preview(
        config,
        guide_heading_level=guide_heading_level,
        preview_heading_level=preview_heading_level,
        include_language_preview=include_language_preview,
        include_intensity=include_intensity,
        include_notes=include_notes,
    ).combined_markdown


def build_philosophy_report_integration_payload(
    config: Optional[Mapping[str, Any]] = None,
    *,
    include_language_preview: bool = True,
) -> Dict[str, Any]:
    """Return a plain dictionary payload for future report integration.

    This helper gives future report generation code a stable object shape while
    keeping v1.1.9 as preview-only.
    """
    preview = build_philosophy_report_preview(
        config,
        include_language_preview=include_language_preview,
    )
    payload = preview.to_dict()
    payload["runtime_report_context"] = runtime_config_to_report_context(config)
    payload["integration_status"] = "preview_only"
    payload["runtime_behavior_changed"] = False
    return payload


def insert_philosophy_preview_into_markdown(
    report_markdown: str,
    config: Optional[Mapping[str, Any]] = None,
    *,
    position: str = "after_title",
    include_language_preview: bool = False,
) -> str:
    """Return a copy of report markdown with a philosophy preview inserted.

    This function is pure: it does not read or write report files. Later patches
    may choose to call it from the real report pipeline after QA.
    """
    source = str(report_markdown or "")
    preview = build_philosophy_report_preview_markdown(
        config,
        include_language_preview=include_language_preview,
    ).rstrip()

    normalized_position = str(position or "after_title").strip().lower().replace("-", "_").replace(" ", "_")

    if normalized_position in {"top", "before_report", "start"}:
        return f"{preview}\n\n{source}".rstrip() + "\n"

    if normalized_position in {"bottom", "after_report", "end"}:
        return f"{source.rstrip()}\n\n{preview}\n" if source.strip() else preview + "\n"

    if normalized_position not in {"after_title", "after_first_heading"}:
        raise ValueError("position must be one of: after_title, top, bottom")

    lines = source.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            before = "\n".join(lines[: idx + 1]).rstrip()
            after = "\n".join(lines[idx + 1 :]).lstrip()
            if after:
                return f"{before}\n\n{preview}\n\n{after}\n"
            return f"{before}\n\n{preview}\n"

    return f"{preview}\n\n{source}".rstrip() + "\n"


def preview_status() -> Dict[str, Any]:
    """Return a small status object for smoke tests and future diagnostics."""
    return {
        "version": "v1.1.9",
        "feature": "Report Integration Preview / No Behavior Change",
        "integration_status": "preview_only",
        "runtime_behavior_changed": False,
        "writes_report_files": False,
        "changes_deck_analysis": False,
        "changes_cut_logic": False,
        "changes_replacement_logic": False,
    }
