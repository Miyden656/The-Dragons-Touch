"""User-guided prompt builder for the modular cleanup version.

The prompt builder keeps v0.6's central purpose separate from report formatting:
ask the pilot for intent, then use that intent to guide the review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_io.output_writer import get_unique_output_path, write_text_file
from analysis.deck_building_philosophies import render_philosophy_prompt_questions


def build_user_guided_prompt(context: dict[str, Any]) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    strategy = context["strategy_summary"]
    cut_pressure = context["cut_pressure"]
    replacement = context["replacement_needs"]
    completion = context.get("deck_completion")

    mode = runtime_config.prompt_interaction_mode
    review_direction = runtime_config.review_direction
    is_build_up = review_direction == "build_up"

    intro = [
        "# MTG Commander User-Guided Review Prompt",
        "",
        "You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot make a user-guided deck review.",
        "",
        f"Command zone card(s): {parsed.commander_name}",
        f"Prompt mode: {mode}",
        f"Review direction: {review_direction}",
        f"Script-reported primary strategy: {strategy.primary_strategy}",
        f"Script-reported secondary strategy: {strategy.secondary_strategy}",
        f"Deck size status: {cut_pressure.status}",
        "",
        "Important workflow rules:",
        "- Do not assume the script's strategy read is correct if the pilot corrects it.",
        "- Separate required cuts from optional optimization cuts.",
        "- Do not recommend cutting cards the pilot refuses to cut.",
        "- Treat bracket pressure as table-fit information, not an automatic cut.",
        "- Do not recommend cards already in the deck unless the card is a legal duplicate exception.",
        "- Before final recommendations, summarize the pilot's intent and ask for confirmation.",
    ]

    if is_build_up:
        intro.extend([
            "- This is a build-up/completion review. Prioritize additions and role needs before cuts.",
            f"- Build-up mode: {runtime_config.build_up_config.get('label', 'Not applicable')}",
        ])
        if completion:
            intro.append(f"- Cards needed to reach 100: {completion.cards_needed}")
    else:
        intro.extend([
            "- This is a cut-down/tuning review. Identify review-worthy cuts carefully, based on plan fit and replaceability.",
            f"- Cut depth mode: {runtime_config.cut_depth_config.get('mode', 'normal')}",
        ])

    if replacement.priority_categories:
        intro.extend(["", "Script-reported replacement/addition categories:"])
        for category in replacement.priority_categories:
            intro.append(f"- {category}")

    philosophy_context = context.get("philosophy_context")
    if philosophy_context:
        intro.extend(["", render_philosophy_prompt_questions(philosophy_context).rstrip()])

    sections = []
    if mode == "worksheet":
        sections.append("""
## One-Shot Worksheet

Answer all sections below in one reply.

### Section 1 — Main Review Goal
1. Is the script's review direction correct: build-up/completion or cut-down/tuning?
2. What do you most want from this review: legal cuts, optimization, strategy correction, additions, replacements, or playtest notes?
3. How much help do you want: light touch, normal tuning, strict optimization, brutal/deep review, or rebuild-level review?

### Section 2 — Deck Plan
1. In your own words, what is this deck trying to do?
2. Is the script-reported primary strategy correct?
3. Is the script-reported secondary strategy correct?
4. What cards, mechanics, or packages are most important to preserve?
5. How should the deck usually win?

### Section 3 — Commander Role
1. Is the commander the engine, payoff, support piece, finisher, or mostly color identity?
2. What does the commander need the 99 to provide?
3. Are there commander-specific cards that look weak but are important?

### Section 4 — Protected / Pet / Build-Around Intent
1. Cards you refuse to cut:
2. Pet cards you want protected:
3. Cards you want to build around:
4. Cards you are uncertain about:
5. Cards you specifically want reviewed:

### Section 5 — Power / Bracket / Table Intent
1. What bracket or power level are you aiming for?
2. Are Game Changers, fast mana, efficient tutors, or free interaction acceptable?
3. Are infinite combos or near-combos welcome, acceptable but not preferred, or unwanted?
4. Should replacements avoid adding or completing combos unless you explicitly want that?
5. What kind of table experience do you want this deck to create?

