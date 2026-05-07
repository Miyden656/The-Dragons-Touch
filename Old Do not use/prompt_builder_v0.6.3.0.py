"""User-guided prompt builder for The Dragon's Touch.

Patch Batch 1 goal:
- Keep the old seven-section guided workflow, but make it faster to use.
- Force the reviewing AI to ask for the generated deck report first.
- Use numbered answer choices where possible.
- Preserve separate cut-down and build-up intake flows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_io.output_writer import get_unique_output_path, write_text_file
from analysis.deck_building_philosophies import render_philosophy_prompt_questions


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


# -----------------------------
# Small formatting helpers
# -----------------------------

def _yes_no_direction_options() -> str:
    return """1. Yes, the script's review direction is correct.
2. No — I want the other review direction instead. Please state build-up/completion or cut-down/tuning."""


def _main_goal_cut_options() -> str:
    return """1. Legal cuts — identify cuts needed to make the deck legal.
2. Optimization — improve a legal deck without treating changes as mandatory.
3. Strategy correction — fix the script's read if the deck plan is wrong.
4. Additions / replacements — identify what kinds of cards would help.
5. Playtest notes — focus on what to watch in future games."""


def _help_depth_options() -> str:
    return """1. Light touch — only obvious issues.
2. Normal tuning — practical review with a few useful candidates.
3. Strict optimization — challenge more slots and tighten the deck.
4. Brutal / deep review — broad diagnostic with many review points.
5. Rebuild-level review — treat the list as a rough pool and reshape around the stated plan."""


def _build_goal_options() -> str:
    return """1. This is correct.
2. No, Build from Scratch — Commander(s) only; create a complete plan and card recommendation path.
3. No, Point me in the right direction — the deck needs 30+ cards and mainly needs structure.
4. No, Help me get there — the deck needs 11 to 30 cards and needs role completion.
5. No, Finalize — the deck needs 10 or fewer cards and needs finishing touches."""


def _commander_role_options() -> str:
    return """1. Engine — the commander repeatedly generates the deck's main advantage.
2. Payoff — the commander rewards the deck for doing its thing.
3. Support piece — the commander helps the plan but is not the whole plan.
4. Finisher — the commander is how the deck closes games.
5. Color identity only — the commander mainly provides colors or theme."""


def _cut_candidate_visibility_options() -> str:
    return """1. Only stronger candidates.
2. Include low-confidence / manual-review candidates too."""


def _bracket_pressure_cut_options() -> str:
    return """1. Yes, review bracket-pressure cards as possible cuts if they exceed my table goal.
2. No, treat bracket-pressure cards as table-fit notes only unless they are also off-plan."""


def _preferred_output_options() -> str:
    return """1. Recommended Cuts — strongest cut recommendations only.
2. Possible Cuts — broader review list with caveats.
3. Playtest Guide — what to watch before cutting.
4. Protected Cards — focus on what should not be cut.
5. Full diagnostic — show strategy, cuts, protected cards, replacements, and playtest notes."""


def _replacement_preference_options(include_replacements: bool = True) -> str:
    if not include_replacements:
        return """1. Categories only — describe what roles the deck needs.
2. Exact cards when obvious — only recommend exact cards when the fit is very clear.
3. Exact cards welcome — recommend specific card names freely.
4. Suggestions for later — finish the plan first, then suggest cards later."""
    return """1. No replacements.
2. Categories only.
3. Exact cards when obvious — specific card names only when the role fit is clear.
4. Exact cards welcome.
5. Suggestions for later."""


def _replacement_source_options() -> str:
    return """1. My collection / card pool.
2. Full Magic card pool."""


def _priority_options() -> str:
    return """Choose 1 to 2 priorities:
1. Synergy — strongest fit with the commander and primary plan.
2. Consistency — make the deck do its thing more often.
3. Bracket limits / power fit — keep the deck inside the intended table range.
4. Budget — respect price limits.
5. Flavor — preserve theme, story, or vibe.
6. Table friendliness — avoid cards that create the wrong table experience."""


def _final_output_style_options() -> str:
    return """1. Short list — concise recommendations only.
