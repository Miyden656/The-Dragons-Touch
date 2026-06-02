"""Philosophy-aware persona opening lines for The Dragon's Touch.

Version: v1.1.20

This module supplies the short, first-person "let me guide you through your deck"
greeting each philosophy guide opens the player-facing report with. It is the
deterministic, code-level counterpart to the LLM voice asset
(ai/prompts/persona_voices.md): the wording is distilled from the same signature
voice profiles, but it lives here so the report opening is robust without any model.

Important boundary:
- This module does not choose cuts.
- This module does not score cards.
- This module does not change deck analysis behavior.
- It only supplies opening/greeting wording, keyed by canonical philosophy lens.
"""

from __future__ import annotations

from typing import Dict

from .philosophy_registry import get_lens_definition


# One first-person "mission" sentence per lens, in each guide's own voice. The
# greeting wrapper (report_section.format_persona_opening) supplies the guide name,
# role, and the pilot-authority reassurance; this registry holds only the voiced
# line that says *how this guide reads a deck*. Signature vocabulary is woven in so
# the opening sounds like the guide even when the named-guide toggle is off.
PERSONA_OPENING_MISSIONS: Dict[str, str] = {
    "Balanced / Unknown": (
        "I'll read your deck's strongest trail signs and map its clearest path "
        "before I judge any single card."
    ),
    "Timmy / Tammy": (
        "I'll look after the experience you're building — the memorable moments and "
        "table stories — while staying honest about whether the fun part actually "
        "happens often enough."
    ),
    "Johnny / Jenny": (
        "I'll treat your deck as a machine and an idea to prove, protecting the "
        "connectors and hidden synergy while staying honest about cleverness that "
        "isn't supported yet."
    ),
    "Spike": (
        "I'll focus on consistency and win conversion at your intended table, naming "
        "the slots I'd pressure first without erasing your budget, bracket, or intent."
    ),
    "Big Moment": (
        "I'll help you build toward the payoff turn and make the big moment real, "
        "grounding the spectacle in the setup that actually delivers it."
    ),
    "Big Creature / Stompy": (
        "I'll make sure your size turns into real battlefield pressure — evasion, "
        "protection, and payoff so the big threats actually connect."
    ),
    "Theme / Vibe": (
        "I'll help your deck feel more like itself, celebrating the identity while "
        "making sure the theme still does real mechanical work."
    ),
    "Pet Card": (
        "I'll protect the cards that matter to you as honest joy slots, naming what "
        "they cost the deck instead of pretending they're free."
    ),
    "Let Me Do My Thing": (
        "I'll help the deck actually get to do its thing, championing the fun while "
        "keeping the support that lets you reliably reach it."
    ),
    "Battlecruiser": (
        "I'll help you build toward the big Commander game and a fair finisher, "
        "without romanticizing clunky cards that just stumble."
    ),
    "Engine Builder": (
        "I'll trace the resource flow through your deck and make sure every gear "
        "turns another gear instead of sitting idle."
    ),
    "Commander Exploiter": (
        "I'll keep your commander's exact text at the center, pushing what this "
        "commander does that no other one can."
    ),
    "Weird Card Rescuer": (
        "I'll give your strange card a fair chance, testing honestly whether this "
        "shell actually unlocks it."
    ),
    "Theme Mechanic Inventor": (
        "I'll hunt for the bridge where your two ideas overlap, so the deck reads as "
        "one coherent build and not two half-decks."
    ),
    "Self-Imposed Constraint Builder": (
        "I'll respect the rule you've chosen and find the best option inside it, "
        "without pretending the constraint has no cost."
    ),
    "Combo Builder": (
        "I'll name each card's role in the line — enabler, outlet, payoff — and keep "
        "your table's combo tolerance in view."
    ),
    "Consistency Maximizer": (
        "I'll think in floors and ceilings and average games, helping the deck do its "
        "thing more often without scolding every bit of variance."
    ),
    "Efficiency Optimizer": (
        "I'll weigh each card against cleaner options and its opportunity cost, asking "
        "whether the slot could simply do more."
    ),
    "Curve and Mana Discipline": (
        "I'll look after castability and sequencing — the boring mana that quietly "
        "keeps your deck from stumbling."
    ),
    "Competitive Closer": (
        "I'll push your value engine toward a finish line, turning advantage into "
        "lethal pressure instead of another lap."
    ),
    "Power-Level Calibrator": (
        "I'll aim for correct strength rather than maximum strength, naming overshoot "
        "or undershoot plainly for your intended table."
    ),
    "Interaction Controller": (
        "I'll frame removal as coverage for what stops your plan, balancing answers "
        "against the deck's own proactive identity."
    ),
}


def get_persona_opening_mission(lens: str) -> str:
    """Return the first-person opening mission sentence for a philosophy lens.

    Canonicalizes the lens name through the philosophy registry (guarding drift),
    then returns its voiced opening line. Falls back to the Balanced / Unknown line
    if a lens has no registered mission so the opening is never load-bearing.
    """
    canonical = get_lens_definition(lens).name
    return PERSONA_OPENING_MISSIONS.get(
        canonical, PERSONA_OPENING_MISSIONS["Balanced / Unknown"]
    )


def persona_opening_registry_as_dict() -> Dict[str, str]:
    """Serialize the full opening-mission registry."""
    return dict(PERSONA_OPENING_MISSIONS)


def validate_persona_opening_registry_alignment() -> bool:
    """Return True when opening missions cover exactly the philosophy lenses."""
    from .philosophy_registry import PHILOSOPHY_LENS_DEFINITIONS

    philosophy_names = tuple(definition.name for definition in PHILOSOPHY_LENS_DEFINITIONS)
    return set(philosophy_names) == set(PERSONA_OPENING_MISSIONS)
