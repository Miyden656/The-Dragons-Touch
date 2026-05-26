from __future__ import annotations
from replacements.replacement_candidates import ensure_replacement_candidate_summary_from_context
from reports.report_postprocessors import apply_normal_report_postprocessors, _v0952_should_show_exact_preview, _v09551_exact_preview_categories  # v1.5.24 safe postprocessor batch
"""Normal report builder for the modular cleanup version.

Patch Batch 5.1 goal:
- Preserve the normal report as a complete AI handoff packet.
- Include the full decklist.
- Include annotated card-role notes for every main-deck card so another AI can
  reason about cuts, protection, and replacements without losing context.
"""


from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from app_io.output_writer import get_unique_output_path, write_text_file
from reports.strategy_knowledge_sections import build_strategy_knowledge_report_section  # v1.4.13 Strategy Knowledge report handoff
from analysis.deck_building_philosophies import render_philosophy_guide_section as _legacy_render_philosophy_guide_section  # fallback only after v1.1.18
from philosophy.report_section import format_philosophy_guide_section_from_runtime_config  # v1.1.18 live report guide section
# v1.1.22.3 manual-context review clarity: off-plan/manual review examples are context flags, not automatic cuts.
# v1.1.19.1 EXPLANATION WORDING CLEANUP / REPLACEMENT DE-DUP
# - Protected infrastructure entries now use infrastructure-safe wording instead
#   of commander-trigger/copy wording.
# - Replacement-direction explanations remain in Replacement Need Profile and
#   are no longer duplicated in the short Replacement / Addition Needs summary.

from philosophy.cut_explanation_wiring import build_philosophy_cut_explanation  # v1.1.19 live cut explanation wording
from philosophy.protected_explanation_wiring import build_philosophy_protected_explanation  # v1.1.19 live protected explanation wording
from philosophy.replacement_explanation_wiring import build_philosophy_replacement_explanation  # v1.1.19 live replacement-direction wording
from legality.companion_rules import (
    OFFICIAL_COMPANION_CARD_NAMES as COMPANION_CARD_NAMES,
    companion_is_banned_as_companion,
    get_companion_banned_note,
    get_companion_intake_lines,
    get_companion_replacement_filter_note,
    get_companion_restriction_summary,
)


# Companion card names are imported from legality.companion_rules.

