"""Guide styles — the NET-NEW tone/format axis for Commander AI responses.

Guide style is orthogonal to persona:
    persona  -> WHAT to prioritize (protect / cut / prefer)   [from the engine]
    style    -> HOW to say it (tone, length, formatting)       [defined here]

These four tokens (adventurer / archivist / strategist / minimal) are the single
source of truth for response style. They are NOT the same as the engine's
`guide_presentation` (masculine/feminine/random/none guide NAME); see the note in
ai/commander_ai_config.py about the retired "<X> Guide" labels.
"""

from __future__ import annotations

from ai.commander_ai_config import DEFAULT_GUIDE_STYLE, normalize_guide_style


_GUIDE_STYLE_BLOCKS: dict[str, str] = {
    "adventurer": (
        "## Guide style: Adventurer\n"
        "Warm, encouraging, and accessible. Talk like a friendly, knowledgeable "
        "playgroup-mate. Keep jargon light and define a term the first time you use "
        "it. Celebrate what the deck does well before suggesting changes. Favor short "
        "paragraphs over dense lists. Good for newer or casual players."
    ),
    "archivist": (
        "## Guide style: Archivist\n"
        "Structured, thorough, and record-friendly. Use clear headers and bullet "
        "lists. Show your reasoning and cite the relevant CONTEXT field for each "
        "claim. Be complete and organized so the answer reads well saved to a report. "
        "Thoroughness over brevity, but never padding."
    ),
    "strategist": (
        "## Guide style: Strategist\n"
        "Direct, analytical, and optimization-focused. Assume Commander fluency — use "
        "bracket, color identity, curve, ramp/draw/removal/protection, and "
        "anchors/payoffs/enablers naturally. Lead with the call, then the reason. Cut "
        "the warm-up. Prioritize the highest-leverage changes first."
    ),
    "minimal": (
        "## Guide style: Minimal\n"
        "Short, clean, low-fluff. Answer first, in as few words as the question allows. "
        "Use compact lists. No preamble, no recap, no closing pleasantries. If a "
        "one-line answer is correct, give one line."
    ),
}


def render_guide_style_block(style: str | None) -> str:
    """Return the instruction block for a guide style (defaults to adventurer)."""
    key = normalize_guide_style(style)
    return _GUIDE_STYLE_BLOCKS.get(key, _GUIDE_STYLE_BLOCKS[DEFAULT_GUIDE_STYLE])


def available_styles() -> tuple[str, ...]:
    return tuple(_GUIDE_STYLE_BLOCKS.keys())
