"""Prompt assembler.

Turns a CommanderAIContext into the system + user messages handed to the Ollama
client. Assembly order (design §5.2):

    SYSTEM = system_prompt.md
           + hallucination_guardrails.md
           + mode_<active>.md
           + persona block (from context.persona)
           + guide-style block (from context.guide_style)

    USER   = verified CONTEXT json
           + warnings + uncertainties (surfaced explicitly)
           + the user's actual request

Static prose lives in ai/prompts/*.md (editable without touching code). The
data-driven persona/guide-style blocks are generated from the context.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.commander_ai_bracket import render_bracket_block
from ai.commander_ai_guide_styles import render_guide_style_block
from ai.commander_ai_personas import render_persona_block
from ai.schemas.ai_context import (
    MODE_BUILD_FROM_COLLECTION,
    MODE_COMMANDER_REVIEW,
    MODE_CUT_REVIEW,
    MODE_PERSONA_COACHING,
    MODE_REPLACEMENT,
    MODE_STRATEGY_TUTOR,
    CommanderAIContext,
)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Modes where a machine-readable JSON mirror is useful to the app. Conversational
# modes (strategy_tutor, persona_coaching) stay prose-only — forcing JSON there
# would only degrade the answer.
STRUCTURED_MODES = frozenset(
    {MODE_COMMANDER_REVIEW, MODE_CUT_REVIEW, MODE_REPLACEMENT, MODE_BUILD_FROM_COLLECTION}
)

# Modes where 4-player pod reasoning is central to a good answer. For these we
# hand the model a focused, plain-text mirror of the engine's verified pod facts
# (the same "hand it the needle" technique as the cut/replacement allow-lists) so
# a small model actually grounds its multiplayer claims instead of guessing.
MULTIPLAYER_FOCUS_MODES = frozenset(
    {MODE_COMMANDER_REVIEW, MODE_STRATEGY_TUTOR, MODE_PERSONA_COACHING}
)

# Appended to the system prompt for STRUCTURED_MODES. The prose stays primary;
# the JSON only mirrors what was already said. Kept in code (not a .md asset) so
# it stays in lockstep with the parser/schema.
_OUTPUT_FORMAT_INSTRUCTION = """## Output format
Write your normal answer first, in prose. Then, on a new line AFTER the prose,
append a single fenced code block tagged `json` that mirrors your answer for the
app to read. Use exactly this shape and omit any field that does not apply:

```json
{
  "summary": "one or two sentence takeaway",
  "primary_recommendation": "the single most important action",
  "confidence": "low | medium | high",
  "possible_cuts": [{"card": "", "reason": "", "confidence": "low | medium | high", "cut_type": "", "replacement_category": ""}],
  "protected_cards": [{"card": "", "reason": ""}],
  "replacement_needs": ["category or need"],
  "warnings": ["verified concern"],
  "follow_up_questions": ["a question that would sharpen the advice"]
}
```

