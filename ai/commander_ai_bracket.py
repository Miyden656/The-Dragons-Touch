"""Power-bracket calibration block for the persona prompt.

A persona decides WHAT to value; the bracket decides HOW MUCH power is appropriate.
Without this, a guide gives the same advice for a kitchen-table bracket-1 build and
a bracket-5 cEDH build. This module renders a short calibration block — keyed to
the deck's target bracket (1-5) — that the persona's recommendations scale to.

Presentation-only: it shapes how recommendations are calibrated in the prompt. It
does NOT change the engine's scoring, cut pressure, or the capped philosophy bias,
and it never overrides the pilot's stated intent or the engine's verified facts.
"""

from __future__ import annotations

import re
from typing import Any

# Calibration guidance per Commander power bracket (the WotC 1-5 system).
BRACKET_TIERS: dict[int, dict[str, str]] = {
    1: {
        "label": "Bracket 1 — Exhibition / ultra-casual",
        "guidance": (
            "Calibrate to fun, theme, and self-expression over power. Favor flavorful, "
            "on-theme, and personal cards, and it is fine to keep a beloved-but-weak card. "
            "Do NOT recommend tutors, fast mana, two-card infinite combos, mass land denial, "
            "or stax. Slow, high-curve, win-eventually decks are expected; interaction is light."
        ),
    },
    2: {
        "label": "Bracket 2 — Core / precon level",
        "guidance": (
            "Calibrate to casual, synergy-forward but unoptimized (upgraded-precon feel). A few "
            "efficient staples and light tutoring are fine; avoid early or explosive combos, heavy "
            "fast mana, and stax. Recommend role-fillers and synergy over raw power. Games run long; "
            "keep interaction modest and fair."
        ),
    },
    3: {
        "label": "Bracket 3 — Upgraded / focused",
        "guidance": (
            "Calibrate to a tuned, intentional deck. Some tutors, a little fast mana, and a single "
            "well-telegraphed late-game combo are acceptable. Recommend consistency and efficiency "
            "upgrades, a real interaction suite, and a clear win path — but not cEDH speed. Balance "
            "power against the table."
        ),
    },
    4: {
        "label": "Bracket 4 — Optimized / high-power",
        "guidance": (
            "Calibrate to strong and efficient, just below cEDH. Tutors, fast mana, compact combos, "
            "and dense interaction are all on the table. Recommend the most efficient version of each "
            "effect, lower the curve, and prioritize consistency and protected win lines. Expect fast, "
            "interactive games."
        ),
    },
    5: {
        "label": "Bracket 5 — cEDH",
        "guidance": (
            "Calibrate to maximum efficiency and speed. Recommend best-in-slot fast mana, tutors, free "
            "interaction (Force-style), and compact, resilient combos with a plan to win or interact in "
            "the first several turns. Cut anything slow, win-more, or purely thematic. Assume a "
            "knowledgeable, meta-aware, interactive table."
        ),
    },
}

_KEYWORD_TIERS = (
    ("cedh", 5), ("competitive", 5),
    ("optimized", 4), ("high power", 4), ("high-power", 4),
    ("upgraded", 3), ("focused", 3),
    ("core", 2), ("precon", 2),
    ("exhibition", 1), ("ultra-casual", 1), ("ultra casual", 1),
)


def normalize_bracket(value: Any) -> int | None:
    """Parse a bracket value ('Bracket 3', '3', 'cEDH', ...) to a tier 1-5, else None."""
    text = str(value or "").strip().lower()
    if not text or "not specified" in text or text in ("unknown", "none"):
        return None
    m = re.search(r"\b([1-5])\b", text)
    if m:
        return int(m.group(1))
    for kw, tier in _KEYWORD_TIERS:
        if kw in text:
            return tier
    return None


def render_bracket_block(bracket_view: Any) -> str:
    """Render the power-bracket calibration block from the AI bracket view.

    Prefers the pilot's intended bracket; falls back to the engine's estimate.
    Returns '' when no bracket can be determined (so the prompt stays clean).
    """
    bv = bracket_view or {}
    if not isinstance(bv, dict):
        return ""
    intended = bv.get("intended_bracket")
    estimated = bv.get("estimated_bracket")
    tier = normalize_bracket(intended)
    source = "the pilot's target"
    if tier is None:
        tier = normalize_bracket(estimated)
        source = "the deck's current read"
    if tier is None:
        return ""

    spec = BRACKET_TIERS[tier]
    lines = [
        "## Power bracket calibration",
        f"Target power level: {spec['label']} ({source}).",
        spec["guidance"],
        "Scale your recommendations to this power level. This sets the appropriate power "
        "ceiling — it does NOT override the pilot's stated intent or the engine's verified "
        "facts, and never push a deck to a higher bracket than the pilot wants.",
    ]
    return "\n".join(lines)