2. Full report — complete reasoning and sections.
3. Strategy review — focus on plan, packages, and identity.
4. Cut-only — only cuts and why.
5. Replacement-focused — focus on what to add or swap.
6. Playtest notes — focus on what to test in games.
7. Prompt for another AI — produce a clean follow-up prompt.
8. Batch QA / bug review — focus on whether the script output looks wrong."""


def _safe_list(items: list[str], fallback: str = "None reported") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def _philosophy_intro_instruction(context: dict[str, Any]) -> str:
    philosophy = context.get("philosophy_context") or {}
    guide_name = philosophy.get("guide_name")
    guide_role = philosophy.get("guide_role") or "Guide"
    label = philosophy.get("label") or "Balanced / Unknown"
    core_question = philosophy.get("core_question") or "What does this deck want to do?"

    if guide_name:
        return (
            f"After receiving the deck report, briefly introduce the selected philosophy guide: "
            f"{guide_name}, {guide_role}. Explain in 2 to 4 sentences that the review will use the "
            f"{label} lens, whose guiding question is: '{core_question}' Do not roleplay heavily; "
            f"use the guide as concise mentor framing."
        )
    return (
        f"After receiving the deck report, briefly introduce the selected philosophy lens: {label}. "
        f"Explain in 2 to 4 sentences that this lens will guide tone and priorities, but not legality or strategy detection."
    )


def _script_context_block(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    strategy = context["strategy_summary"]
    cut_pressure = context["cut_pressure"]
    replacement = context["replacement_needs"]
    completion = context.get("deck_completion")

    lines = [
        "## Script Context From The Dragon's Touch",
        "",
        f"- Command zone card(s): {parsed.commander_name}",
        f"- Prompt mode: {runtime_config.prompt_interaction_mode}",
        f"- Review direction: {runtime_config.review_direction}",
        f"- Script-reported primary strategy: {strategy.primary_strategy}",
        f"- Script-reported secondary strategy: {strategy.secondary_strategy}",
        f"- Deck size status: {cut_pressure.status}",
        f"- Current deck size: {cut_pressure.deck_card_count}",
        f"- Required cuts: {cut_pressure.required_cuts}",
        f"- Optional cut target: {runtime_config.cut_depth_config.get('optional_cut_target', 0)}",
    ]

    if runtime_config.review_direction == "build_up":
        lines.append(f"- Build-up mode: {runtime_config.build_up_config.get('label', 'Not applicable')}")
        if completion:
            lines.append(f"- Cards needed to reach 100: {completion.cards_needed}")
    else:
        lines.append(f"- Cut depth mode: {runtime_config.cut_depth_config.get('mode', 'normal')}")

    if replacement.priority_categories:
        lines.extend(["", "Script-reported replacement/addition categories:"])
        lines.extend(f"- {category}" for category in replacement.priority_categories)

    core_packages = []
    for candidate in getattr(strategy, "candidates", [])[:6]:
        name = getattr(candidate, "name", None) or getattr(candidate, "strategy", None)
        if name:
            core_packages.append(str(name))
    if core_packages:
        lines.extend(["", "Script-reported visible packages / themes:"])
        lines.extend(f"- {package}" for package in core_packages)

    return lines


def _global_prompt_rules(context: dict[str, Any]) -> list[str]:
    return [
        "## Required Workflow Rules For The Reviewing AI",
        "",
        "1. First, ask the user to paste or upload the generated deck report. Do not begin Section 1 until the report is provided.",
        "2. The deck report should include a section titled 'Full Decklist / Main Deck Cards for AI Review'. If that section is missing, ask the user to paste the full decklist before making final cut, replacement, or completion recommendations.",
        "3. Also check for a 'Reference / Non-Mainboard / Ignored Cards' section. If present, ask whether any listed card is intended as a companion, sideboard/maybeboard card, or reference-only card before making final recommendations.",
        "4. After the deck report is provided, confirm receipt and give a brief initial summary of what the report appears to say.",
        f"5. {_philosophy_intro_instruction(context)}",
        "6. Then immediately ask Section 1 only. Do not ask multiple sections at once in interactive mode.",
        "7. The user may answer using just numbers, short phrases, or N/A. Accept numbered answers without forcing long explanations.",
        "8. After each section, summarize the user's answers in 3 to 6 bullets, then immediately ask the next section.",
        "9. Do not make final cut, addition, or replacement recommendations until all required sections are complete.",
        "10. Do not assume the script's strategy read is correct if the pilot corrects it.",
        "11. Separate required legality cuts from optional optimization cuts.",
        "12. Do not recommend cutting cards the pilot refuses to cut.",
        "13. Treat bracket pressure as table-fit information, not an automatic cut.",
        "14. Do not recommend cards already in the deck unless the card is a legal duplicate exception.",
        "15. Before final recommendations, provide a full intent summary titled '<Commander Name> Review Intent Summary' and ask the user to confirm or correct it.",
        "16. Only after confirmation should you produce the final recommendations in the user's selected output style.",
    ]


# -----------------------------
# Cut-down prompt sections
# -----------------------------

def _cut_down_sections(context: dict[str, Any], worksheet: bool = False) -> str:
    strategy = context["strategy_summary"]
    cut_pressure = context["cut_pressure"]

    prefix = "Answer all sections below in one reply." if worksheet else "Ask only Section 1 first. After the user answers, summarize Section 1 and immediately ask Section 2. Continue one section at a time."

    return f"""