### Section 6 — Cut Philosophy
1. How many cuts do you want reviewed?
2. Are we making required cuts, optional upgrades, or both?
3. Should the review show only stronger candidates or include low-confidence/manual-review candidates?
4. Should bracket-pressure cards be reviewed as possible cuts if they exceed your table goal?
5. Preferred output: Recommended Cuts, Possible Cuts, Playtest First, Protected Cards, or full diagnostic?

### Section 7 — Replacement Philosophy and Output Questions
1. Replacement preference: no replacements, categories only, exact cards when obvious, exact cards welcome, collection-only, or suggestions later?
2. Replacement source: your collection/card pool, budget limit, or full Magic card pool?
3. Budget limit if any:
4. Priority: synergy, consistency, power, budget, flavor, or table friendliness?
5. Are there cards you already own or do not want recommended?
6. Preferred final output style: short list, full report, strategy review, cut-only, replacement-focused, playtest notes, prompt for another AI, or batch QA/bug review?

After I answer, summarize my intent first. Do not produce final recommendations until you have summarized the intent.
""")
    else:
        sections.append("""
## Interactive Guided Flow

Ask me only Section 1 first. After I answer, summarize Section 1 and then ask Section 2. Continue one section at a time.

### Section 1 — Main Review Goal
1. Is the script's review direction correct: build-up/completion or cut-down/tuning?
2. What do you most want from this review: legal cuts, optimization, strategy correction, additions, replacements, or playtest notes?
3. How much help do you want: light touch, normal tuning, strict optimization, brutal/deep review, or rebuild-level review?

### Section 2 — Deck Plan
1. In your own words, what is this deck trying to do?
2. Is the script-reported primary strategy correct?
3. Is the script-reported secondary strategy correct?
4. What cards, mechanics, or packages are most important to preserve?
5. How should the deck usually win?

### Section 3 — Commander Role
1. Is the commander the engine, payoff, support piece, finisher, or mostly color identity?
2. What does the commander need the 99 to provide?
3. Are there commander-specific cards that look weak but are important?

### Section 4 — Protected / Pet / Build-Around Intent
1. Cards you refuse to cut:
2. Pet cards you want protected:
3. Cards you want to build around:
4. Cards you are uncertain about:
5. Cards you specifically want reviewed:

### Section 5 — Power / Bracket / Table Intent
1. What bracket or power level are you aiming for?
2. Are Game Changers, fast mana, efficient tutors, or free interaction acceptable?
3. Are infinite combos or near-combos welcome, acceptable but not preferred, or unwanted?
4. Should replacements avoid adding or completing combos unless you explicitly want that?
5. What kind of table experience do you want this deck to create?

### Section 6 — Cut Philosophy
1. How many cuts do you want reviewed?
2. Are we making required cuts, optional upgrades, or both?
3. Should the review show only stronger candidates or include low-confidence/manual-review candidates?
4. Should bracket-pressure cards be reviewed as possible cuts if they exceed your table goal?
5. Preferred output: Recommended Cuts, Possible Cuts, Playtest First, Protected Cards, or full diagnostic?

### Section 7 — Replacement Philosophy and Output Questions
1. Replacement preference: no replacements, categories only, exact cards when obvious, exact cards welcome, collection-only, or suggestions later?
2. Replacement source: your collection/card pool, budget limit, or full Magic card pool?
3. Budget limit if any:
4. Priority: synergy, consistency, power, budget, flavor, or table friendliness?
5. Are there cards you already own or do not want recommended?
6. Preferred final output style: short list, full report, strategy review, cut-only, replacement-focused, playtest notes, prompt for another AI, or batch QA/bug review?

After Section 7, summarize my full intent and ask me to confirm before final recommendations.
""")

    return "\n".join(intro).rstrip() + "\n" + "\n".join(sections).strip() + "\n"


def write_user_guided_prompt(deck_folder: Path, deck_name: str, context: dict[str, Any]) -> Path:
    path = get_unique_output_path(deck_folder, f"{deck_name}_user_guided_prompt", ".md")
    write_text_file(path, build_user_guided_prompt(context))
    return path
