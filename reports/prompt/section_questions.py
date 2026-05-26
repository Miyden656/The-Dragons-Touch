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

def _cut_down_sections(context: dict[str, Any], worksheet: bool = False) -> str:
    strategy = context["strategy_summary"]
    cut_pressure = context["cut_pressure"]

    prefix = "Answer all sections below in one reply. Short answers, numbers, and N/A are fine." if worksheet else "Ask only Section 1 first. After the pilot answers, summarize Section 1 briefly and then ask Section 2. Continue one section at a time."
    cut_review_optional_text = (
        f"optional review paused while under 100; requested optional target: {getattr(cut_pressure, 'optional_cut_target', 'see report')}"
        if getattr(cut_pressure, "deck_card_count", 0) < 100
        else f"optional target: {getattr(cut_pressure, 'optional_cut_target', 'see report')}"
    )

    return f"""
## Cut-Down / Tuning Guided Flow

{prefix}

{PROMPT_FORMATTING_RULE}

### Section 1 — Main Review Goal
1. Is the Dragon's Touch review direction correct? Current Dragon's Touch direction: **cut_down / tuning**.
{_yes_no_direction_options()}

2. What do you want from this review?
{_main_goal_cut_options()}

3. Confirm or correct the Review Setup intensity. Current Dragon's Touch Review Intensity: **{context["runtime_config"].cut_depth_config.get("mode", "normal")}**. Use the current intensity unless you want a different review depth.
{_help_depth_options()}

### Section 2 — Commander Role
1. Is the commander the...?
{_commander_role_options()}

2. What does the commander need the rest of the deck to provide? Choose all that apply, or choose Other and describe.
{COMMANDER_NEEDS_OPTIONS}

3. Are there commander-specific cards that look weak but are important? Answer with card names, N/A, or a short explanation.

### Section 3 — Commander Plan / Deck Identity
1. What do you want this commander or deck to do when it is working correctly?

2. Is the reported primary strategy correct? Dragon's Touch reports: **{strategy.primary_strategy}**. If not, what should it be?

3. Is the reported secondary strategy correct? Dragon's Touch reports: **{strategy.secondary_strategy}**. If not, what should it be?

4. Are there specific mechanics, themes, packages, or play patterns you want to preserve?

5. How should the deck usually win? Keep this player-defined.

### Section 4 — Protected / Pet / Build-Around Intent
If nothing applies, **No**, **N/A**, or **None** can cover this whole section.

1. Cards you refuse to cut:
2. Pet cards you want protected:
3. Cards you want to build around:
4. Cards you are uncertain about:
5. Cards you specifically want reviewed:

### Section 5 — Bracket / Table Intent
1. Confirm or correct the intended bracket. Current UI/runtime intended bracket: **{_runtime_value(context, "intended_bracket", "Not sure yet")}**.
{BRACKET_OPTIONS}

2. Budget/table boundary note from UI/runtime: **{_runtime_value(context, "budget_note", "No budget note provided")}**. Confirm, correct, or add any table/budget boundary the review should respect.

3. Are Game Changers, fast mana, efficient tutors, or free interaction acceptable?
{_game_changer_acceptance_options()}

4. Are infinite combos or near-combos welcome?
{_combo_welcome_options()}

5. Should replacements avoid adding or completing combos unless you explicitly want that?
{_combo_avoidance_options()}

6. What kind of table experience should this deck create?
{TABLE_EXPERIENCE_OPTIONS}

### Section 6 — Cut Philosophy
1. Is the cut review from the deck report correct? The report says: **{cut_pressure.status}; required cuts: {cut_pressure.required_cuts}; {cut_review_optional_text}**.
Optional: enter a specific number of cuts you want reviewed. N/A or no answer means the report's range is fine.

2. Are we making required cuts, optional upgrades, or both?
{_required_vs_optional_cut_options()}

3. Should the review show only stronger candidates or include low-confidence/manual-review candidates?
{_cut_candidate_visibility_options()}

4. Should bracket-pressure cards be reviewed as possible cuts if they exceed your table goal?
{_bracket_pressure_cut_options()}

5. Preferred cut output:
{_preferred_output_options()}

### Section 7 — Replacement Philosophy
1. Replacement preference:
{_replacement_preference_options(True)}

2. Replacement source. Current Dragon's Touch collection setting: **{_collection_context_summary(context)}**.
{_replacement_source_options()}

3. Budget limit. Current UI/runtime budget note: **{_runtime_value(context, "budget_note", "No budget note provided")}**. Confirm or correct this budget limit:

4. Priority:
{_priority_options()}

5. Are there cards you already own or do not want recommended?

6. Preferred final output style:
{_final_output_style_options()}

### Collection Pull Handling During Final Recommendations
If the deck report includes **Collection Pull Candidates**, use them as follows:
- Strong Owned Candidates are the best owned fits to review first, not automatic swaps.
- Possible Owned Candidates require pilot review before being treated as upgrades.
- Best Available Collection Shakeup Candidates are experiments only.
- If collection-only mode is active and no owned card is a strong fit for a role, say that clearly.
- If the pilot wants full-card-pool suggestions instead, ask them to confirm that shift before recommending non-owned cards.

### Final Pilot Confirmation Step
After Section 7, provide a full intent summary titled **{context['parsed_deck'].commander_name} Review Intent Summary**. Ask the pilot to confirm or correct the summary before final recommendations. After confirmation, produce the final output based on Section 7, question 6.
""".strip()

