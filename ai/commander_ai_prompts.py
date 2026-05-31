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

from pathlib import Path

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
        render_guide_style_block(context.guide_style),
    ]
    return "\n\n".join(p for p in parts if p and p.strip())


def build_user_prompt(
    context: CommanderAIContext,
    *,
    verified_card_facts: str = "",
) -> str:
    parts: list[str] = [
        "## Verified deck context (engine-provided — treat as source of truth)",
        "```json",
        context.to_json(),
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

    # Cut Review: hand the model the exact candidate list and forbid going outside
    # it. Small models otherwise roam the JSON and "cut" protected/strategy cards.
    if context.mode == MODE_CUT_REVIEW:
        focus = _cut_candidate_focus(context.cuts)
        if focus:
            parts.append(
                "## The ONLY cards you may recommend cutting (the engine's candidates)\n"
                + focus
                + "\nRecommend cuts ONLY from this exact list. Any card not listed here — "
                "including everything in `protected` and `replacements` — must NOT be called a cut."
            )
        else:
            parts.append(
                "## Cut candidates\nThe engine found no clear cut candidates for this deck. "
                "Say so plainly instead of inventing cuts."
            )

    parts.append("## User request")
    parts.append(context.user_request or "(No specific question — give a review appropriate to the mode.)")
    return "\n\n".join(parts)


def _cut_candidate_focus(cuts: dict) -> str:
    """Render the engine's actual cut candidates as an explicit allow-list."""
    cuts = cuts or {}
    labels = [
        ("required_cuts", "Required (legality/size)"),
        ("optional_cuts", "Optional (optimization)"),
        ("manual_review", "Manual review"),
        ("playtest_first", "Playtest before cutting"),
    ]
    lines: list[str] = []
    for key, label in labels:
        names = [str(e.get("card", "")) for e in (cuts.get(key) or []) if isinstance(e, dict) and e.get("card")]
        if names:
            lines.append(f"- {label}: {', '.join(names)}")
    return "\n".join(lines)


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
