"""UI / runtime hook helpers for The Dragon's Touch philosophy layer.

Version: v1.1.11

This module provides safe metadata payloads that future UI/runtime code can use
to populate philosophy fields, validate selected values, and preview philosophy
handoff context.

Important boundary:
- This module does not change the UI by itself.
- This module does not write settings files.
- This module does not change deck analysis behavior.
- This module does not choose cuts.
- This module does not score cards.
- This module does not recommend exact replacement cards.
- This module only returns option lists, normalized configs, and preview payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from .philosophy_profile import (
    BALANCED_UNKNOWN,
    BIG_THREE_PHILOSOPHIES,
    GUIDE_PRESENTATIONS,
    INTENSITY_LEVELS,
    PHILOSOPHY_SUBTYPES,
)
from .philosophy_registry import (
    get_lens_definition,
    get_supported_lens_names,
    list_subtypes_by_parent,
)
from .persona_registry import get_persona_report_context
from .prompt_injection import build_philosophy_prompt_preview
from .report_integration_preview import build_philosophy_report_preview_markdown
from .runtime_config_mapping import (
    context_from_runtime_config,
    normalize_runtime_config,
    runtime_config_to_report_context,
)


@dataclass(frozen=True)
class PhilosophyRuntimeHookPayload:
    """Structured payload for future UI/runtime integration."""

    normalized_config: Dict[str, Any]
    context: Dict[str, Any]
    options: Dict[str, Any]
    report_preview_markdown: str
    prompt_preview_markdown: str
    status: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "normalized_config": dict(self.normalized_config),
            "context": dict(self.context),
            "options": dict(self.options),
            "report_preview_markdown": self.report_preview_markdown,
            "prompt_preview_markdown": self.prompt_preview_markdown,
            "status": dict(self.status),
        }



def _safe_lens_description(definition: Any) -> str:
    """Return optional lens description metadata without requiring a specific field."""
    for attr in ("description", "short_description", "summary"):
        value = getattr(definition, attr, None)
        if value:
            return str(value)
    return ""

def get_philosophy_ui_option_payload() -> Dict[str, Any]:
    """Return UI-safe philosophy option metadata.

    The payload is intended for dropdowns, settings forms, and future runtime
    config previews. It is stable, plain-data, and free of UI-framework objects.
    """
    broad = list(BIG_THREE_PHILOSOPHIES)
    subtypes_by_parent = {
        parent: list(list_subtypes_by_parent(parent))
        for parent in broad
    }

    return {
        "default_lens": BALANCED_UNKNOWN,
        "all_lenses": list(get_supported_lens_names()),
        "broad_philosophies": broad,
        "subtypes": list(PHILOSOPHY_SUBTYPES),
        "subtypes_by_parent": subtypes_by_parent,
        "guide_presentations": list(GUIDE_PRESENTATIONS),
        "intensity_levels": list(INTENSITY_LEVELS),
        "named_guide_supported": True,
        "no_named_guide_supported": True,
    }


def get_philosophy_ui_lens_options() -> List[Dict[str, Any]]:
    """Return lens options as list-of-dicts for UI controls."""
    options: List[Dict[str, Any]] = []
    for lens_name in get_supported_lens_names():
        definition = get_lens_definition(lens_name)
        options.append(
            {
                "value": definition.name,
                "label": definition.name,
                "parent_philosophy": definition.parent_philosophy,
                "depth": definition.depth,
                "guide_role": definition.guide_role,
                "primary_question": definition.primary_question,
                "description": _safe_lens_description(definition),
            }
        )
    return options


def get_philosophy_ui_persona_preview(
    selected_lens: str = BALANCED_UNKNOWN,
    guide_presentation: str = "no_named_guide",
) -> Dict[str, Any]:
    """Return persona preview metadata for a selected lens/presentation."""
    context = get_persona_report_context(selected_lens, guide_presentation)
    return {
        "selected_lens": selected_lens,
        "guide_presentation": guide_presentation,
        "guide_name": context.get("guide_name"),
        "guide_role": context.get("guide_role"),
        "display_label": context.get("display_label"),
        "named_guide_enabled": context.get("named_guide_enabled"),
        "primary_question": context.get("primary_question"),
        "short_guidance": context.get("short_guidance"),
    }


def build_default_philosophy_runtime_config() -> Dict[str, Any]:
    """Return the safe default runtime config for philosophy support."""
    return {
        "philosophy_lens": BALANCED_UNKNOWN,
        "guide_presentation": "no_named_guide",
        "philosophy_intensity": "normal",
        "pilot_notes": "",
        "protected_cards": [],
        "declared_constraints": [],
        "combo_tolerance": None,
        "budget_note": None,
        "table_power_note": None,
    }


def build_philosophy_runtime_config_patch(
    *,
    selected_lens: Optional[str] = None,
    guide_presentation: Optional[str] = None,
    intensity: Optional[str] = None,
    pilot_notes: Optional[str] = None,
    protected_cards: Optional[List[str]] = None,
    declared_constraints: Optional[List[str]] = None,
    combo_tolerance: Optional[str] = None,
    budget_note: Optional[str] = None,
    table_power_note: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a partial runtime config patch from UI-style values.

    None means "do not include this field." This makes it useful for future UI
    update events without overwriting unrelated settings.
    """
    patch: Dict[str, Any] = {}

    if selected_lens is not None:
        patch["philosophy_lens"] = selected_lens
    if guide_presentation is not None:
        patch["guide_presentation"] = guide_presentation
    if intensity is not None:
        patch["philosophy_intensity"] = intensity
    if pilot_notes is not None:
        patch["pilot_notes"] = pilot_notes
    if protected_cards is not None:
        patch["protected_cards"] = list(protected_cards)
    if declared_constraints is not None:
        patch["declared_constraints"] = list(declared_constraints)
    if combo_tolerance is not None:
        patch["combo_tolerance"] = combo_tolerance
    if budget_note is not None:
        patch["budget_note"] = budget_note
    if table_power_note is not None:
        patch["table_power_note"] = table_power_note

    return patch


