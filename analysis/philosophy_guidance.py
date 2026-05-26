# v1.1.20 LEGACY PHILOSOPHY DIAGNOSTICS CLEANUP
"""
analysis/deck_building_philosophies.py

Philosophy and persona guide data for The Dragon's Touch.

This module is designed for the v0.6.2 CLEANUP layout, which uses top-level
packages such as analysis, cuts, reports, app_io, and rules.

Design rules:
- Strategy detection remains primary.
- The philosophy/subtype key is the rules object.
- The persona name is the user-facing guide.
- This module should not perform strategy detection.
- Reports, cut logic, replacement logic, and prompt generation can consume this module.

v0.6.5.3 adds report-facing subtype summaries. These summaries are still
non-scoring guidance: they help humans and reviewing AIs understand what the
selected lens means without changing legality, strategy detection, cuts, or
collection matching.

v0.6.5.4 adds prompt-facing showcase polish so generated guided prompts explain
philosophy lenses consistently across subtypes.

v0.6.6.1 adds the foundation for philosophy-aware cut/replacement bias.
v0.6.6.2 turns on a light optional-cut scoring nudge while leaving strategy detection, legality, and collection matching unchanged.
v0.6.6.5 adds a philosophy-bias QA / stress-test checkpoint while preserving the v0.6.6.4.2 replacement-bias behavior and all quality gates.
v0.6.6.6 locks the v0.6.6 philosophy-bias milestone and documents its scope, boundaries, and QA expectations. The v0.6.6.5.2 balanced-neutrality and companion-review cleanup remains active.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import choice
from typing import Dict, List, Literal, Optional


GuidePreference = Literal["masculine", "feminine", "either", "random", "none"]
GuidePreference = Literal["masculine", "feminine", "either", "random", "none"]

def _build_report_guidance_summary(profile: PhilosophyProfile) -> str:
    """Return a report-facing explanation of how to read cards through this lens."""
    if profile.key == "theme_vibe":
        return "Judge cards by whether they make the deck feel more like its intended story, creature type, joke, table experience, or aesthetic. Theme cards get extra respect when they also perform a useful role; flavor-only cards can still be challenged if they weaken function."
    if profile.key == "pet_card":
        return "Declared pet cards should be protected from normal optimization pressure, while the surrounding shell should be improved so those cards can matter in games."
    if profile.key == "combo_builder":
        return "Evaluate whether each card finds, protects, enables, or cleanly supports the intended combo or interaction chain without adding unwanted combo pressure."
    if profile.key == "commander_exploiter":
        return "Prioritize cards that specifically exploit the commander's rules text over generic good cards that do not strengthen the commander's unique plan."
    if profile.key == "curve_mana_discipline":
        return "Evaluate whether the mana curve, land count, ramp, and color requirements let the deck actually execute its plan on time."
    if profile.key == "power_level_calibrator":
        return "Evaluate whether the deck is matched to the target table experience; stronger is not automatically better if it violates the intended bracket."
    if profile.key == "balanced_unknown":
        return "Use the report to identify the deck's likely plan, tensions, and possible philosophy lean without applying subtype-specific assumptions yet."
    return profile.rules_summary

def render_philosophy_report_guidance(context: dict) -> str:
    """Render v0.6.5.3 report-facing philosophy guidance.

    This is intentionally guidance text only. It does not change scoring,
    legality, strategy detection, collection matching, or required cuts.
    """
    label = context.get("label", "Balanced / Unknown")
    key = context.get("key", "balanced_unknown")
    guide = _guide_display_name(context)
    parent = context.get("parent_label") or label
    protect = context.get("protect_summary") or _comma_list(context.get("protect_bias", []), 6)
    review = context.get("question_summary") or _comma_list(context.get("review_bias", []), 6)
    replacement = context.get("prefer_summary") or _comma_list(context.get("replacement_bias", []), 6)

    lines = [
        "**v0.6.5.3 Philosophy Subtype Report Summary:** This block explains how to read this report through the selected lens. It is still guidance only and does not change legality, deck size, color identity, strategy detection, required cuts, collection matching, cut scores, or replacement scores.",
        "",
        "**At-a-glance lens summary:**",
        f"- {context.get('short_lens_summary') or context.get('rules_summary', 'Use the selected lens as review framing only.')}",
        "",
        "**How to read cards through this lens:**",
        f"- {context.get('report_guidance_summary') or context.get('rules_summary', 'Use this lens to shape explanation style and review priorities.')}",
        "",
        "**Protect / Question / Prefer:**",
        f"- Protect: {protect}.",
        f"- Question: {review}.",
        f"- Prefer replacements that support: {replacement}.",
        "",
        "**Review boundaries:**",
        "- Treat all philosophy language as review framing, not as a hard mechanical override.",
        "- If the pilot's stated intent conflicts with this lens, the pilot's stated intent wins.",
        "- Required legality fixes still outrank philosophy preference.",
    ]

    if key == "balanced_unknown":
        lines.extend([
            "- Balanced / Unknown should avoid strong assumptions, identify possible philosophy lean, and recommend choosing a deeper lens only when it would materially improve the review.",
        ])
    elif parent in {"Timmy / Tammy", "Johnny / Jenny", "Spike"}:
        lines.append(f"- Because this is under {parent}, preserve the deck's chosen style while still checking whether the support structure actually works.")

    if context.get("example_language"):
        lines.extend(["", "**Example review language:**", f"> {context.get('example_language')}"])

    if context.get("named_guide_enabled", True):
        lines.extend([
            "",
            "**Guide presentation note:**",
            f"- {guide} should be used as a concise mentor frame, not as heavy roleplay or a separate character speaking in first person.",
        ])
    else:
        lines.extend([
            "",
            "**Guide presentation note:**",
            "- Named guide presentation is disabled; use philosophy labels only.",
        ])

    return "\n".join(lines)

def get_cut_modifier_hints(key: Optional[str]) -> dict:
    """
    Return lightweight hints for cut logic.

    Existing cut logic can consume these hints without needing persona names.
    MVP implementation should label cards first before changing numeric scoring.
    """
    profile = get_philosophy_profile(key)
    bias = _build_bias_profile(profile)
    return {
        "philosophy_key": profile.key,
        "protect_bias": list(profile.protect_bias),
        "review_bias": list(profile.review_bias),
        "cut_pressure_notes": list(profile.cut_pressure_notes),
        "philosophy_bias_foundation_active": bias["philosophy_bias_foundation_active"],
        "bias_scoring_active": bias["bias_scoring_active"],
        "bias_strength": bias["bias_strength"],
        "cut_bias_scoring_active": bias.get("cut_bias_scoring_active", False),
        "replacement_bias_scoring_active": bias.get("replacement_bias_scoring_active", False),
        "cut_bias_protect_roles": list(bias["cut_bias_protect_roles"]),
        "cut_bias_review_roles": list(bias["cut_bias_review_roles"]),
    }

def get_replacement_bias(key: Optional[str]) -> List[str]:
    """Return preferred replacement categories for the selected philosophy."""
    return list(get_philosophy_profile(key).replacement_bias)

def get_replacement_bias_roles(key: Optional[str]) -> List[str]:
    """Return v0.6.6.1 replacement-bias role buckets for future candidate logic."""
    profile = get_philosophy_profile(key)
    return list(_build_bias_profile(profile)["replacement_bias_roles"])
