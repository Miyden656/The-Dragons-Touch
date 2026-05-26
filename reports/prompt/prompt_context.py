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

def _collection_context_summary(context: dict[str, Any]) -> str:
    runtime_config = context.get("runtime_config")
    collection_summary = context.get("collection_summary")
    mode = getattr(runtime_config, "collection_mode", "none") if runtime_config is not None else "none"
    source_mode = getattr(runtime_config, "collection_source_mode", "none") if runtime_config is not None else "none"
    source_path = getattr(runtime_config, "collection_file", "") if runtime_config is not None else ""
    loaded = getattr(collection_summary, "loaded", False) if collection_summary is not None else False
    unique = getattr(collection_summary, "unique_cards", 0) if collection_summary is not None else 0
    files = getattr(runtime_config, "collection_files", ()) if runtime_config is not None else ()
    return f"mode={mode}; source={source_mode}; path={source_path or 'not provided'}; files={len(files or ())}; loaded={'yes' if loaded else 'no'}; unique_owned_names={unique}"

def _collection_prompt_context_block(context: dict[str, Any]) -> list[str]:
    collection_summary = context.get("collection_summary")
    collection_candidates = context.get("collection_candidates")
    runtime_config = context.get("runtime_config")
    mode = getattr(collection_candidates, "mode", None) or getattr(collection_summary, "mode", None) or getattr(runtime_config, "collection_mode", "none")
    if mode == "none" and not collection_summary and not collection_candidates:
        return []

    lines = [
        "",
        "## Collection Pull Context",
        "",
        f"- Collection mode: {mode}",
    ]
    if collection_summary:
        lines.extend([
            f"- Collection loaded: {'Yes' if getattr(collection_summary, 'loaded', False) else 'No'}",
            f"- Total owned cards loaded: {getattr(collection_summary, 'total_cards', 0)}",
            f"- Unique owned card names: {getattr(collection_summary, 'unique_cards', 0)}",
            f"- Selected collection files: {len(getattr(collection_summary, 'selected_files', []) or [])}",
        ])
    if collection_candidates:
        lines.extend([
            f"- Strong owned candidates in report: {len(getattr(collection_candidates, 'strong_candidates', []) or [])}",
            f"- Possible owned candidates in report: {len(getattr(collection_candidates, 'possible_candidates', []) or [])}",
            f"- Shakeup candidates in report: {len(getattr(collection_candidates, 'shakeup_candidates', []) or [])}",
        ])
        no_fit = list(getattr(collection_candidates, 'no_strong_fit_categories', []) or [])
        if no_fit:
            lines.append("- Replacement categories with no strong owned fit: " + ", ".join(no_fit[:8]))
    lines.extend([
        "",
        "Collection-review rules for the reviewing assistant:",
        "1. Treat collection candidates as review candidates, not automatic upgrades or automatic swaps.",
        "2. In collection-only mode, do not recommend non-owned cards as if they are available from the user's collection.",
        "3. If no owned card is a strong fit for a role, say that clearly instead of forcing a weak recommendation.",
        "4. Use Strong Owned Candidates first, but still confirm they actually improve the pilot's stated plan.",
        "5. Use Possible Owned Candidates only after warning that they require pilot review.",
        "6. Use Shakeup Candidates only if the pilot asks for experiments or a shakeup; do not frame them as upgrades.",
        "7. Do not create exact one-for-one swaps unless the deck report and pilot intent make the swap clearly justified.",
    ])
    return lines