def validate_philosophy_runtime_config_for_ui(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Validate and normalize UI/runtime philosophy config.

    Returns a plain dictionary instead of raising UI-specific errors. Invalid
    configs are reported with success=False and an error message.
    """
    try:
        normalized = normalize_runtime_config(config)
        context = context_from_runtime_config(normalized)
        return {
            "success": True,
            "error": None,
            "normalized_config": normalized,
            "selected_lens": context.profile.selected_lens,
            "parent_philosophy": context.profile.parent_philosophy,
            "guide_presentation": context.profile.guide_presentation,
            "guide_name": context.persona_context.get("guide_name"),
            "guide_role": context.persona_context.get("guide_role"),
            "display_label": context.persona_context.get("display_label"),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "normalized_config": None,
            "selected_lens": None,
            "parent_philosophy": None,
            "guide_presentation": None,
            "guide_name": None,
            "guide_role": None,
            "display_label": None,
        }


def build_philosophy_runtime_hook_payload(
    config: Optional[Mapping[str, Any]] = None,
    *,
    include_report_preview: bool = True,
    include_prompt_preview: bool = True,
) -> PhilosophyRuntimeHookPayload:
    """Build a complete safe payload for future UI/runtime integration."""
    normalized = normalize_runtime_config(config)
    context = runtime_config_to_report_context(normalized)
    options = get_philosophy_ui_option_payload()

    report_preview = (
        build_philosophy_report_preview_markdown(normalized, include_language_preview=False)
        if include_report_preview
        else ""
    )
    prompt_preview = (
        build_philosophy_prompt_preview(normalized)
        if include_prompt_preview
        else ""
    )

    return PhilosophyRuntimeHookPayload(
        normalized_config=normalized,
        context=context,
        options=options,
        report_preview_markdown=report_preview,
        prompt_preview_markdown=prompt_preview,
        status=ui_runtime_hook_status(),
    )


def ui_runtime_hook_status() -> Dict[str, Any]:
    """Return a status object for diagnostics and smoke tests."""
    return {
        "version": "v1.1.11",
        "feature": "UI / Runtime Config Hook",
        "integration_status": "ui_payload_helper_only",
        "runtime_behavior_changed": False,
        "writes_settings_files": False,
        "changes_ui_behavior": False,
        "changes_deck_analysis": False,
        "changes_cut_logic": False,
        "changes_replacement_logic": False,
        "recommends_exact_cards": False,
    }
