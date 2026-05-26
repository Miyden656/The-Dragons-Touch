"""User-guided prompt builder for The Dragon's Touch.

Patch Batch 1 goal:
- Keep the old seven-section guided workflow, but make it faster to use.
- Force the reviewing assistant to ask for the generated deck report first.
- Use numbered answer choices where possible.
- Preserve separate cut-down and build-up intake flows.

v0.6.5.2 goal:
- Improve philosophy/persona prompt framing.
- Add concise guide introductions without heavy roleplay.
- Keep philosophy guidance separate from legality, strategy, cut, and collection logic.

v0.6.5.2.1 hotfix:
- Render answer choices as bullets so receiving assistants do not flatten nested numbered lists.

v0.6.5.2.2 polish:
- Render answer choices as plain `number = choice` lines, without bullets.

v0.6.5.4 polish:
- Make philosophy/persona prompt behavior more showcase-ready across lenses.
- Add explicit partial-answer clarification rules.
- Keep prompt QA guidance separate from mechanical scoring.

v0.6.8.1 polish:
- Clean final user-guided prompt wording before the stable v0.6 lock.
- Replace internal "script" phrasing with Dragon's Touch wording.
- Keep workflow behavior unchanged.

v0.6.8.1.1 hotfix:
- Indent answer choices consistently under their questions.
- Carry UI/runtime bracket, budget, collection mode, and collection source context into the guided prompt.
- Keep prompt behavior and backend analysis logic unchanged.

v0.6.8.2 polish:
- Remove repeated Section 1 review-outcome confirmation.
- Reference staged Review Intensity / Build-Up Mode in Section 1.
- Restore clean Game Changer / fast mana / tutor / free interaction option formatting.

v0.6.8.3 boundary cleanup (carried into v0.6.8.4 regression pass):
- Keep prompt wording aligned with final user-facing boundaries without changing prompt workflow behavior.

v1.1.17.3 direct cleanup:
- Suppress legacy v0.6.5.x prompt philosophy sections when the new v1.1 Philosophy / Persona Guidance block renders.
- Keep legacy philosophy prompt sections only as a fallback if the v1.1 handoff block cannot render.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_io.output_writer import get_unique_output_path, write_text_file
from reports.strategy_knowledge_sections import build_strategy_knowledge_prompt_block  # v1.4.13 Strategy Knowledge AI handoff
from analysis.deck_building_philosophies import (
    render_philosophy_prompt_questions,
    render_philosophy_prompt_showcase_block,
)


BRACKET_OPTIONS = """1. Exhibition / Bracket 1 — very casual, theme-first, intentionally low pressure.
2. Core / Bracket 2 — normal casual Commander with functional decks but limited pressure.
3. Upgraded / Bracket 3 — tuned casual with stronger cards, clearer engines, and better interaction.
4. Optimized / Bracket 4 — high-power, efficient, consistent, and often bracket-pressure aware.
5. cEDH / Bracket 5 — competitive EDH expectations; fast, efficient, and win-focused."""

TABLE_EXPERIENCE_OPTIONS = """1. Proactive combat-focused table experience
2. Big splashy Commander moments
3. Synergy engine / value puzzle
4. Political or table-shaping gameplay
5. Lower-pressure casual fun
6. High-power tuned gameplay
7. Theme / flavor-first experience
8. Other — please describe"""

COMMANDER_NEEDS_OPTIONS = """1. Ramp / mana acceleration
2. Card draw or card selection
3. Protection / ways to keep the commander alive
4. Cheap enablers that make the commander work
5. Payoffs that convert the commander engine into a win
6. Removal / interaction
7. Token production or bodies
8. Recursion / graveyard support
9. Mana fixing / better curve support
10. Other — please describe"""

PACKAGE_DEFINITION_NOTE = """Use the deck report as evidence, but let the pilot override it. Packages are groups of cards that work together, such as ramp, typal support, sacrifice outlets, token makers, landfall enablers, wheels, draw-punishers, protection, copy effects, or combo pieces. Play pattern means how the pilot wants games to feel and unfold; that stays player-defined."""

PROMPT_FORMATTING_RULE = """Formatting rule for the reviewing assistant: Keep each question separate. Render answer choices as indented plain option lines like `   1 = choice`, with no bullet dots and no nested numbered lists. If the pilot partially answers a section, ask only for the missing or unclear items from that section."""



# -----------------------------
# Small formatting helpers
# -----------------------------

# v0.6.5.2.2: Keep fast numbered answers while avoiding nested Markdown numbering.
BRACKET_OPTIONS = """1. Exhibition / Bracket 1 — very casual, theme-first, intentionally low pressure.
2. Core / Bracket 2 — normal casual Commander with functional decks but limited pressure.
3. Upgraded / Bracket 3 — tuned casual with stronger cards, clearer engines, and better interaction.
4. Optimized / Bracket 4 — high-power, efficient, consistent, and often bracket-pressure aware.
5. cEDH / Bracket 5 — competitive EDH expectations; fast, efficient, and win-focused."""
TABLE_EXPERIENCE_OPTIONS = """1. Proactive combat-focused table experience
2. Big splashy Commander moments
3. Synergy engine / value puzzle
4. Political or table-shaping gameplay
5. Lower-pressure casual fun
6. High-power tuned gameplay
7. Theme / flavor-first experience
8. Other — please describe"""
COMMANDER_NEEDS_OPTIONS = """1. Ramp / mana acceleration
2. Card draw or card selection
3. Protection / ways to keep the commander alive
4. Cheap enablers that make the commander work
5. Payoffs that convert the commander engine into a win
6. Removal / interaction
7. Token production or bodies
8. Recursion / graveyard support
9. Mana fixing / better curve support
10. Other — please describe"""
PACKAGE_DEFINITION_NOTE = """Use the deck report as evidence, but let the pilot override it. Packages are groups of cards that work together, such as ramp, typal support, sacrifice outlets, token makers, landfall enablers, wheels, draw-punishers, protection, copy effects, or combo pieces. Play pattern means how the pilot wants games to feel and unfold; that stays player-defined."""
PROMPT_FORMATTING_RULE = """Formatting rule for the reviewing assistant: Keep each question separate. Render answer choices as indented plain option lines like `   1 = choice`, with no bullet dots and no nested numbered lists. If the pilot partially answers a section, ask only for the missing or unclear items from that section."""

def _philosophy_intro_instruction(context: dict[str, Any]) -> str:
    philosophy = context.get("philosophy_context") or {}
    guide_name = philosophy.get("guide_name")
    guide_role = philosophy.get("guide_role") or "Guide"
    label = philosophy.get("label") or "Balanced / Unknown"
    core_question = philosophy.get("core_question") or "What does this deck want to do?"
    tone = philosophy.get("tone") or "clear, practical, and supportive"
    lens_summary = philosophy.get("short_lens_summary") or philosophy.get("rules_summary") or "Use this lens as review framing only."

    if guide_name:
        return (
            f"After receiving the deck report, confirm receipt and briefly introduce the selected philosophy guide as "
            f"{guide_name}, {guide_role}. Use exactly 2 to 4 sentences. State that the review will use the "
            f"{label} lens, whose guiding question is: '{core_question}'. In plain language, frame the lens as: {lens_summary} "
            f"Keep the tone {tone}. Do not write in first person as the persona, do not roleplay a scene, and do not let the persona override the pilot, legality, deck size, color identity, collection mode, or the report evidence."
        )
    return (
        f"After receiving the deck report, confirm receipt and briefly introduce the selected philosophy lens: {label}. "
        f"Use exactly 2 to 4 sentences. Explain that this lens guides tone and priorities, but does not override pilot intent, legality, deck size, color identity, collection mode, or strategy evidence. Lens summary: {lens_summary}"
    )

def _philosophy_prompt_behavior_block(context: dict[str, Any]) -> list[str]:
    philosophy = context.get("philosophy_context") or {}
    if not philosophy:
        return []

    guide_name = philosophy.get("guide_name")
    guide_role = philosophy.get("guide_role") or "Guide"
    label = philosophy.get("label") or "Balanced / Unknown"
    core_question = philosophy.get("core_question") or "What does this deck want to do?"
    core_philosophy = philosophy.get("core_philosophy") or "Use the selected lens to frame the review."
    rules_summary = philosophy.get("rules_summary") or "Use the selected lens as guidance only."
    tone = philosophy.get("tone") or "clear, practical, and supportive"
    example_language = philosophy.get("example_language")

    short_lens_summary = philosophy.get("short_lens_summary")
    report_guidance_summary = philosophy.get("report_guidance_summary")
    protect_summary = philosophy.get("protect_summary")
    question_summary = philosophy.get("question_summary")
    prefer_summary = philosophy.get("prefer_summary")
    pilot_override_note = philosophy.get("pilot_override_note")

    lines = [
        "## v0.6.5.4 Philosophy / Persona Prompt Behavior",
        "",
        f"- Selected lens: {label}",
        f"- Guide/persona: {guide_name or 'No named guide'}{f' — {guide_role}' if guide_name else ''}",
        f"- Guiding question: {core_question}",
        f"- Core philosophy: {core_philosophy}",
        f"- Review summary: {rules_summary}",
        f"- Tone target: {tone}",
    ]

    if short_lens_summary:
        lines.append(f"- Showcase lens summary: {short_lens_summary}")
    if report_guidance_summary:
        lines.append(f"- How to use this lens: {report_guidance_summary}")
    if protect_summary:
        lines.append(f"- Protect emphasis: {protect_summary}")
    if question_summary:
        lines.append(f"- Question/review emphasis: {question_summary}")
    if prefer_summary:
        lines.append(f"- Replacement framing: {prefer_summary}")
    if pilot_override_note:
        lines.append(f"- Pilot override note: {pilot_override_note}")

    lines.extend([
        "",
        "How the reviewing assistant should use this lens:",
        "1. Use the philosophy to shape explanation style, protection language, review priorities, and recommendation framing.",
        "2. Do not use the philosophy to override legality, deck-size rules, color identity, commander legality, companion restrictions, collection mode, budget, or required cuts.",
        "3. Do not use the philosophy to invent a new primary strategy if the pilot has not confirmed it.",
        "4. Do not roleplay as the guide in first person. The guide is a mentor frame, not a character scene.",
        "5. Keep guide/persona references short: introduce the lens once, then use normal deck-review language.",
        "6. If pilot answers conflict with the selected philosophy, pilot intent wins and the final summary should mention the shift.",
        "7. If the selected lens is Balanced / Unknown, stay exploratory and avoid making subtype-specific assumptions.",
        "8. Keep the final review grounded in the deck report and the pilot's section answers; do not turn the philosophy lens into a separate roleplay voice.",
    ])

    protect = philosophy.get("protect_bias") or []
    review = philosophy.get("review_bias") or []
    replace = philosophy.get("replacement_bias") or []
    cut_notes = philosophy.get("cut_pressure_notes") or []

    if protect:
        lines.append("- Philosophy tends to protect: " + ", ".join(protect[:8]))
    if review:
        lines.append("- Philosophy tends to question: " + ", ".join(review[:8]))
    if replace:
        lines.append("- Philosophy replacement framing prefers: " + ", ".join(replace[:8]))
    if cut_notes:
        lines.append("- Philosophy cut-pressure reminders:")
        lines.extend(f"  - {note}" for note in cut_notes[:5])
    if example_language:
        lines.extend(["", "Example tone to emulate:", f"> {example_language}"])

    return lines

def _v1117_live_philosophy_handoff_block(context: dict[str, Any]) -> str:
    """Build the v1.1 Philosophy / Persona Guidance block for live prompt output.

    This is prompt-text wiring only. It does not change deck analysis, cut scoring,
    replacement scoring, card selection, report generation, or UI behavior.
    """
    try:
        from philosophy.prompt_injection import build_philosophy_handoff_block
    except Exception:
        return ""

    runtime_config = context.get("runtime_config")
    philosophy_context = context.get("philosophy_context") or {}

    config = {
        "philosophy_lens": _v1117_canonical_lens_from_legacy_context(context),
        "guide_presentation": _v1117_guide_presentation_from_runtime(context),
        "budget_note": getattr(runtime_config, "budget_note", None),
        "intended_bracket": getattr(runtime_config, "intended_bracket", None),
        "combo_tolerance": "Combo awareness enabled" if getattr(runtime_config, "combo_awareness_enabled", False) else None,
    }

    if isinstance(philosophy_context, dict):
        # Carry the existing concise philosophy summary as pilot/context notes.
        summary = philosophy_context.get("lens_summary") or philosophy_context.get("rules_summary")
        if summary:
            config["pilot_notes"] = str(summary)

    try:
        block = build_philosophy_handoff_block(config)
    except Exception:
        return ""

    if "# Philosophy / Persona Guidance" not in block:
        return ""

    return block.rstrip()