def _build_up_sections(context: dict[str, Any], worksheet: bool = False) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    strategy = context["strategy_summary"]
    completion = context.get("deck_completion")
    build_mode = runtime_config.build_up_config.get("mode", "finalize_10_or_less")
    build_label = runtime_config.build_up_config.get("label", "Build-up / completion")
    cards_needed = getattr(completion, "cards_needed", "see report")
    is_scratch = build_mode == "build_from_scratch"

    prefix = "Answer all sections below in one reply. Short answers, numbers, and N/A are fine." if worksheet else "Ask only Section 1 first. After the pilot answers, summarize Section 1 briefly and then ask Section 2. Continue one section at a time."

    if is_scratch:
        section_6 = """### Section 6 — Cut Philosophy
Skip this section because the selected build-up mode is **Build from Scratch — Commander(s) only**. Do not ask optimization-cut questions for a commander-only build. Immediately continue to Section 7."""
        replacement_note = "This is Build from Scratch, so do not frame recommendations as swaps. Focus on building a complete legal 100-card Commander deck."
        replacement_pref_block = f"""1. Build recommendation preference:
{_build_recommendation_preference_options()}"""
    else:
        section_6 = f"""### Section 6 — Cut Philosophy For Optimization
This section is for optional upgrade swaps during build-up. If the pilot wants additions only, they can say so.

1. Do you want optional upgrade recommendations alongside cut suggestions?
{_optional_upgrade_recommendation_options()}

2. How many optimization cut recommendations do you want?
{_optimization_cut_count_options()}

3. Should the review show only stronger candidates or include low-confidence/manual-review candidates?
{_cut_candidate_visibility_options()}

4. Should bracket-pressure cards be reviewed as possible cuts if they exceed your table goal?
{_bracket_pressure_cut_options()}

5. Preferred cut output:
{_preferred_output_options()}"""
        replacement_note = "Because this is not Build from Scratch, replacement questions may apply if existing cards are being upgraded or swapped."
        replacement_pref_block = f"""1. Replacement preference:
{_replacement_preference_options(True)}"""

    return f"""
## Build-Up / Completion Guided Flow

{prefix}

{PROMPT_FORMATTING_RULE}

### Section 1 — Main Review Goal
1. Is the Dragon's Touch review direction correct? Current Dragon's Touch direction: **build_up / completion**.
{_yes_no_direction_options()}

2. Confirm or correct the Build-Up Mode from Review Setup. Current Dragon's Touch build-up mode: **{build_label}**. Cards needed to reach 100: **{cards_needed}**.
{_build_goal_options()}

### Section 2 — Commander Role
1. Is the commander the...?
{_commander_role_options()}

2. What does the commander need the rest of the deck to provide? Choose all that apply, or choose Other and describe.
{COMMANDER_NEEDS_OPTIONS}

### Section 3 — Deck Plan
1. What do you want this commander or deck to do when it is working correctly?

2. Is the reported primary strategy correct? Dragon's Touch reports: **{strategy.primary_strategy}**. If not, what should it be?

3. Is the reported secondary strategy correct? Dragon's Touch reports: **{strategy.secondary_strategy}**. If not, what should it be?

4. Are there specific mechanics, themes, packages, or play patterns you want to build around?

5. How should the deck usually win? Keep this player-defined.

### Section 4 — Protected / Pet / Build-Around Intent
If nothing applies, **No**, **N/A**, or **None** can cover this whole section.

1. Cards you refuse to cut:
2. Pet cards you want protected:
3. Cards you want to build around:
4. Cards you are uncertain about:
5. Cards you specifically want reviewed:

### Section 5 — Bracket / Table Intent
1. Confirm or correct the intended bracket. Current UI/runtime intended bracket: **{_runtime_value(context, "intended_bracket", "Not sure yet")}**.
{BRACKET_OPTIONS}

2. Budget/table boundary note from UI/runtime: **{_runtime_value(context, "budget_note", "No budget note provided")}**. Confirm, correct, or add any table/budget boundary the review should respect.

3. Are Game Changers, fast mana, efficient tutors, or free interaction acceptable?
{_game_changer_acceptance_options()}

4. Are infinite combos or near-combos welcome?
{_combo_welcome_options()}

5. Should replacements avoid adding or completing combos unless you explicitly want that?
{_combo_avoidance_options()}

6. What kind of table experience should this deck create?
{TABLE_EXPERIENCE_OPTIONS}

{section_6}

### Section 7 — Replacement Philosophy, Build Source, and Output Questions
{replacement_note}

{replacement_pref_block}

2. Replacement source, if replacements are relevant. Current Dragon's Touch collection setting: **{_collection_context_summary(context)}**.
{_replacement_source_options()}

3. Build source. Current Dragon's Touch collection setting: **{_collection_context_summary(context)}**.
{_replacement_source_options()}

4. Budget limit. Current UI/runtime budget note: **{_runtime_value(context, "budget_note", "No budget note provided")}**. Confirm or correct this budget limit:

5. Priority:
{_priority_options()}

6. Are there cards you already own or do not want recommended?

7. Preferred final output style:
{_final_output_style_options()}

### Collection Pull Handling During Final Recommendations
If the deck report includes **Collection Pull Candidates**, use them as follows:
- Strong Owned Candidates are the best owned fits to review first, not automatic swaps.
- Possible Owned Candidates require pilot review before being treated as upgrades.
- Best Available Collection Shakeup Candidates are experiments only.
- If collection-only mode is active and the owned pool cannot complete the deck cleanly, say what roles remain unfilled.
- If the pilot wants full-card-pool suggestions instead, ask them to confirm that shift before recommending non-owned cards.

### Final Pilot Confirmation Step
After Section 7, provide a full intent summary titled **{parsed.commander_name} Review Intent Summary**. Ask the pilot to confirm or correct the summary before final recommendations.

When the pilot confirms, produce the final output based on Section 7, question 7. The final response must begin with the requested report title and a brief status summary, then immediately provide the copy/paste-ready recommendation list before the detailed explanation.

### Required Build-Up Final Output Rule
The final build-up output must include a copy/paste-ready card recommendation list directly after the opening summary. This list must get the user to a complete and legal 100-card Commander deck when the requested build task requires completion. The list should be easy to paste into Archidekt, Moxfield, MTGGoldfish, or another decklist site.

If the deck report says the deck is already a legal 100-card deck, clearly state that there are 0 required cuts and that the build-up review is upgrade-swap or tuning focused. In that case, the copy/paste-ready list should be presented as recommended swaps or additions/removals, not as required deck-completion cards.

Do not include cards already in the deck unless the card is a legal duplicate exception or the user explicitly asks for duplicates where legal.
""".strip()
