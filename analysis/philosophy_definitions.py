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

@dataclass(frozen=True)
class Persona:
    role: str
    core_question: str
    masculine: Optional[str] = None
    feminine: Optional[str] = None
    neutral: Optional[str] = None

    def resolve_name(self, preference: GuidePreference = "either") -> Optional[str]:
        """Resolve the user-facing guide name from the preferred presentation style."""
        if preference == "none":
            return None

        if self.neutral:
            return self.neutral

        if preference == "masculine":
            return self.masculine or self.feminine
        if preference == "feminine":
            return self.feminine or self.masculine
        if preference in {"either", "random"}:
            options = [name for name in [self.masculine, self.feminine] if name]
            return choice(options) if options else None

        return self.masculine or self.feminine or self.neutral

@dataclass(frozen=True)
class PhilosophyProfile:
    key: str
    label: str
    parent: Optional[str]
    persona: Persona
    core_philosophy: str
    rules_summary: str
    protect_bias: List[str] = field(default_factory=list)
    review_bias: List[str] = field(default_factory=list)
    replacement_bias: List[str] = field(default_factory=list)
    cut_pressure_notes: List[str] = field(default_factory=list)
    # v0.6.6.1 bias foundation fields. These are exposed for diagnostics and
    # future cut/replacement logic. In v0.6.6.5 the v0.6.6.4.2 cut/replacement bias behavior remains active and a QA/stress-test checkpoint documents whether the lens is behaving safely.
    cut_bias_protect_roles: List[str] = field(default_factory=list)
    cut_bias_review_roles: List[str] = field(default_factory=list)
    replacement_bias_roles: List[str] = field(default_factory=list)
    bias_strength: str = "guidance"
    bias_warning: str = "v0.6.6.6 locks the philosophy-bias milestone: light optional-cut nudges, protected/watch explanation fields, replacement-candidate presentation nudges, balanced-neutrality cleanup, and companion manual-review wording are active. Bias must not override legality, required cuts, pilot-protected cards, color identity, companion restrictions, collection mode, quality gates, or explicit pilot intent."
    tone: str = "balanced, clear, and supportive"
    example_language: str = ""

def _add_subtype(profile: PhilosophyProfile) -> None:
    PHILOSOPHY_PROFILES[profile.key] = profile

def normalize_philosophy_key(key: Optional[str]) -> str:
    """Normalize user/env/config input into a known philosophy key."""
    if not key:
        return "balanced_unknown"

    normalized = str(key).strip().lower()
    if not normalized:
        return "balanced_unknown"

    if normalized in PHILOSOPHY_NUMBER_ALIASES:
        return PHILOSOPHY_NUMBER_ALIASES[normalized]

    normalized = normalized.replace(" / ", "_").replace("/", "_").replace("-", "_").replace(" ", "_")

    aliases = {
        "balanced": "balanced_unknown",
        "unknown": "balanced_unknown",
        "balanced_unknown": "balanced_unknown",
        "rowan": "balanced_unknown",
        "timmy": "timmy_tammy",
        "tammy": "timmy_tammy",
        "timmy_tammy": "timmy_tammy",
        "johnny": "johnny_jenny",
        "jenny": "johnny_jenny",
        "johnny_jenny": "johnny_jenny",
        "big_creature": "big_creature_stompy",
        "stompy": "big_creature_stompy",
        "theme": "theme_vibe",
        "vibe": "theme_vibe",
        "self_imposed_constraint_builder": "constraint_builder",
        "constraint": "constraint_builder",
        "combo": "combo_builder",
        "mana_discipline": "curve_mana_discipline",
        "curve": "curve_mana_discipline",
        "interaction": "interaction_controller",
    }
    return aliases.get(normalized, normalized)

def get_philosophy_profile(key: Optional[str]) -> PhilosophyProfile:
    """Return a philosophy profile. Defaults safely to Balanced / Unknown."""
    normalized = normalize_philosophy_key(key)
    return PHILOSOPHY_PROFILES.get(normalized, PHILOSOPHY_PROFILES["balanced_unknown"])