## Cut-Down / Tuning Guided Flow

{prefix}

### Section 1 — Main Review Goal
1. Is the script's review direction correct? Script says: **cut_down / tuning**.
{_yes_no_direction_options()}

2. What do you want from this review?
{_main_goal_cut_options()}

3. How much help do you want?
{_help_depth_options()}

### Section 2 — Commander Role
1. Is the commander the...?
{_commander_role_options()}

2. What does the commander need the 99 to provide? Choose all that apply, or choose Other and describe.
{COMMANDER_NEEDS_OPTIONS}

3. Are there commander-specific cards that look weak but are important? Answer with card names, N/A, or a short explanation.

### Section 3 — Commander Plan / Deck Identity
1. What do you want this commander or deck to do when it is working correctly?

2. Is the reported primary strategy correct? Script says: **{strategy.primary_strategy}**. If not, what should it be?

3. Is the reported secondary strategy correct? Script says: **{strategy.secondary_strategy}**. If not, what should it be?

4. Are there specific mechanics, themes, packages, or play patterns you want to preserve?

5. How should the deck usually win? This should remain player-defined.

### Section 4 — Protected / Pet / Build-Around Intent
A simple **No**, **N/A**, or **None** can cover this whole section if nothing applies.

1. Cards you refuse to cut:
2. Pet cards you want protected:
3. Cards you want to build around:
4. Cards you are uncertain about:
5. Cards you specifically want reviewed:

### Section 5 — Bracket / Table Intent
1. What bracket or power level are you aiming for?
{BRACKET_OPTIONS}

2. Are Game Changers, fast mana, efficient tutors, or free interaction acceptable? Answer Yes, No, Some, or explain.

3. Are infinite combos or near-combos welcome?
1. Welcome.
2. Acceptable but not preferred.
3. Only if they require 3+ cards.
4. Unwanted.
5. Other — please describe.

4. Should replacements avoid adding or completing combos unless you explicitly want that?
1. Yes.
2. No.
3. Case-by-case.

5. What kind of table experience do you want this deck to create?
{TABLE_EXPERIENCE_OPTIONS}

### Section 6 — Cut Philosophy
1. Is the cut review from the deck report correct? The report says: **{cut_pressure.status}; required cuts: {cut_pressure.required_cuts}; optional target: {getattr(cut_pressure, 'optional_cut_target', 'see report')}**.
- Optional: enter a specific number of cuts you want reviewed. N/A or no answer means the report's range is fine.

2. Are we making required cuts, optional upgrades, or both?
1. Required legal cuts only.
2. Optional upgrades only.
3. Both required cuts and optional upgrades.
4. Not sure — use the deck report's deck-size status.