def _v1118_absorb_object_public_attrs(value: Any) -> dict[str, Any]:
    """Best-effort conversion of runtime/config objects into a small safe mapping."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    data: dict[str, Any] = {}
    for name in (
        "guide_preference",
        "philosophy_key",
        "selected_lens",
        "philosophy_lens",
        "philosophy_subtype",
        "intended_bracket",
        "budget_note",
        "prompt_interaction_mode",
    ):
        if hasattr(value, name):
            try:
                data[name] = getattr(value, name)
            except Exception:
                pass
    return data

def _v1118_runtime_config_from_legacy_philosophy_context(context: dict[str, Any]) -> dict[str, Any]:
    """Build a v1.1 runtime-style philosophy config from the existing report context.

    v1.1.18 live report hook:
    - Uses the existing legacy philosophy_context as input.
    - Maps legacy `label` to v1.1 `selected_lens`.
    - Uses runtime bracket/budget fields when available.
    - Does not change deck analysis, cut scoring, replacement scoring, legality,
      collection matching, or combo behavior.
    """
    philosophy_context = context.get("philosophy_context") or {}
    runtime_config = context.get("runtime_config")

    config: dict[str, Any] = {}
    config.update(_v1118_absorb_object_public_attrs(runtime_config))

    if isinstance(philosophy_context, dict):
        # Preserve useful aliases already understood by v1.1 runtime mapping.
        for key in (
            "selected_lens",
            "philosophy_lens",
            "philosophy",
            "selected_philosophy",
            "review_philosophy",
            "subtype",
            "philosophy_subtype",
            "selected_subtype",
            "guide_lens",
            "guide_presentation",
            "guide_style",
            "guide_preference",
            "persona_presentation",
            "persona_style",
            "named_guide_preference",
            "intensity",
            "philosophy_intensity",
            "pilot_notes",
            "philosophy_notes",
            "combo_tolerance",
            "budget_note",
            "table_power_note",
            "intended_bracket",
        ):
            if key in philosophy_context and philosophy_context[key] not in (None, ""):
                config[key] = philosophy_context[key]

        # Legacy context primarily exposes `label`, not v1.1 `selected_lens`.
        if not config.get("selected_lens"):
            config["selected_lens"] = philosophy_context.get("label") or "Balanced / Unknown"

        # Legacy report text used rules_summary as the short pilot-facing note.
        if not config.get("pilot_notes"):
            config["pilot_notes"] = philosophy_context.get("rules_summary") or philosophy_context.get("report_guidance_summary") or ""

        if "named_guide_enabled" in philosophy_context:
            config["named_guide_enabled"] = philosophy_context.get("named_guide_enabled")

    if not config.get("guide_presentation") and not config.get("guide_preference"):
        config["guide_presentation"] = getattr(runtime_config, "guide_preference", None) or "either"

    if not config.get("budget_note"):
        config["budget_note"] = getattr(runtime_config, "budget_note", None) or "No budget note provided"

    if not config.get("table_power_note") and not config.get("intended_bracket"):
        config["table_power_note"] = getattr(runtime_config, "intended_bracket", None) or "Not sure yet"

    if not config.get("intensity"):
        config["intensity"] = "normal"

    return config

def _possible_companion_names_from_reference(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    command_zone = context.get("command_zone")
    known_companions = {str(name).lower() for name in getattr(command_zone, "companion_names", []) or []}
    candidates: list[str] = []
    for name in getattr(parsed, "reference_cards", []) or []:
        clean_name = str(name).strip()
        if clean_name in COMPANION_CARD_NAMES and clean_name.lower() not in known_companions:
            if clean_name not in candidates:
                candidates.append(clean_name)
    return candidates

def _v1119_runtime_config_for_explanations(context: dict[str, Any] | None) -> dict[str, Any]:
    """Build v1.1 runtime config for live explanation rendering."""
    if not isinstance(context, dict):
        return {}
    try:
        return _v1118_runtime_config_from_legacy_philosophy_context(context)
    except Exception:
        return {}

def _v095_get_replacement_needs_from_context(context: dict) -> list[str]:
    needs = []
    for key in ("replacement_needs", "replacement_need_profile", "needs", "replacement_profile"):
        value = context.get(key)
        if not value:
            continue
        if isinstance(value, dict):
            for item in value.values():
                if isinstance(item, (list, tuple, set)):
                    needs.extend(str(x) for x in item)
                else:
                    needs.append(str(item))
        elif isinstance(value, (list, tuple, set)):
            needs.extend(str(x) for x in value)
        else:
            needs.append(str(value))

    cleaned = []
    for need in needs:
        need = need.strip()
        if need and need not in cleaned:
            cleaned.append(need)
    return cleaned[:8]

def _v0951_get_replacement_needs_from_context(context: dict) -> list[str]:
    needs: list[str] = []

    for key in ("replacement_needs", "replacement_need_profile", "replacement_candidate_needs", "needs", "replacement_profile"):
        for need in _v0951_clean_need_text(context.get(key)):
            if need not in needs:
                needs.append(need)

    # If the only thing available was an empty summary object, provide a readable fallback reason.
    if not needs:
        summary = (
            context.get("replacement_needs")
            or context.get("replacement_need_profile")
            or context.get("replacement_candidate_needs")
            or context.get("replacement_profile")
        )
        if summary is not None:
            notes = _v0951_clean_need_text(getattr(summary, "notes", None))
            for note in notes:
                if note not in needs:
                    needs.append(note)

    if not needs:
        needs.append("No urgent replacement category detected")

    return needs[:8]
