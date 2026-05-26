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

def _option_block(options: str, indent: str = "   ") -> str:
    """Render numbered choices as indented plain `number = choice` lines.

    This keeps the fast numbered-answer workflow while avoiding nested Markdown
    numbering, avoiding visible bullet dots, and making each answer choice sit
    visually under the question that owns it.
    """
    lines: list[str] = []
    for raw in (options or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if ". " in line:
            number, text = line.split(". ", 1)
            if number.isdigit():
                lines.append(f"{indent}{number} = {text}")
                continue
        lines.append(f"{indent}{line}" if indent and not line.startswith(indent) else line)
    return "\n".join(lines)

def _yes_no_direction_options() -> str:
    return _option_block("""1. Yes, the Dragon's Touch review direction is correct.
2. No — I want the other review direction instead. Please state build-up/completion or cut-down/tuning.""")

def _review_outcome_confirmation_options(current_direction: str) -> str:
    if current_direction == "build_up":
        return _option_block("""1. Yes — use the current build-up / completion plan.
2. Change this into a cut-down / tuning review.
3. I am not sure — help me choose the right review direction.""")
    return _option_block("""1. Yes — use the current cut-down / tuning plan.
2. Change this into a build-up / completion review.
3. I am not sure — help me choose the right review direction.""")

def _runtime_value(context: dict[str, Any], name: str, fallback: str = "Not provided") -> str:
    runtime_config = context.get("runtime_config")
    value = getattr(runtime_config, name, None) if runtime_config is not None else None
    text = str(value or "").strip()
    return text or fallback

def _main_goal_cut_options() -> str:
    return _option_block("""1. Legal cuts — identify cuts needed to make the deck legal.
2. Optimization — improve a legal deck without treating changes as mandatory.
3. Strategy correction — fix the Dragon's Touch strategy read if the deck plan is wrong.
4. Additions / replacements — identify what kinds of cards would help.
5. Playtest notes — focus on what to watch in future games.""")

def _help_depth_options() -> str:
    return _option_block("""1. Light touch — only obvious issues.
2. Normal tuning — practical review with a few useful candidates.
3. Strict optimization — challenge more slots and tighten the deck.
4. Brutal / deep review — broad diagnostic with many review points.
5. Rebuild-level review — treat the list as a rough pool and reshape around the stated plan.""")

def _build_goal_options() -> str:
    return _option_block("""1. This is correct.
2. No, Build from Scratch — Commander(s) only; create a complete plan and card recommendation path.
3. No, Point me in the right direction — the deck needs 30+ cards and mainly needs structure.
4. No, Help me get there — the deck needs 11 to 30 cards and needs role completion.
5. No, Finalize — the deck needs 10 or fewer cards and needs finishing touches.""")

def _commander_role_options() -> str:
    return _option_block("""1. Engine — the commander repeatedly generates the deck's main advantage.
2. Payoff — the commander rewards the deck for doing its thing.
3. Support piece — the commander helps the plan but is not the whole plan.
4. Finisher — the commander is how the deck closes games.
5. Color identity only — the commander mainly provides colors or theme.""")

def _cut_candidate_visibility_options() -> str:
    return _option_block("""1. Only stronger candidates.
2. Include low-confidence / manual-review candidates too.""")

def _bracket_pressure_cut_options() -> str:
    return _option_block("""1. Yes, review bracket-pressure cards as possible cuts if they exceed my table goal.
2. No, treat bracket-pressure cards as table-fit notes only unless they are also off-plan.""")

def _preferred_output_options() -> str:
    return _option_block("""1. Recommended Cuts — strongest cut recommendations only.
2. Possible Cuts — broader review list with caveats.
3. Playtest Guide — what to watch before cutting.
4. Protected Cards — focus on what should not be cut.
5. Full diagnostic — show strategy, cuts, protected cards, replacements, and playtest notes.""")

def _replacement_preference_options(include_replacements: bool = True) -> str:
    if not include_replacements:
        return _option_block("""1. Categories only — describe what roles the deck needs.
2. Exact cards when obvious — only recommend exact cards when the fit is very clear.
3. Exact cards welcome — recommend specific card names freely.
4. Suggestions for later — finish the plan first, then suggest cards later.""")
    return _option_block("""1. No replacements.
2. Categories only.
3. Exact cards when obvious — specific card names only when the role fit is clear.
4. Exact cards welcome.
5. Suggestions for later.""")

def _replacement_source_options() -> str:
    return _option_block("""1. My collection / card pool.
2. Full Magic card pool.""")

def _combo_welcome_options() -> str:
    return _option_block("""1. Welcome.
2. Acceptable but not preferred.
3. Only if they require 3+ cards.
4. Unwanted.
5. Other — please describe.""")

def _combo_avoidance_options() -> str:
    return _option_block("""1. Yes.
2. No.
3. Case-by-case.""")

def _game_changer_acceptance_options() -> str:
    return _option_block("""1. Yes.
2. No.
3. Some / case-by-case.
4. Explain.""")

def _build_recommendation_preference_options() -> str:
    return _option_block("""1. Categories only.
2. Exact cards when obvious.
3. Exact cards welcome.
4. Suggestions for later.""")

def _optional_upgrade_recommendation_options() -> str:
    return _option_block("""1. Yes.
2. No, additions only.
3. Only if the cut is very obvious.""")

def _optimization_cut_count_options() -> str:
    return _option_block("""1. 3–5
2. 6–9
3. 10–14
4. None unless required for legality.""")

def _required_vs_optional_cut_options() -> str:
    return _option_block("""1. Required legal cuts only.
2. Optional upgrades only.
3. Both required cuts and optional upgrades.
4. Not sure — use the deck report's deck-size status.""")

def _priority_options() -> str:
    return "Choose 1 to 2 priorities:\n" + _option_block("""1. Synergy — strongest fit with the commander and primary plan.
2. Consistency — make the deck do its thing more often.
3. Bracket limits / power fit — keep the deck inside the intended table range.
4. Budget — respect price limits.
5. Flavor — preserve theme, story, or vibe.
6. Table friendliness — avoid cards that create the wrong table experience.""")

def _final_output_style_options() -> str:
    return _option_block("""1. Short list — concise recommendations only.
2. Full report — complete reasoning and sections.
3. Strategy review — focus on plan, packages, and identity.
4. Cut-only — only cuts and why.
5. Replacement-focused — focus on what to add or swap.
6. Playtest notes — focus on what to test in games.
7. Prompt for another AI — produce a clean follow-up prompt.
8. Batch QA / bug review — focus on whether the Dragon's Touch output looks wrong.""")

def _safe_list(items: list[str], fallback: str = "None reported") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)