3. Should the review show only stronger candidates or include low-confidence/manual-review candidates?
{_cut_candidate_visibility_options()}

4. Should bracket-pressure cards be reviewed as possible cuts if they exceed your table goal?
{_bracket_pressure_cut_options()}

5. Preferred cut output:
{_preferred_output_options()}

### Section 7 — Replacement Philosophy
1. Replacement preference:
{_replacement_preference_options(True)}

2. Replacement source:
{_replacement_source_options()}

3. Budget limit if any:

4. Priority:
{_priority_options()}

5. Are there cards you already own or do not want recommended?

6. Preferred final output style:
{_final_output_style_options()}

### Final Confirmation Step
After Section 7, provide a full intent summary titled **{context['parsed_deck'].commander_name} Review Intent Summary**. Ask the user to confirm or correct the summary before final recommendations. After confirmation, produce the final output based on Section 7, question 6.
""".strip()


# -----------------------------
# Build-up prompt sections
# -----------------------------

def _build_up_sections(context: dict[str, Any], worksheet: bool = False) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    strategy = context["strategy_summary"]
    completion = context.get("deck_completion")
    build_mode = runtime_config.build_up_config.get("mode", "finalize_10_or_less")
    build_label = runtime_config.build_up_config.get("label", "Build-up / completion")
    cards_needed = getattr(completion, "cards_needed", "see report")
    is_scratch = build_mode == "build_from_scratch"

    prefix = "Answer all sections below in one reply." if worksheet else "Ask only Section 1 first. After the user answers, summarize Section 1 and immediately ask Section 2. Continue one section at a time."

    if is_scratch:
        section_6 = """### Section 6 — Cut Philosophy
Skip this section because the selected build-up mode is **Build from Scratch — Commander(s) only**. Do not ask optimization-cut questions for a commander-only build. Immediately continue to Section 7."""
        replacement_note = "This is Build from Scratch, so do not discuss replacements or swaps. Focus only on building a complete legal 100-card Commander deck."
        replacement_pref_block = """1. Build recommendation preference:
1. Categories only.
2. Exact cards when obvious.
3. Exact cards welcome.
4. Suggestions for later."""
    else:
        section_6 = f"""### Section 6 — Cut Philosophy For Optimization
This section exists because build-up mode may still need optional optimization swaps if the list already contains cards or if a suggested addition replaces a weaker role card. If the user wants additions only, they can say so.

1. Do you want optional upgrade recommendations with every cut suggestion made?
1. Yes.
2. No, additions only.
3. Only if the cut is very obvious.

2. How many optimization cut recommendations do you want?
1. 3–5
2. 6–9
3. 10–14
4. None unless required for legality.

3. Should the review show only stronger candidates or include low-confidence/manual-review candidates?
{_cut_candidate_visibility_options()}

4. Should bracket-pressure cards be reviewed as possible cuts if they exceed your table goal?
{_bracket_pressure_cut_options()}

5. Preferred cut output:
{_preferred_output_options()}"""
        replacement_note = "If this is not Build from Scratch, replacement questions may apply because the deck may already have cards that are being upgraded or swapped."
        replacement_pref_block = f"""1. Replacement preference:
{_replacement_preference_options(True)}"""

    return f"""
## Build-Up / Completion Guided Flow

{prefix}

### Section 1 — Main Review Goal
1. Is the script's review direction correct? Script says: **build_up / completion**.
{_yes_no_direction_options()}

2. What kind of build-up help do you want? Script currently says: **{build_label}**. Cards needed to reach 100: **{cards_needed}**.
{_build_goal_options()}

### Section 2 — Commander Role
1. Is the commander the...?
{_commander_role_options()}

2. What does the commander need the 99 to provide? Choose all that apply, or choose Other and describe.
{COMMANDER_NEEDS_OPTIONS}

### Section 3 — Deck Plan
1. What do you want this commander or deck to do when it is working correctly?

2. Is the reported primary strategy correct? Script says: **{strategy.primary_strategy}**. If not, what should it be?