Rules for the JSON: only include cards you already named in the prose; never
invent a card to fill a field; if you have nothing for a field, omit it. The
prose above is what the user reads — keep it complete on its own."""

_MODE_FILES: dict[str, str] = {
    MODE_COMMANDER_REVIEW: "mode_commander_review.md",
    MODE_BUILD_FROM_COLLECTION: "mode_build_from_collection.md",
    MODE_CUT_REVIEW: "mode_cut_review.md",
    MODE_REPLACEMENT: "mode_replacement.md",
    MODE_STRATEGY_TUTOR: "mode_strategy_tutor.md",
    MODE_PERSONA_COACHING: "mode_persona_coaching.md",
}

# Tiny in-process cache so we don't re-read the .md assets every turn.
_asset_cache: dict[str, str] = {}


def load_prompt_asset(name: str) -> str:
    """Read a prompt asset from ai/prompts/. Missing file -> '' (never raises)."""
    if name in _asset_cache:
        return _asset_cache[name]
    path = PROMPTS_DIR / name
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        text = ""
    _asset_cache[name] = text
    return text


def build_system_prompt(context: CommanderAIContext) -> str:
    mode_file = _MODE_FILES.get(context.mode, _MODE_FILES[MODE_COMMANDER_REVIEW])
    parts = [
        load_prompt_asset("system_prompt.md"),
        load_prompt_asset("hallucination_guardrails.md"),
        load_prompt_asset(mode_file),
        render_persona_block(context.persona),
        render_bracket_block(context.bracket),
        render_guide_style_block(context.guide_style),
    ]
    return "\n\n".join(p for p in parts if p and p.strip())


def build_user_prompt(
    context: CommanderAIContext,
    *,
    verified_card_facts: str = "",
) -> str:
    # Compact (not pretty-printed) JSON: identical information, ~32% fewer tokens.
    # The grounded prompt is large and the model's context window is finite on an
    # 8 GB card — every token of indentation is a token of grounding we can't fit.
    parts: list[str] = [
        "## Verified deck context (engine-provided — treat as source of truth)",
        "```json",
        json.dumps(context.to_payload(), ensure_ascii=False, separators=(",", ":")),
        "```",
    ]

    # Grounding block: verified Scryfall facts for any card the user asked about
    # (legality across formats, oracle text, mana value). Hand the model the
    # answer rather than hoping it recalls ~30k cards correctly.
    if verified_card_facts and verified_card_facts.strip():
        parts.append(verified_card_facts.strip())

    if context.warnings:
        parts.append("## Engine warnings (verified facts to surface)")
        parts.extend(f"- {w}" for w in context.warnings)

    if context.uncertainties:
        parts.append("## Uncertainties (state plainly; do not paper over)")
        parts.extend(f"- {u}" for u in context.uncertainties)

    if context.pet_cards:
        parts.append("## User-named pet cards (protect unless told otherwise)")
        parts.append(", ".join(context.pet_cards))

    if context.user_constraints:
        parts.append("## User constraints")
        parts.extend(f"- {c}" for c in context.user_constraints)

    # Pilot intent the decklist can't reveal (from the per-guide intake windows).
    if context.rescue_cards:
        parts.append(
            "## Rescue target (build the deck to make these work; do not suggest cutting them)\n"
            + ", ".join(context.rescue_cards)
        )
    if context.hybrid_themes:
        parts.append(
            "## Themes to bridge (find the cards that serve BOTH; flag single-side cards)\n"
            + " + ".join(context.hybrid_themes)
        )
    if context.theme_intent:
        parts.append(
            "## Theme / vibe the pilot is going for (judge identity against THIS, not a guess)\n"
            + context.theme_intent
        )

    # Pod-value focus: surface the engine's verified 4-player facts as plain text
    # for the modes where multiplayer reasoning matters most. Grounds claims about
    # sweeper value, single-target trades, table reach, and archenemy risk.
    if context.mode in MULTIPLAYER_FOCUS_MODES:
        focus = _multiplayer_focus(context.multiplayer)
        if focus:
            parts.append(
                "## Verified pod facts (4-player reasoning — ground multiplayer claims here)\n"
                + focus
                + "\nReason about the pod from these engine-verified numbers; do not invent "
                "interaction counts, table reach, or threat level."
            )

    # Political focus: when the engine detected a political archetype, hand the
    # model the verified political read so it coaches the deck as a political plan
    # (incentive / deterrence / payoff / inevitability) instead of guessing.
    if context.mode in MULTIPLAYER_FOCUS_MODES:
        focus = _political_focus(context.political)
        if focus:
            parts.append(
                "## Verified political read (Section-3 archetypes - ground political claims here)\n"
                + focus
                + "\nUse this engine-verified political read; do not invent a political archetype "
                "the engine did not detect, and do not call the deck political if it is not."
            )

    # Cut Review: hand the model the exact candidate list (with the engine's own
    # reasons) and forbid going outside it. Small models otherwise roam the JSON,
    # "cut" protected/strategy cards, and invent their own reasons.
    if context.mode == MODE_CUT_REVIEW:
        focus = _cut_candidate_focus(context.cuts)
        if focus:
            parts.append(
                "## The ONLY cards you may recommend cutting (the engine's candidates)\n"
                + focus
                + "\nRecommend cuts ONLY from this exact list. Any card not listed here — "
                "including everything in `protected` and `replacements` — must NOT be called a cut. "
                "Lead with the engine's stated reason for each card; do not substitute a reason of your own."
            )
        else:
            parts.append(
                "## Cut candidates\nThe engine found no clear cut candidates for this deck. "
                "Say so plainly instead of inventing cuts."
            )

    # Replacement: same "hand it the verified list" discipline. The engine has
    # already ranked legal, color-identity-valid candidates; the model must not
    # name cards outside this set.
    if context.mode == MODE_REPLACEMENT:
        focus = _replacement_focus(context.replacements)
        if _replacement_has_named_candidates(context.replacements):
            parts.append(
                "## The ONLY specific cards you may recommend adding (the engine's verified candidates)\n"
                + focus
                + "\nWhen you name a specific card to add, it MUST come from this exact list. "
                "You may freely discuss the need CATEGORIES above, but do not invent or recall "
                "specific card names outside this verified, color-identity-legal set."
            )
        elif focus:
            parts.append(
                "## Replacement needs (no specific verified cards available)\n"
                + focus
                + "\nThe engine surfaced these need CATEGORIES but no verified specific cards "
                "for this deck/collection. Speak to the categories only — do NOT name specific "
                "cards to add, since none have been engine-verified as legal in this color identity."
            )
        else:
            parts.append(
                "## Replacement candidates\nThe engine did not surface replacement needs or "
                "candidates. Say so plainly; do not name specific cards to add."
            )

    parts.append("## User request")
    parts.append(context.user_request or "(No specific question — give a review appropriate to the mode.)")

    # Output-format instruction goes LAST so a small model actually obeys it —
    # the same "what it sees most recently wins" lesson as the cut allow-list.
    if context.mode in STRUCTURED_MODES:
        parts.append(_OUTPUT_FORMAT_INSTRUCTION)
    return "\n\n".join(parts)


def _cut_candidate_focus(cuts: dict) -> str:
    """Render the engine's actual cut candidates as an explicit allow-list, each
    card paired with the engine's own reason so the model echoes it rather than
    inventing one."""
    cuts = cuts or {}
    labels = [
        ("required_cuts", "Required (legality/size)"),
        ("optional_cuts", "Optional (optimization)"),
        ("manual_review", "Manual review"),
        ("playtest_first", "Playtest before cutting"),
    ]
    lines: list[str] = []
    for key, label in labels:
        entries = [e for e in (cuts.get(key) or []) if isinstance(e, dict) and e.get("card")]
        if not entries:
            continue
        lines.append(f"- {label}:")
        for e in entries:
            reasons = [str(r) for r in (e.get("reasons") or []) if r]
            reason = reasons[0] if reasons else ""
            conf = str(e.get("confidence", "")).strip()
            suffix = f" — {reason}" if reason else ""
            if conf:
                suffix += f" [engine confidence: {conf}]"
            lines.append(f"    - {e['card']}{suffix}")
    return "\n".join(lines)


def _replacement_focus(replacements: dict) -> str:
    """Render the engine's verified add-candidates (and need categories) as an
    explicit allow-list for replacement mode."""
    replacements = replacements or {}
    lines: list[str] = []

    categories = [str(c) for c in (replacements.get("priority_categories") or []) if c]
    needs = replacements.get("need_details") or []
    if categories:
        lines.append(f"- Priority need categories: {', '.join(categories)}")
    for n in needs:
        if isinstance(n, dict) and n.get("category"):
            reason = str(n.get("reason", "")).strip()
            lines.append(f"    - need: {n['category']}" + (f" — {reason}" if reason else ""))

    def _add_cards(key: str, label: str, fit_key: str) -> None:
        entries = [e for e in (replacements.get(key) or []) if isinstance(e, dict) and e.get("card")]
        if not entries:
            return
        lines.append(f"- {label}:")
        for e in entries:
            cat = str(e.get("replacement_category", "")).strip()
            fit = str(e.get(fit_key, "")).strip()
            bits = " · ".join(b for b in (cat, fit) if b)
            lines.append(f"    - {e['card']}" + (f" ({bits})" if bits else ""))

    _add_cards("candidates", "Engine-ranked candidates", "why_it_fits")
    _add_cards("collection_candidates", "From your collection", "reason")
    return "\n".join(lines)


_MULTIPLAYER_EXAMPLE_LABELS = (
    ("sweepers", "board wipes"),
    ("table_wide_pressure", "table-wide pressure"),
    ("goad", "goad"),
    ("pillowfort", "pillowfort / attack-deterrents"),
    ("threats", "main threats"),
)


def _multiplayer_example_line(examples: dict) -> str:
    """Name the engine-identified cards behind the counts so a small model does
    not invent which cards are the sweepers/threats (the 'hand it the needle'
    technique — the counts alone let it guess, the names pin it down)."""
    examples = examples or {}
    parts = []
    for key, label in _MULTIPLAYER_EXAMPLE_LABELS:
        names = [str(n) for n in (examples.get(key) or []) if n]
        if names:
            parts.append(f"{label}: {', '.join(names)}")
    if not parts:
        return ""
    return (
        "- Cards the engine counted (use these EXACT names if you name cards; do "
        "not assign these roles to any other card): " + "; ".join(parts) + "."
    )


def _multiplayer_focus(multiplayer: dict) -> str:
    """Render the engine's verified pod facts as a focused plain-text block.

    Prefers the ready-made `facts` list (already grounded, human-readable). Falls
    back to the structured bands so the block is never empty when data exists.
    Either way, appends the engine-identified example cards so the model grounds
    not just the counts but WHICH cards they are.
    """
    multiplayer = multiplayer or {}
    facts = [str(f) for f in (multiplayer.get("facts") or []) if f]
    example_line = _multiplayer_example_line(multiplayer.get("example_cards"))

    if facts:
        block = "\n".join(f"- {f}" for f in facts)
        return block + ("\n" + example_line if example_line else "")

    interaction = multiplayer.get("interaction") or {}
    reach = multiplayer.get("table_reach") or {}
    archenemy = multiplayer.get("archenemy") or {}
    if not (interaction or reach or archenemy):
        return ""
    lines = [
        f"- Interaction: {interaction.get('sweepers', 0)} sweepers, "
        f"{interaction.get('spot_removal', 0)} single-target, "
        f"{interaction.get('counterspells', 0)} counters "
        f"(reach: {interaction.get('reach_band', 'none')}).",
        f"- Table reach: {reach.get('band', 'none')}.",
        f"- Archenemy risk: {archenemy.get('risk_band', 'low')}.",
    ]
    if example_line:
        lines.append(example_line)
    return "\n".join(lines)


def _political_focus(political: dict) -> str:
    """Render the engine's verified political read as a focused plain-text block.

    Returns '' when the deck is not political, so the block only appears when the
    engine actually detected a political archetype.
    """
    political = political or {}
    if not political.get("is_political"):
        return ""

    def _line(block: dict, label: str) -> str:
        if not isinstance(block, dict) or not block.get("name"):
            return ""
        name = block.get("name", "")
        axis = block.get("axis", "")
        conf = block.get("confidence", "low")
        support = block.get("commander_support", "none")
        examples = [e for e in (block.get("example_cards") or []) if e][:4]
        ex = f" (e.g. {', '.join(examples)})" if examples else ""
        axis_txt = f" - {axis}" if axis else ""
        return f"- {label}: {name}{axis_txt} [confidence: {conf}, commander support: {support}]{ex}"

    lines: list[str] = []
    primary_line = _line(political.get("primary") or {}, "Primary political axis")
    if primary_line:
        lines.append(primary_line)
    secondary_line = _line(political.get("secondary") or {}, "Secondary political package")
    if secondary_line:
        lines.append(secondary_line)
    lines.append(
        f"- Table dependency: {political.get('table_dependency', 'low')}; "
        f"salt risk: {political.get('salt_risk', 'low')}; "
        f"reputation: {political.get('reputation_modifier', 'none')}."
    )
    for w in (political.get("warnings") or [])[:4]:
        if w:
            lines.append(f"- Watch: {w}")
    return "\n".join(lines) if lines else ""


def _replacement_has_named_candidates(replacements: dict) -> bool:
    """True only if the engine surfaced specific add-cards (not just categories)."""
    replacements = replacements or {}
    for key in ("candidates", "collection_candidates"):
        if any(isinstance(e, dict) and e.get("card") for e in (replacements.get(key) or [])):
            return True
    return False


def build_messages(
    context: CommanderAIContext,
    *,
    history: list[dict] | None = None,
    verified_card_facts: str = "",
) -> list[dict]:
    """Assemble the full [system, ...history, user] message list for Ollama."""
    messages: list[dict] = [{"role": "system", "content": build_system_prompt(context)}]
    if history:
        messages.extend(history)
    messages.append(
        {"role": "user", "content": build_user_prompt(context, verified_card_facts=verified_card_facts)}
    )
    return messages