def _global_prompt_rules(context: dict[str, Any]) -> list[str]:
    return [
        "## Required Workflow Rules for the Reviewing Assistant",
        "",
        "1. First, ask the pilot to paste or upload the generated deck report. Do not begin Section 1 until the report is provided.",
        "2. After the deck report is provided, confirm receipt and give a brief initial summary of what the report appears to say.",
        f"3. {_philosophy_intro_instruction(context)}",
        "4. After the philosophy/guide introduction, immediately ask Section 1 only. Do not ask multiple sections at once in interactive mode.",
        "5. The pilot may answer using just numbers, short phrases, or N/A. Accept numbered answers without forcing long explanations.",
        "6. If the pilot answers only part of a section, ask only for the missing or unclear items from that same section before summarizing and moving on.",
        "7. After each completed section, summarize the pilot's answers in 3 to 6 bullets, then immediately ask the next section.",
        "8. Preserve deck-report terms and separators when summarizing, such as Token Combat / Go-Wide-Go-Tall, ETB Control / Flicker Control, and collection-only.",
        "9. Use the selected philosophy as a review lens only: tone, priorities, protection language, and framing. Do not let it override mechanical facts.",
        "10. Do not make final cut, addition, or replacement recommendations until all required sections are complete.",
        "11. Do not assume Dragon's Touch strategy read is correct if the pilot corrects it.",
        "12. Separate required legality cuts from optional optimization cuts.",
        "13. Do not recommend cutting cards the pilot refuses to cut.",
        "14. Treat bracket pressure as table-fit information, not an automatic cut.",
        "15. Do not recommend cards already in the deck unless the card is a legal duplicate exception.",
        "16. Before final recommendations, provide a full intent summary titled '<Commander Name> Review Intent Summary' and ask the pilot to confirm or correct it.",
        "17. Only after confirmation should you produce the final recommendations in the user's selected output style.",
        "18. If Collection Pull Candidates are present, treat them as review candidates. Strong means review first, Possible means pilot review required, and Shakeup means experiment only.",
        "19. If collection-only mode is active, do not present outside-card suggestions as owned or available from the selected collection.",
        "20. If the collection does not contain a strong fit for a role, say so directly and do not force a weak owned-card recommendation.",
    ]

def _v1117_guide_presentation_from_runtime(context: dict[str, Any]) -> str:
    """Map the existing guide preference values into the v1.1 guide presentation enum."""
    runtime_config = context.get("runtime_config")
    raw = str(getattr(runtime_config, "guide_preference", "") or "").strip().lower()

    if raw in {"none", "no_named_guide", "no named guide", "off", "false"}:
        return "no_named_guide"
    if raw in {"masculine", "feminine", "either"}:
        return raw
    if raw in {"random", ""}:
        return "either"
    return raw