3. Is the reported secondary strategy correct? Script says: **{strategy.secondary_strategy}**. If not, what should it be?

4. Are there specific mechanics, themes, packages, or play patterns you want to build around?

5. How should the deck usually win? This should remain player-defined.

### Section 4 — Protected / Pet / Build-Around Intent
A simple **No**, **N/A**, or **None** can cover this whole section if nothing applies.

1. Cards you refuse to cut:
2. Pet cards you want protected:
3. Cards you want to build around:
4. Cards you are uncertain about:
5. Cards you specifically want reviewed:

### Section 5 — Bracket / Table Intent
1. What bracket or power level are you aiming for?
{BRACKET_OPTIONS}

2. Are Game Changers, fast mana, efficient tutors, or free interaction acceptable? Answer Yes, No, Some, or explain.

3. Are infinite combos or near-combos welcome?
1. Welcome.
2. Acceptable but not preferred.
3. Only if they require 3+ cards.
4. Unwanted.
5. Other — please describe.

4. Should replacements avoid adding or completing combos unless you explicitly want that?
1. Yes.
2. No.
3. Case-by-case.

5. What kind of table experience do you want this deck to create?
{TABLE_EXPERIENCE_OPTIONS}

{section_6}

### Section 7 — Replacement Philosophy, Build Source, and Output Questions
{replacement_note}

{replacement_pref_block}

2. Replacement source, if replacements are relevant:
{_replacement_source_options()}

3. Build source:
{_replacement_source_options()}

4. Budget limit if any:

5. Priority:
{_priority_options()}

6. Are there cards you already own or do not want recommended?

7. Preferred final output style:
{_final_output_style_options()}

### Final Confirmation Step
After Section 7, provide a full intent summary titled **{parsed.commander_name} Review Intent Summary**. Ask the user to confirm or correct the summary before final recommendations.

When the user confirms, produce the final output based on Section 7, question 7. The final response must begin with the requested report title and a brief status summary, then immediately provide the copy/paste-ready recommendation list before the detailed explanation.

### Required Build-Up Final Output Rule
The final build-up output must include a copy/paste-ready card recommendation list directly after the opening summary. This list must get the user to a complete and legal 100-card Commander deck when the requested build task requires completion. The list should be easy to paste into Archidekt, Moxfield, MTGGoldfish, or another decklist site.

If the deck report says the deck is already a legal 100-card deck, clearly state that there are 0 required cuts and that the build-up review is upgrade-swap or tuning focused. In that case, the copy/paste-ready list should be presented as recommended swaps or additions/removals, not as required deck-completion cards.

Do not include cards already in the deck unless the card is a legal duplicate exception or the user explicitly asks for duplicates where legal.
""".strip()


# -----------------------------
# Public builder
# -----------------------------

def build_user_guided_prompt(context: dict[str, Any]) -> str:
    runtime_config = context["runtime_config"]
    mode = runtime_config.prompt_interaction_mode
    is_build_up = runtime_config.review_direction == "build_up"
    worksheet = mode == "worksheet"

    lines = [
        "# MTG Commander User-Guided Review Prompt",
        "",
        "You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot make a user-guided deck review for The Dragon's Touch.",
        "",
    ]
    lines.extend(_script_context_block(context))
    lines.extend(["", *_global_prompt_rules(context)])

    philosophy_context = context.get("philosophy_context")
    if philosophy_context:
        lines.extend(["", "## Philosophy Guide Context", "", render_philosophy_prompt_questions(philosophy_context).rstrip()])

    if is_build_up:
        lines.extend(["", _build_up_sections(context, worksheet=worksheet)])
    else:
        lines.extend(["", _cut_down_sections(context, worksheet=worksheet)])

    return "\n".join(lines).rstrip() + "\n"


def write_user_guided_prompt(deck_folder: Path, deck_name: str, context: dict[str, Any]) -> Path:
    path = get_unique_output_path(deck_folder, f"{deck_name}_user_guided_prompt", ".md")
    write_text_file(path, build_user_guided_prompt(context))
    return path
