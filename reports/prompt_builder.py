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

# Convert shared option blocks once; question numbers remain normal, answer choices become plain option lines.
BRACKET_OPTIONS = _option_block(BRACKET_OPTIONS)
TABLE_EXPERIENCE_OPTIONS = _option_block(TABLE_EXPERIENCE_OPTIONS)
COMMANDER_NEEDS_OPTIONS = _option_block(COMMANDER_NEEDS_OPTIONS)

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


# -----------------------------
# Cut-down prompt sections
# -----------------------------

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



# -----------------------------
# v1.1.17 live philosophy handoff helpers
# -----------------------------

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
        "You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot complete a guided review using The Dragon's Touch report.",
        "",
    ]

    v1117_philosophy_handoff = _v1117_live_philosophy_handoff_block(context)
    if v1117_philosophy_handoff:
        lines.extend([v1117_philosophy_handoff, "", "---", ""])

    lines.extend(_script_context_block(context))
    lines.extend(_collection_prompt_context_block(context))
    lines.extend(["", *_global_prompt_rules(context)])

    # v1.4.13 Strategy Knowledge AI Handoff integration.
    # Prompt context only: does not authorize automatic deck edits or final inclusions.
    strategy_knowledge_prompt_block = build_strategy_knowledge_prompt_block(context)
    if strategy_knowledge_prompt_block:
        lines.extend(["", strategy_knowledge_prompt_block.rstrip()])

    # v1.1.17.3 PROMPT PHILOSOPHY DE-DUPLICATION
    # The v1.1 Philosophy / Persona Guidance block now carries the live philosophy
    # handoff context. Suppress the older v0.6.5.x prompt philosophy blocks when
    # the v1.1 block successfully renders, but keep them as a safe fallback if the
    # v1.1 helper ever fails or returns an empty block.
    philosophy_context = context.get("philosophy_context")
    if philosophy_context and not v1117_philosophy_handoff:
        philosophy_text = render_philosophy_prompt_questions(philosophy_context).rstrip()
        if philosophy_text.startswith("### Philosophy Guide Context"):
            philosophy_text = philosophy_text.replace("### Philosophy Guide Context", "## Philosophy Guide Context", 1)
        lines.extend(["", philosophy_text])
        showcase_block = render_philosophy_prompt_showcase_block(philosophy_context).rstrip()
        if showcase_block:
            lines.extend(["", showcase_block])
        lines.extend(["", *_philosophy_prompt_behavior_block(context)])

    if is_build_up:
        lines.extend(["", _build_up_sections(context, worksheet=worksheet)])
    else:
        lines.extend(["", _cut_down_sections(context, worksheet=worksheet)])

    from reports.player_facing_status_cleanup import clean_player_facing_prompt_text
    return clean_player_facing_prompt_text("\n".join(lines)).rstrip() + "\n"


def write_user_guided_prompt(deck_folder: Path, deck_name: str, context: dict[str, Any]) -> Path:
    path = get_unique_output_path(deck_folder, f"{deck_name}_user_guided_prompt", ".md")
    write_text_file(path, build_user_guided_prompt(context))
    return path
