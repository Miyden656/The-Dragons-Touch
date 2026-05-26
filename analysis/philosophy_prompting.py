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

def render_philosophy_prompt_showcase_block(context: dict) -> str:
    """Render v0.6.5.4 prompt-facing philosophy QA / showcase guidance.

    This block is meant for the AI that receives the generated user-guided prompt.
    It keeps guide/persona behavior consistent across lenses and remains
    guidance-only: no scoring, legality, strategy, or collection logic changes.
    """
    if not context:
        return ""

    guide = _guide_display_name(context)
    lens = context.get("label", "Balanced / Unknown")
    role = context.get("guide_role", "Guide")
    question = context.get("core_question", "What does this deck want to do?")
    short_summary = context.get("short_lens_summary") or context.get("rules_summary", "Use this lens as review framing only.")
    report_guidance = context.get("report_guidance_summary") or context.get("rules_summary", "Use this lens to shape review language and priorities.")
    protect = context.get("protect_summary") or _comma_list(context.get("protect_bias", []), 6)
    review = context.get("question_summary") or _comma_list(context.get("review_bias", []), 6)
    prefer = context.get("prefer_summary") or _comma_list(context.get("replacement_bias", []), 6)
    pilot_override = context.get("pilot_override_note") or "Pilot-stated intent beats the philosophy lens when they conflict."

    lines = [
        "## v0.6.5.4 Philosophy Prompt QA / Showcase Polish",
        "",
        f"- Lens: {lens}",
        f"- Guide frame: {guide} — {role}",
        f"- Guiding question: {question}",
        f"- One-sentence lens summary: {short_summary}",
        "",
        "Use this lens in the guided review as follows:",
        f"1. Read cards through this lens: {report_guidance}",
        f"2. Protect or lower cut pressure for: {protect}.",
        f"3. Question or review more carefully: {review}.",
        f"4. Prefer recommendations that support: {prefer}.",
        f"5. Pilot override rule: {pilot_override}",
        "6. Introduce the guide/lens once after the deck report, then continue as a practical deck-review assistant.",
        "7. Do not use the guide as a roleplay character, speaking persona, or substitute for strategy evidence.",
        "8. If the pilot gives a partial section answer, ask only for the missing or unclear items from that section before moving on.",
    ]

    return "\n".join(lines)

def render_philosophy_prompt_questions(context: dict) -> str:
    """Render philosophy guidance for the user-guided prompt.

    This function intentionally does not replace the main seven-section workflow.
    It gives the reviewing AI a concise guide/persona frame and a few optional
    philosophy-specific clarifying questions.
    """
    guide = _guide_display_name(context)
    key = context.get("key", "balanced_unknown")

    base = [
        "### Philosophy Guide Context",
        f"Selected lens: {context.get('label', 'Balanced / Unknown')}",
        f"Guide: {guide}",
        f"Guide role: {context.get('guide_role', 'Guide')}",
        f"Primary question: {context.get('core_question', 'What does this deck want to do?')}",
        "",
        "Guide introduction instruction:",
        render_guide_introduction_instruction(context),
        "",
        "Philosophy boundary:",
        "Use this philosophy as a review lens only. Strategy detection, legality, deck size, color identity, budget, combo tolerance, bracket goals, and user answers take priority.",
        "",
        "Optional later philosophy clarification questions if needed; do not ask these before Section 1:",
    ]

    question_map = {
        "balanced_unknown": [
            "1. Do you want to stay Balanced / Unknown, or choose Timmy/Tammy, Johnny/Jenny, Spike, or a subtype?",
            "2. Are you trying to discover the deck's identity, refine it, or optimize it?",
            "3. What kind of experience do you want this deck to create?",
        ],
        "big_moment": [
            "1. What is the one unforgettable play this deck wants to create?",
            "2. Is that moment supposed to win the game, or is a memorable story enough?",
            "3. Which cards directly create, protect, or amplify that moment?",
        ],
        "pet_card": [
            "1. Which cards are protected because they matter personally?",
            "2. Are those cards protected permanently, or only until they create the desired moment once?",
            "3. How much performance cost are you willing to accept for those cards?",
        ],
        "commander_exploiter": [
            "1. What specific commander text are you trying to exploit?",
            "2. Which cards look weak generally but become important because of the commander?",
            "3. Should generic good cards lose priority if they do not support the commander’s specific plan?",
        ],
        "combo_builder": [
            "1. Are there known combos you want to include?",
            "2. Are infinite combos welcome, restricted, or unwanted?",
            "3. Should the combo be the main win condition or a backup plan?",
            "4. Do you prefer compact combos or multi-piece interaction chains?",
        ],
        "power_level_calibrator": [
            "1. What kind of table is this deck meant for?",
            "2. Are infinites, tutors, fast mana, or stax acceptable?",
            "3. Should the deck be stronger, softer, or better matched?",
            "4. Are there cards you want to avoid because they create bad table experiences?",
        ],
        "interaction_controller": [
            "1. What types of threats does your table usually present?",
            "2. What does this deck currently struggle to answer?",
            "3. Should interaction be proactive and synergy-friendly, or are pure answers acceptable?",
        ],
    }

    questions = question_map.get(key, [
        f"1. Through the {context.get('label', 'selected')} lens, what matters most to preserve?",
        "2. What kinds of cards should receive lower cut pressure?",
        "3. What kinds of cards should be reviewed more aggressively?",
    ])

    return "\n".join(base + questions)