def _script_context_block(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    original_runtime_config = context.get("original_runtime_config", runtime_config)
    strategy = context["strategy_summary"]
    cut_pressure = context["cut_pressure"]
    replacement = context["replacement_needs"]
    completion = context.get("deck_completion")

    lines = [
        "## Dragon's Touch Review Context",
        "",
        f"- Command zone card(s): {parsed.commander_name}",
        f"- Prompt mode: {runtime_config.prompt_interaction_mode}",
        f"- Review direction: {runtime_config.review_direction}",
        f"- Auto-batch selected this direction from deck size: {'Yes' if getattr(original_runtime_config, 'review_direction', '') == 'batch_auto' else 'No'}",
        f"- Dragon's Touch reported primary strategy: {strategy.primary_strategy}",
        f"- Dragon's Touch reported secondary strategy: {strategy.secondary_strategy}",
        f"- Deck size status: {cut_pressure.status}",
        f"- Current deck size: {cut_pressure.deck_card_count}",
        f"- Required cuts: {cut_pressure.required_cuts}",
        (f"- Optional cut target setting: {runtime_config.cut_depth_config.get('optional_cut_target', 0)} (paused while deck is under 100; addition-first review is active)" if cut_pressure.deck_card_count < 100 else f"- Optional cut target: {runtime_config.cut_depth_config.get('optional_cut_target', 0)}"),
        f"- Collection mode: {getattr(runtime_config, 'collection_mode', 'none')}",
        f"- Intended bracket from UI/runtime: {getattr(runtime_config, 'intended_bracket', 'Not provided')}",
        f"- Budget note from UI/runtime: {getattr(runtime_config, 'budget_note', 'Not provided')}",
    ]

    if getattr(original_runtime_config, "review_direction", "") == "batch_auto":
        lines.append(f"- Auto-batch source: deck size ({parsed.deck_card_count} main-deck cards)")
        lines.append("- Auto-batch note: review direction/build-up level were detected per deck; cut strictness, prompt mode, philosophy, guide style, and collection behavior came from global run settings.")
    if runtime_config.review_direction == "build_up":
        lines.append(f"- Build-up mode: {runtime_config.build_up_config.get('label', 'Not applicable')}")
        if completion:
            lines.append(f"- Cards needed to reach 100: {completion.cards_needed}")
    else:
        lines.append(f"- Cut depth mode: {runtime_config.cut_depth_config.get('mode', 'normal')}")
        note = runtime_config.cut_depth_config.get("auto_batch_pool_note")
        if note:
            lines.append(f"- Auto-batch pool note: {note}")

    if replacement.priority_categories:
        lines.extend(["", "Dragon's Touch reported replacement/addition categories:"])
        lines.extend(f"- {category}" for category in replacement.priority_categories)

    core_packages = []
    for candidate in getattr(strategy, "candidates", [])[:6]:
        name = getattr(candidate, "name", None) or getattr(candidate, "strategy", None)
        if name:
            core_packages.append(str(name))
    if core_packages:
        lines.extend(["", "Dragon's Touch visible packages / themes:"])
        lines.extend(f"- {package}" for package in core_packages)

    return lines

def _v1117_canonical_lens_from_legacy_context(context: dict[str, Any]) -> str:
    """Resolve the v1.1 philosophy lens from existing v0.x runtime/context data."""
    philosophy_context = context.get("philosophy_context") or {}
    runtime_config = context.get("runtime_config")

    # Prefer the already-rendered legacy label because it is user-facing/canonical.
    if isinstance(philosophy_context, dict):
        label = philosophy_context.get("label")
        if label:
            return str(label)

        key = philosophy_context.get("key")
        legacy_key_map = {
            "balanced_unknown": "Balanced / Unknown",
            "timmy_tammy": "Timmy / Tammy",
            "johnny_jenny": "Johnny / Jenny",
            "spike": "Spike",
            "big_moment": "Big Moment",
            "big_creature_stompy": "Big Creature / Stompy",
            "theme_vibe": "Theme / Vibe",
            "pet_card": "Pet Card",
            "let_me_do_my_thing": "Let Me Do My Thing",
            "battlecruiser": "Battlecruiser",
            "engine_builder": "Engine Builder",
            "commander_exploiter": "Commander Exploiter",
            "weird_card_rescuer": "Weird Card Rescuer",
            "theme_mechanic_inventor": "Theme Mechanic Inventor",
            "self_imposed_constraint_builder": "Self-Imposed Constraint Builder",
            "combo_builder": "Combo Builder",
            "consistency_maximizer": "Consistency Maximizer",
            "efficiency_optimizer": "Efficiency Optimizer",
            "curve_and_mana_discipline": "Curve and Mana Discipline",
            "competitive_closer": "Competitive Closer",
            "power_level_calibrator": "Power-Level Calibrator",
            "interaction_controller": "Interaction Controller",
        }
        if key in legacy_key_map:
            return legacy_key_map[key]

    runtime_key = getattr(runtime_config, "philosophy_key", None)
    if runtime_key:
        return {
            "balanced_unknown": "Balanced / Unknown",
            "timmy_tammy": "Timmy / Tammy",
            "johnny_jenny": "Johnny / Jenny",
            "spike": "Spike",
        }.get(str(runtime_key), str(runtime_key))

    return "Balanced / Unknown"