def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Return unique, non-empty strings while preserving first-seen order."""
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output

def _build_bias_profile(profile: PhilosophyProfile) -> dict:
    """Build v0.6.6.1 philosophy bias foundation data.

    This exposes the *shape* of future cut/replacement bias without applying it.
    Cut logic and collection candidate logic consume these fields as light nudges. They remain diagnostics/report context for legality, strategy detection, required cuts, and collection mode boundaries.
    """
    # Explicit profile fields win if a future profile supplies them. Otherwise,
    # map existing human-facing philosophy guidance into role-like buckets that
    # later logic can consume.
    protect_roles = list(profile.cut_bias_protect_roles)
    review_roles = list(profile.cut_bias_review_roles)
    replacement_roles = list(profile.replacement_bias_roles)

    key_specific: dict[str, dict[str, list[str] | str]] = {
        "balanced_unknown": {
            # v0.6.6.5.2: Balanced / Unknown must stay mostly neutral. Normal
            # protection/context rules already handle commander support, primary
            # plan support, infrastructure, role-fillers, and protected cards.
            # The Balanced philosophy layer should add visible cut-bias text only
            # to clear off-plan cards or explicit user-intent conflicts.
            "protect": ["declared_user_intent"],
            "review": ["off_plan", "user_intent_conflict"],
            "replacement": ["role_balance", "strategy_support", "mana_consistency", "clear_deck_identity"],
            "strength": "neutral",
        },
        "big_moment": {
            "protect": ["declared_big_moment_card", "big_moment_enabler", "splashy_finisher", "x_spell", "doublers", "payoff_ramp", "payoff_protection"],
            "review": ["unsupported_haymaker", "expensive_no_payoff", "win_more", "clunky_unrelated_card"],
            "replacement": ["better_ramp", "payoff_support", "protection", "haste_evasion_trample", "copy_or_doubling_effect", "draw_to_find_payoff"],
            "strength": "light",
        },
        "big_creature_stompy": {
            "protect": ["impactful_large_creature", "ramp_into_threats", "haste_evasion_trample", "creature_protection", "power_toughness_payoff", "typal_commander_support"],
            "review": ["large_creature_no_impact", "redundant_top_end", "ramp_light_expensive_hand", "small_value_dilution"],
            "replacement": ["ramp", "creature_based_draw", "trample_evasion_haste", "protection", "impactful_top_end", "size_to_value_payoff"],
            "strength": "light",
        },
        "theme_vibe": {
            "protect": ["declared_theme", "typal_piece", "flavor_with_function", "identity_preserving_card"],
            "review": ["flavor_only_low_function", "identity_clashing_staple", "low_impact_theme_card"],
            "replacement": ["on_theme_role_filler", "flavorful_removal", "flavorful_draw", "vibe_preserving_upgrade"],
            "strength": "light",
        },
        "pet_card": {
            "protect": ["declared_pet_card", "personal_attachment_card", "build_around_memory_card"],
            "review": ["surrounding_shell_weakness", "support_piece_not_helping_pet_card"],
            "replacement": ["pet_card_support", "shell_consistency", "protection_for_pet_card"],
            "strength": "light",
        },
        "commander_exploiter": {
            "protect": ["commander_text_synergy", "commander_scaling", "commander_protection", "ability_enabler", "resource_converter", "commander_specific_payoff"],
            "review": ["generic_goodstuff", "commander_ignoring_card", "unused_ability_support", "color_fit_plan_miss"],
            "replacement": ["commander_synergy", "commander_protection", "ability_multiplier", "redundancy_for_commander_effect", "backup_engine"],
            "strength": "light",
        },
        "engine_builder": {
            "protect": ["engine_piece", "connector_card", "enabler", "payoff_bridge", "weak_alone_strong_in_context"],
            "review": ["unsupported_engine_piece", "disconnected_package", "cute_but_unconnected_card"],
            "replacement": ["engine_redundancy", "connector_piece", "enabler_density", "payoff_support"],
            "strength": "light",
        },
        "combo_builder": {
            "protect": ["combo_piece", "combo_tutor", "combo_protection", "combo_enabler", "combo_payoff"],
            "review": ["partial_combo_without_support", "unwanted_combo_pressure", "dead_combo_piece"],
            "replacement": ["combo_consistency", "combo_protection", "cleaner_enabler", "backup_plan"],
            "strength": "light",
        },
        "curve_mana_discipline": {
            "protect": ["efficient_ramp", "cheap_interaction", "curve_smoothing", "mana_fixing", "low_curve_enabler"],
            "review": ["overcosted_effect", "curve_clog", "clunky_top_end", "mana_intensive_card"],
            "replacement": ["lower_curve", "efficient_role_filler", "better_mana", "cheap_card_selection"],
            "strength": "medium",
        },
        "power_level_calibrator": {
            "protect": ["table_fit_card", "bracket_appropriate_interaction", "power_limit_respecting_card"],
            "review": ["bracket_pressure", "table_mismatch", "unwanted_fast_mana", "unwanted_tutor", "unwanted_combo"],
            "replacement": ["table_fit_upgrade", "bracket_appropriate_answer", "power_matched_role_filler"],
            "strength": "medium",
        },
        "interaction_controller": {
            "protect": ["flexible_interaction", "synergy_interaction", "board_control_piece", "commander_protection"],
            "review": ["narrow_answer", "dead_interaction", "threat_mismatch", "uninteractive_payoff"],
            "replacement": ["better_interaction", "role_compression", "table_specific_answer", "protective_interaction"],
            "strength": "medium",
        },
        "spike": {
            "protect": ["efficient_ramp", "efficient_draw", "flexible_interaction", "reliable_mana", "clean_finisher"],
            "review": ["overcosted_effect", "low_impact_card", "win_more", "narrow_card", "clunky_top_end"],
            "replacement": ["efficiency_upgrade", "consistency_upgrade", "role_compression", "better_interaction"],
            "strength": "medium",
        },
    }

    data = key_specific.get(profile.key)
    if data:
        protect_roles.extend(data.get("protect", []))
        review_roles.extend(data.get("review", []))
        replacement_roles.extend(data.get("replacement", []))
        strength = str(data.get("strength", profile.bias_strength or "guidance"))
    else:
        # Safe default for profiles that do not yet have explicit bias maps.
        protect_roles.extend(profile.protect_bias)
        review_roles.extend(profile.review_bias)
        replacement_roles.extend(profile.replacement_bias)
        if profile.parent == "spike":
            strength = "medium"
        elif profile.parent in {"timmy_tammy", "johnny_jenny"}:
            strength = "light"
        else:
            strength = profile.bias_strength or "guidance"

    return {
        "philosophy_bias_foundation_active": True,
        "philosophy_bias_foundation_version": "v0.6.6.6",
        "bias_scoring_active": True,
        "cut_bias_scoring_active": True,
        "replacement_bias_scoring_active": True,
        "bias_strength": strength,
        "bias_warning": profile.bias_warning,
        "cut_bias_protect_roles": _dedupe_preserve_order(protect_roles),
        "cut_bias_review_roles": _dedupe_preserve_order(review_roles),
        "replacement_bias_roles": _dedupe_preserve_order(replacement_roles),
    }

def build_philosophy_context(
    key: Optional[str] = None,
    guide_preference: GuidePreference = "either",
) -> dict:
    """Build a serializable context object for reports, prompts, and analysis."""
    profile = get_philosophy_profile(key)
    guide_name = profile.persona.resolve_name(guide_preference)

    parent_label = None
    if profile.parent:
        parent_label = PHILOSOPHY_PROFILES[profile.parent].label
    elif profile.key == "balanced_unknown":
        parent_label = "Balanced / Unknown"

    summary_fields = _summaries_for_profile(profile)
    bias_fields = _build_bias_profile(profile)

    return {
        "key": profile.key,
        "label": profile.label,
        "parent_key": profile.parent,
        "parent_label": parent_label,
        "guide_name": guide_name,
        "guide_role": profile.persona.role,
        "core_question": profile.persona.core_question,
        "core_philosophy": profile.core_philosophy,
        "rules_summary": profile.rules_summary,
        "protect_bias": list(profile.protect_bias),
        "review_bias": list(profile.review_bias),
        "replacement_bias": list(profile.replacement_bias),
        "cut_pressure_notes": list(profile.cut_pressure_notes),
        "tone": profile.tone,
        "example_language": profile.example_language,
        "named_guide_enabled": guide_preference != "none",
        **summary_fields,
        **bias_fields,
    }

def _guide_display_name(context: dict) -> str:
    """Return the best user-facing name for the selected guide/lens."""
    if context.get("named_guide_enabled", True) and context.get("guide_name"):
        return str(context["guide_name"])
    return str(context.get("label", "Balanced / Unknown"))

def _comma_list(values: list[str], limit: int = 6) -> str:
    """Render a short comma-separated list for report guidance."""
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return ", ".join(cleaned[:limit]) if cleaned else "None listed"

def _sentence_list(values: list[str], limit: int = 5) -> str:
    """Render short guidance values as a readable comma list."""
    return _comma_list(values, limit=limit)

def _build_short_lens_summary(profile: PhilosophyProfile) -> str:
    """Return one concise at-a-glance sentence for the selected lens."""
    if profile.key == "balanced_unknown":
        return "Use this lens to discover the deck's natural identity before making strong philosophy assumptions."

    parent = PHILOSOPHY_PROFILES.get(profile.parent).label if profile.parent and profile.parent in PHILOSOPHY_PROFILES else profile.label
    if parent == "Timmy / Tammy":
        return f"Use this lens to preserve the deck's intended experience while checking that the support structure actually lets that experience happen."
    if parent == "Johnny / Jenny":
        return f"Use this lens to protect the deck's idea, engine, constraint, or clever interaction while challenging pieces that do not actually connect."
    if parent == "Spike":
        return f"Use this lens to improve performance at the intended table without assuming cEDH or overriding the pilot's power goal."
    return profile.rules_summary

def _summaries_for_profile(profile: PhilosophyProfile) -> dict:
    """Build v0.6.5.3 summary fields from the existing philosophy profile."""
    protect = _sentence_list(profile.protect_bias, 6)
    question = _sentence_list(profile.review_bias, 6)
    prefer = _sentence_list(profile.replacement_bias, 6)
    return {
        "short_lens_summary": _build_short_lens_summary(profile),
        "report_guidance_summary": _build_report_guidance_summary(profile),
        "protect_summary": protect,
        "question_summary": question,
        "prefer_summary": prefer,
        "pilot_override_note": "Pilot-stated intent overrides this lens whenever the two conflict.",
        "subtype_summary_active": True,
        "subtype_summary_version": "v0.6.5.3",
    }

def render_guide_introduction_instruction(context: dict) -> str:
    """Render prompt instructions for the AI that will use the generated user-guided prompt.

    This is intentionally instruction text, not roleplay. The guide should be introduced
    briefly after the deck report is received, then the review should move directly into
    the numbered intake flow.
    """
    guide = _guide_display_name(context)
    lens = context.get("label", "Balanced / Unknown")
    role = context.get("guide_role", "Guide")
    question = context.get("core_question", "What does this deck want to do?")
    named_enabled = context.get("named_guide_enabled", True)

    if named_enabled and context.get("guide_name"):
        opening = f"After receiving the deck report, briefly introduce {guide} as the {role}."
    else:
        opening = f"After receiving the deck report, briefly introduce the {lens} philosophy lens."

    return "\n".join([
        opening,
        f"Use this guide question to frame the review: {question}",
        "Keep the introduction to 2-4 sentences, then immediately ask Section 1.",
        "The guide/persona is a mentor framing device only; it must not override legality, deck size, strategy detection, budget, combo tolerance, bracket goals, collection mode, or user answers.",
    ])

def render_philosophy_guide_section(context: dict) -> str:
    """Render the Philosophy Guide report section.

    v0.6.5.1 expands this from a simple label block into a report guidance
    checkpoint while keeping philosophy as non-scoring guidance.
    """
    selected_lens = context.get("label", "Balanced / Unknown")
    parent_label = context.get("parent_label")
    guide_name = context.get("guide_name")
    named_enabled = context.get("named_guide_enabled", True)

    lines = ["## Philosophy Guide", ""]
    lines.append(f"**Selected Lens:** {selected_lens}")

    if named_enabled and guide_name:
        lines.append(f"**Guide:** {guide_name}")
        lines.append(f"**Guide Role:** {context.get('guide_role', 'Guide')}")
    else:
        lines.append("**Guide:** No named guide selected")

    if parent_label and parent_label != selected_lens:
        lines.append(f"**Parent Philosophy:** {parent_label}")

    lines.append(f"**Primary Question:** {context.get('core_question', 'What does this deck want to do?')}")
    lines.append("")
    lines.append(context.get("rules_summary", "Use a balanced exploratory lens."))
    lines.append("")
    lines.append("**Boundary:** This philosophy is a review lens. It does not replace strategy detection, legality, deck-size rules, color identity, budget, combo tolerance, bracket goals, collection limits, or user-stated intent.")
    lines.append("")

    if context.get("short_lens_summary"):
        lines.append("**Lens Summary:** " + context.get("short_lens_summary", ""))
        lines.append("")

    if context.get("report_guidance_summary"):
        lines.append("**How to Use This Lens:** " + context.get("report_guidance_summary", ""))
        lines.append("")

    if context.get("core_philosophy"):
        lines.append("**Core Philosophy:** " + context.get("core_philosophy", ""))
        lines.append("")

    if context.get("protect_bias"):
        lines.append("**What this lens tends to protect:** " + ", ".join(context["protect_bias"][:6]))
        lines.append("")

    if context.get("review_bias"):
        lines.append("**What this lens tends to challenge:** " + ", ".join(context["review_bias"][:6]))
        lines.append("")

    if context.get("replacement_bias"):
        lines.append("**Replacement Bias:** " + ", ".join(context["replacement_bias"][:6]))
        lines.append("")

    if context.get("cut_pressure_notes"):
        lines.append("**Cut-Pressure Notes:**")
        for note in context["cut_pressure_notes"][:4]:
            lines.append(f"- {note}")
        lines.append("")

    lines.append(render_philosophy_report_guidance(context).rstrip())
    lines.append("")

    return "\n".join(lines)

def render_philosophy_diagnostics_section(context: dict) -> str:
    """Render a detailed debug section for the selected philosophy/persona."""
    guide = _guide_display_name(context)
    lines = [
        "## Philosophy / Persona Context",
        "- v1.1 surface alignment: This section identifies the selected lens/persona that now feeds the live v1.1 prompt, report, and explanation surfaces.",
        "- Legacy diagnostic note: v0.6.5.x / v0.6.6.x entries below describe older internal bias counters and QA checkpoints, not a separate active philosophy system.",
        f"- Selected lens: {context.get('label', 'Balanced / Unknown')}",
        f"- Philosophy key: {context.get('key', 'balanced_unknown')}",
        f"- Parent philosophy: {context.get('parent_label') or 'None'}",
        f"- Named guide enabled: {context.get('named_guide_enabled', True)}",
        f"- Resolved guide: {guide}",
        f"- Guide role: {context.get('guide_role', 'Guide')}",
        f"- Primary question: {context.get('core_question', 'What does this deck want to do?')}",
        f"- Tone: {context.get('tone', 'balanced, clear, and supportive')}",
        "- Boundary: Philosophy/persona is guidance only; it does not override legality, deck size, color identity, strategy detection, required cuts, collection matching, quality gates, budget, bracket, or pilot intent.",
        "- v1.1 live prompt/report/explanation surfaces active: Yes",
        "- Legacy v0.6.5.1 report guidance counter retained for diagnostics: Yes",
        "- Legacy v0.6.5.3 subtype report summary counter retained for diagnostics: Yes",
        f"- Report guidance summary available: {'Yes' if context.get('report_guidance_summary') else 'No'}",
        f"- Protect / Question / Prefer summaries available: {'Yes' if context.get('protect_summary') and context.get('question_summary') and context.get('prefer_summary') else 'No'}",
        "- Guidance scope: live v1.1 framing plus legacy/internal light optional-cut and replacement-candidate nudges. Legacy counters are retained for QA visibility and do not represent a competing user-facing philosophy system.",
        f"- Legacy v0.6.6.5 philosophy cut/replacement bias QA active: {'Yes' if context.get('philosophy_bias_foundation_active') else 'No'}",
        f"- Bias profile available: {'Yes' if context.get('cut_bias_protect_roles') or context.get('cut_bias_review_roles') or context.get('replacement_bias_roles') else 'No'}",
        f"- Bias strength: {context.get('bias_strength', 'guidance')}",
        f"- Legacy optional cut-bias currently applied: {'Yes' if context.get('cut_bias_scoring_active') else 'No'}",
        f"- Legacy replacement presentation/order bias currently applied: {'Yes' if context.get('replacement_bias_scoring_active') else 'No'}",
    ]

    if context.get("short_lens_summary"):
        lines.append("- Short lens summary: " + str(context.get("short_lens_summary")))
    if context.get("report_guidance_summary"):
        lines.append("- Report guidance summary: " + str(context.get("report_guidance_summary")))

    if context.get("protect_bias"):
        lines.append("- Protect bias: " + ", ".join(context["protect_bias"][:8]))
    if context.get("review_bias"):
        lines.append("- Review bias: " + ", ".join(context["review_bias"][:8]))
    if context.get("replacement_bias"):
        lines.append("- Replacement bias: " + ", ".join(context["replacement_bias"][:8]))
    if context.get("cut_pressure_notes"):
        lines.append("- Cut-pressure notes:")
        for note in context["cut_pressure_notes"][:5]:
            lines.append(f"  - {note}")

    if context.get("philosophy_bias_foundation_active"):
        lines.extend([
            "",
            "## Legacy Philosophy Bias Foundation Diagnostics",
            "- Legacy v0.6.6.1 bias foundation active: Yes",
            "- Legacy v0.6.6.5 optional-cut / replacement-candidate bias QA active: Yes",
            f"- Bias profile version: {context.get('philosophy_bias_foundation_version', 'v0.6.6.5')}",
            f"- Bias strength: {context.get('bias_strength', 'guidance')}",
            f"- Legacy optional cut-bias currently applied: {'Yes' if context.get('cut_bias_scoring_active') else 'No'}",
        f"- Legacy replacement presentation/order bias currently applied: {'Yes' if context.get('replacement_bias_scoring_active') else 'No'}",
            "- Scope: cut-side bias is a small optional nudge. Replacement bias applies light collection-candidate presentation/order nudges with visibility counters; it is not a hard recommendation override.",
            f"- Protect-biased roles available: {'Yes' if context.get('cut_bias_protect_roles') else 'No'}",
            f"- Review-biased roles available: {'Yes' if context.get('cut_bias_review_roles') else 'No'}",
            f"- Replacement-biased roles available: {'Yes' if context.get('replacement_bias_roles') else 'No'}",
        ])
        if context.get("cut_bias_protect_roles"):
            lines.append("- Protect-biased roles: " + ", ".join(context["cut_bias_protect_roles"][:10]))
        if context.get("cut_bias_review_roles"):
            lines.append("- Review-biased roles: " + ", ".join(context["cut_bias_review_roles"][:10]))
        if context.get("replacement_bias_roles"):
            lines.append("- Replacement-biased roles: " + ", ".join(context["replacement_bias_roles"][:10]))
        if context.get("bias_warning"):
            lines.append("- Bias warning: " + str(context.get("bias_warning")))

    return "\n".join(lines)
