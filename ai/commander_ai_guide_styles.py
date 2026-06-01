"""Guide styles — the NET-NEW tone/format axis for Commander AI responses.

Guide style is orthogonal to persona:
    persona  -> WHAT to prioritize (protect / cut / prefer) AND the VOICE/attitude
                to speak in (each philosophy carries its own + a family tone)  [engine]
    style    -> the LENGTH, STRUCTURE, and FORMAT of the answer                [here]

So the two compose: the persona sets the voice (warm / analytical / decisive…),
the guide style sets how long and how structured the answer is. Style blocks here
deliberately avoid dictating tone so they don't fight the persona's voice.

These four tokens (adventurer / archivist / strategist / minimal) are the single
source of truth for response style. They are NOT the same as the engine's
`guide_presentation` (masculine/feminine/random/none guide NAME); see the note in
ai/commander_ai_config.py about the retired "<X> Guide" labels.
"""

from __future__ import annotations

from ai.commander_ai_config import DEFAULT_GUIDE_STYLE, normalize_guide_style


# NOTE: these govern LENGTH / STRUCTURE / FORMAT only. The persona block owns the
# VOICE (tone/attitude). Keep tone words out of here so the two don't conflict —
# e.g. a Pet Card persona in Strategist style = warm voice, lean structure.
_GUIDE_STYLE_BLOCKS: dict[str, str] = {
    "adventurer": (
        "## Guide style: Adventurer\n"
        "Format: accessible and flowing. Favor short paragraphs over dense lists. "
        "Define a term the first time you use it. Lead with what the deck does well "
        "before suggesting changes. Room to explain. (Speak it in the persona's voice.)"
    ),
    "archivist": (
        "## Guide style: Archivist\n"
        "Format: structured and thorough. Use clear headers and bullet lists. Cite the "
        "relevant CONTEXT field for each claim. Complete and organized so it reads well "
        "saved to a report. Thoroughness over brevity, but never padding."
    ),
    "strategist": (
        "## Guide style: Strategist\n"
        "Format: lean and lead-with-the-call. State the call, then the reason; highest-"
        "leverage changes first; minimal warm-up. Assume Commander fluency in vocabulary "
        "(bracket, color identity, curve, anchors/payoffs/enablers)."
    ),
    "minimal": (
        "## Guide style: Minimal\n"
        "Format: as few words as the question allows. Answer first. Compact lists. No "
        "preamble, no recap, no closing pleasantries. If one line is correct, give one line."
    ),
}


def render_guide_style_block(style: str | None) -> str:
    """Return the instruction block for a guide style (defaults to adventurer)."""
    key = normalize_guide_style(style)
    return _GUIDE_STYLE_BLOCKS.get(key, _GUIDE_STYLE_BLOCKS[DEFAULT_GUIDE_STYLE])


def available_styles() -> tuple[str, ...]:
    return tuple(_GUIDE_STYLE_BLOCKS.keys())
