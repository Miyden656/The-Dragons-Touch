"""Philosophy-aware cut-language helpers for The Dragon's Touch.

Version: v1.1.6

This module provides reusable language for explaining cut pressure through the
selected philosophy lens.

Important boundary:
- This module does not choose cuts.
- This module does not score cards.
- This module does not change deck analysis behavior.
- This module does not wire itself into existing cut reports.
- This module only formats explanation text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .philosophy_profile import PhilosophyProfile
from .philosophy_registry import get_lens_definition
from .runtime_config_mapping import context_from_profile, context_from_runtime_config


CUT_LANGUAGE_TYPES = (
    "standard",
    "strong",
    "low_confidence",
    "manual_review",
    "protected_conflict",
)


@dataclass(frozen=True)
class CutLanguageDefinition:
    """Cut-pressure language bundle for one philosophy lens."""

    lens: str
    standard: str
    strong: str
    low_confidence: str
    manual_review: str
    protected_conflict: str

    def get(self, language_type: str = "standard") -> str:
        normalized = normalize_cut_language_type(language_type)
        return getattr(self, normalized)

    def to_dict(self) -> Dict[str, str]:
        return {
            "lens": self.lens,
            "standard": self.standard,
            "strong": self.strong,
            "low_confidence": self.low_confidence,
            "manual_review": self.manual_review,
            "protected_conflict": self.protected_conflict,
        }


def normalize_cut_language_type(language_type: Optional[str]) -> str:
    text = str(language_type or "standard").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "": "standard",
        "normal": "standard",
        "default": "standard",
        "cut": "standard",
        "standard": "standard",
        "strong": "strong",
        "high": "strong",
        "high_confidence": "strong",
        "strong_cut": "strong",
        "low": "low_confidence",
        "low_confidence": "low_confidence",
        "uncertain": "low_confidence",
        "manual": "manual_review",
        "review": "manual_review",
        "manual_review": "manual_review",
        "context": "manual_review",
        "protected": "protected_conflict",
        "conflict": "protected_conflict",
        "protected_conflict": "protected_conflict",
    }
    if text not in aliases:
        raise ValueError(
            f"Unknown cut language type: {language_type!r}. Expected one of: "
            + ", ".join(CUT_LANGUAGE_TYPES)
        )
    return aliases[text]


def _definition(
    lens: str,
    *,
    standard: str,
    strong: str,
    low_confidence: str,
    manual_review: str,
    protected_conflict: str,
) -> CutLanguageDefinition:
    # Guard against drift: every language bundle must correspond to a known lens.
    canonical = get_lens_definition(lens).name
    return CutLanguageDefinition(
        lens=canonical,
        standard=standard,
        strong=strong,
        low_confidence=low_confidence,
        manual_review=manual_review,
        protected_conflict=protected_conflict,
    )


CUT_LANGUAGE_DEFINITIONS = (
    _definition(
        "Balanced / Unknown",
        standard="This card has cut pressure because its role is unclear compared to the deck's clearest visible plan.",
        strong="This is one of the stronger cut candidates because it does not clearly support the commander, the primary strategy, or any visible secondary package.",
        low_confidence="I would not cut this blindly. Its role is unclear, but it may have theme, meta, combo, or personal value that is not visible from the list alone.",
        manual_review="Review this manually because its value depends on user intent. It may belong for theme, personal preference, meta reasons, or a hidden package.",
        protected_conflict="This card may be protected by user intent, but the balanced read does not show enough visible evidence to treat it as core without that context.",
    ),
    _definition(
        "Timmy / Tammy",
        standard="This card has cut pressure because it does not clearly help create the memorable experience, theme, payoff, or table story the deck appears to want.",
        strong="This is one of the stronger cut candidates because it asks for space without helping the deck reach, protect, or express its intended experience.",
        low_confidence="I would review this carefully. If this card is part of the experience the pilot wants, it may deserve protection even if it is inefficient.",
        manual_review="Review this manually to decide whether it is carrying joy, theme, or emotional payoff. If it is not, it should face normal cut pressure.",
        protected_conflict="This card may be worth protecting for experience reasons, but the deck should be honest about the performance cost of keeping it.",
    ),
    _definition(
        "Johnny / Jenny",
        standard="This card has cut pressure because it does not clearly connect to the deck's idea, engine, interaction, constraint, or experiment.",
        strong="This is one of the stronger cut candidates because it looks disconnected from the machine the deck is trying to prove.",
        low_confidence="I would review this carefully. If it is a weak-looking connector piece in a real engine or combo line, it may deserve protection.",
        manual_review="Review this manually because the card may have a hidden role as fuel, outlet, converter, bridge, combo piece, or constraint-compliant role-filler.",
        protected_conflict="This card may be protected as part of the deck's idea, but the current explanation needs to show what it connects, converts, or proves.",
    ),
    _definition(
        "Spike",
        standard="This card has cut pressure because it may not justify its slot through consistency, efficiency, interaction, win conversion, or table fit.",
        strong="This is one of the stronger cut candidates because it appears inefficient, narrow, low-impact, or replaceable for the deck's intended performance level.",
        low_confidence="I would review this carefully if it is a low-power but strategy-critical piece. Spike pressure should not cut essential synergy just because it looks weak alone.",
        manual_review="Review this manually if the card's value depends on the intended table, power band, combo tolerance, or a specific matchup.",
        protected_conflict="This card may be protected by user intent or deck identity, but it carries a clear performance cost that should be named honestly.",
    ),
    _definition(
        "Big Moment",
        standard="This card has cut pressure because it is big, splashy, or expensive without clearly supporting the deck's actual payoff moment.",
        strong="This is one of the stronger cut candidates because it competes for payoff space without making the big moment more likely, protected, amplified, or decisive.",
        low_confidence="I would review this manually. If this card is part of the specific unforgettable play the pilot wants, it may deserve protection.",
        manual_review="Review this manually to decide whether it sets up, protects, amplifies, or converts the deck's big moment.",
        protected_conflict="This card may be emotionally tied to the big moment, but if it does not help the payoff happen, the deck should name it as a protected joy slot rather than a performance piece.",
    ),
    _definition(
        "Big Creature / Stompy",
        standard="This card has cut pressure because it does not clearly help large creatures become battlefield pressure.",
        strong="This is one of the stronger cut candidates because it is large or expensive without enough evasion, protection, immediate value, or combat payoff.",
        low_confidence="I would review this manually if it is a key threat, theme piece, pet card, or commander-specific payoff.",
        manual_review="Review this manually to decide whether it helps the deck cast, protect, push through, or profit from large creatures.",
        protected_conflict="This card may fit the Stompy identity, but size alone is not enough protection unless it becomes real pressure.",
    ),
    _definition(
        "Theme / Vibe",
        standard="This card has cut pressure because it supports the deck's flavor more than its function.",
        strong="This is one of the stronger cut candidates because it occupies a real slot without meaningfully supporting the commander, primary strategy, or a needed role within the theme.",
        low_confidence="I would review this manually if it is an identity anchor, lore card, joke card, or emotional theme piece.",
        manual_review="Review this manually to decide whether it is theme with function or flavor without enough purpose.",
        protected_conflict="This card may be protected as part of the deck's identity, but the deck should be honest if it is costing function.",
    ),
    _definition(
        "Pet Card",
        standard="This card has cut pressure unless it is a declared pet card or part of a protected pet-card package.",
        strong="This is one of the stronger cut candidates because it is neither a declared pet card nor a strong support piece for the deck's primary plan.",
        low_confidence="I would review this manually. If this card matters personally, it can be protected honestly; if not, it should face normal cut pressure.",
        manual_review="Review this manually to decide whether the card is a protected joy slot, pet-card support, or simply a low-synergy card.",
        protected_conflict="This card can stay because it matters to the pilot, but the deck should name the opportunity cost instead of pretending it is optimal.",
    ),
    _definition(
        "Let Me Do My Thing",
        standard="This card has cut pressure because it does not help the deck actually do the thing it was built to do.",
        strong="This is one of the stronger cut candidates because it neither advances the main experience nor helps the deck survive long enough to reach it.",
        low_confidence="I would review this manually if it is part of the specific play pattern or experience the pilot wants from the deck.",
        manual_review="Review this manually to decide whether it helps the deck get started, keep playing, recover, or reach the fun part.",
        protected_conflict="This card may be fun, but if it distracts from the deck doing its main thing, it should be protected only with that cost clearly named.",
    ),
    _definition(
        "Battlecruiser",
        standard="This card has cut pressure because it is slow without creating enough late-game payoff.",
        strong="This is one of the stronger cut candidates because it adds top-end pressure without improving ramp, resilience, recovery, or fair win conversion.",
        low_confidence="I would review this manually if it defines the late-game Commander experience the pilot wants.",
        manual_review="Review this manually to decide whether it is worth the wait or simply clunky.",
        protected_conflict="This card may preserve the Battlecruiser texture, but slow cards still need to create a meaningful payoff.",
    ),
    _definition(
        "Engine Builder",
        standard="This card has cut pressure because it does not clearly create fuel, provide an outlet, convert resources, repeat value, or pay off the engine.",
        strong="This is one of the stronger cut candidates because it neither feeds the machine nor helps the machine survive or win.",
        low_confidence="I would review this manually if it is a weak-looking connector piece in a real engine line.",
        manual_review="Review this manually to identify whether the card is fuel, outlet, converter, payoff, recursion, protection, or a hidden connector.",
        protected_conflict="This card may look weak, but it should be protected if it is a real connector. If it does not connect the machine, it has cut pressure.",
    ),
    _definition(
        "Commander Exploiter",
        standard="This card has cut pressure because it does not clearly interact with the commander's specific text, trigger, activated ability, restriction, or resource.",
        strong="This is one of the stronger cut candidates because it could go in many decks but does not exploit this commander in particular.",
        low_confidence="I would review this manually if it supports a commander line that is not obvious from the card name alone.",
        manual_review="Review this manually to decide whether it multiplies, protects, resets, copies, or converts something unique about the commander.",
        protected_conflict="This card may be good, but Commander Exploiter protection should come from interaction with this commander's unique text, not generic strength.",
    ),
    _definition(
        "Weird Card Rescuer",
        standard="This card has cut pressure because it is strange without enough visible support to make the experiment work.",
        strong="This is one of the stronger cut candidates because it asks the deck to carry an unusual effect without enough payoff or support.",
        low_confidence="I would review this manually if this is the declared weird card the pilot is trying to rescue.",
        manual_review="Review this manually to decide whether the strange card has a real shell, support package, or commander-specific role.",
        protected_conflict="This card may deserve protection as the experiment, but the deck should show how it makes the strange card meaningful.",
    ),
    _definition(
        "Theme Mechanic Inventor",
        standard="This card has cut pressure because it supports only one isolated piece of the hybrid concept without bridging the deck's ideas together.",
        strong="This is one of the stronger cut candidates because it makes the deck feel like two half-decks instead of one coherent hybrid.",
        low_confidence="I would review this manually if it is a bridge card whose overlap is not obvious from the list alone.",
        manual_review="Review this manually to decide whether the card creates real overlap between the deck's mechanics or themes.",
        protected_conflict="This card may fit one side of the concept, but it should be protected only if it helps the ideas touch.",
    ),
    _definition(
        "Self-Imposed Constraint Builder",
        standard="This card has cut pressure because it may not be the best functional option inside the chosen rule or limitation.",
        strong="This is one of the stronger cut candidates if it either violates the constraint or fills a role poorly when better legal options exist inside the constraint.",
        low_confidence="I would review this manually if the constraint makes this card one of the few available role-fillers.",
        manual_review="Review this manually to decide whether the card is weak in general but correct inside the declared restriction.",
        protected_conflict="This card may be protected by the deck-building rule, but the deck should name any structural weakness that the constraint creates.",
    ),
    _definition(
        "Combo Builder",
        standard="This card has cut pressure because its role in the combo line is unclear.",
        strong="This is one of the stronger cut candidates because it appears to be an unsupported combo fragment, dead narrow piece, or redundant piece beyond the package's needs.",
        low_confidence="I would review this manually if it is a weak-alone role-player required by a declared combo line.",
        manual_review="Review this manually to identify whether the card is a combo piece, enabler, tutor, protector, recursion piece, mana converter, outlet, or win condition.",
        protected_conflict="This card may be protected as a combo role-player, but the report should clearly state what role it plays in the line.",
    ),
    _definition(
        "Consistency Maximizer",
        standard="This card has cut pressure because it increases variance, creates awkward draws, or does not help the deck do its intended thing more often.",
        strong="This is one of the stronger cut candidates because it is narrow, high-variance, bad from behind, or only good when everything already lines up.",
        low_confidence="I would review this manually if it is a redundant enabler or backup effect that reduces fail states.",
        manual_review="Review this manually to decide whether the card reduces non-games or creates more of them.",
        protected_conflict="This card may be fun or powerful, but if it creates too many dead draws, the consistency cost should be named.",
    ),
    _definition(
        "Efficiency Optimizer",
        standard="This card has cut pressure because it may be playable but replaceable compared to cleaner alternatives.",
        strong="This is one of the stronger cut candidates because it is overcosted, narrow, low-impact, win-more, or inefficient for its slot.",
        low_confidence="I would review this manually if it is less efficient by rate but unusually efficient inside this deck's specific synergy.",
        manual_review="Review this manually to decide whether the card's rate, flexibility, role compression, or synergy justifies the slot.",
        protected_conflict="This card may be protected by theme or user intent, but it has efficiency pressure that should be named honestly.",
    ),
    _definition(
        "Curve and Mana Discipline",
        standard="This card has cut pressure because it adds stress to the deck's curve, mana, sequencing, or color requirements.",
        strong="This is one of the stronger cut candidates because it worsens an already crowded mana value, shaky mana base, or slow early game.",
        low_confidence="I would review this manually if it is expensive but essential, or if it functions as a mana sink rather than a normal curve card.",
        manual_review="Review this manually to decide whether the deck can cast it on time and use mana efficiently around it.",
        protected_conflict="This card may be important, but if it strains the curve or mana base, the deck needs enough infrastructure to justify keeping it.",
    ),
    _definition(
        "Competitive Closer",
        standard="This card has cut pressure because it adds value without helping the deck actually end the game.",
        strong="This is one of the stronger cut candidates because it prolongs the game without converting resources, board position, or advantage into a win.",
        low_confidence="I would review this manually if it is a finisher whose power depends on board state, table speed, or combo tolerance.",
        manual_review="Review this manually to decide whether the card is setup, payoff, or a real closing tool.",
        protected_conflict="This card may be enjoyable value, but if the deck already has enough value, it needs to justify why it is not occupying a closer slot.",
    ),
    _definition(
        "Power-Level Calibrator",
        standard="This card has cut pressure because it may not match the intended table strength.",
        strong="This is one of the stronger cut candidates if it pushes the deck above the table, falls below the table, or violates the user's stated power expectations.",
        low_confidence="I would review this manually if the card's appropriateness depends heavily on the user's pod, bracket, budget, or combo tolerance.",
        manual_review="Review this manually to decide whether the card is too weak, too strong, too fast, too oppressive, or just right for the intended table.",
        protected_conflict="This card may be protected by identity or preference, but it should be named as a table-fit cost if it mismatches the pod.",
    ),
    _definition(
        "Interaction Controller",
        standard="This card has cut pressure if it does not help the deck answer threats, protect its plan, or avoid preventable losses.",
        strong="This is one of the stronger cut candidates if the deck needs answers and this slot does not interact, protect, or advance the proactive plan.",
        low_confidence="I would review this manually if it is narrow interaction that may be correct for the user's actual meta.",
        manual_review="Review this manually to decide what problem this card answers and whether that problem matters at the intended table.",
        protected_conflict="This card may be part of the deck's proactive identity, but if the deck cannot answer common threats, non-interactive slots carry pressure.",
    ),
)

CUT_LANGUAGE_REGISTRY: Dict[str, CutLanguageDefinition] = {
    definition.lens: definition for definition in CUT_LANGUAGE_DEFINITIONS
}


def get_cut_language_definition(lens: str) -> CutLanguageDefinition:
    """Return the cut-language definition for a philosophy lens."""
    canonical = get_lens_definition(lens).name
    try:
        return CUT_LANGUAGE_REGISTRY[canonical]
    except KeyError as exc:
        raise ValueError(f"No cut-language definition is registered for {lens!r}.") from exc


def get_cut_pressure_language(lens: str, language_type: str = "standard") -> str:
    """Return a cut-pressure sentence for a philosophy lens."""
    return get_cut_language_definition(lens).get(language_type)


def get_cut_pressure_language_from_profile(
    profile: PhilosophyProfile,
    language_type: str = "standard",
) -> str:
    """Return cut-pressure language using an existing PhilosophyProfile."""
    return get_cut_pressure_language(profile.selected_lens, language_type)


def get_cut_pressure_language_from_runtime_config(
    config: Optional[Mapping[str, Any]],
    language_type: str = "standard",
) -> str:
    """Return cut-pressure language from raw runtime/UI config data."""
    context = context_from_runtime_config(config)
    return get_cut_pressure_language(context.profile.selected_lens, language_type)


def format_cut_pressure_note(
    lens: str,
    card_name: Optional[str] = None,
    *,
    reason: Optional[str] = None,
    language_type: str = "standard",
) -> str:
    """Format a short markdown cut-pressure note.

    This does not decide whether a card should be cut. It only phrases the note
    through the selected philosophy lens.
    """
    base = get_cut_pressure_language(lens, language_type)
    prefix = f"**{card_name}:** " if card_name else ""
    suffix = f" {str(reason).strip()}" if reason else ""
    return f"{prefix}{base}{suffix}".strip()


def format_cut_pressure_note_from_profile(
    profile: PhilosophyProfile,
    card_name: Optional[str] = None,
    *,
    reason: Optional[str] = None,
    language_type: str = "standard",
) -> str:
    """Format a cut-pressure note from an existing PhilosophyProfile."""
    return format_cut_pressure_note(
        profile.selected_lens,
        card_name,
        reason=reason,
        language_type=language_type,
    )


def format_cut_pressure_note_from_runtime_config(
    config: Optional[Mapping[str, Any]],
    card_name: Optional[str] = None,
    *,
    reason: Optional[str] = None,
    language_type: str = "standard",
) -> str:
    """Format a cut-pressure note from runtime/UI config data."""
    context = context_from_runtime_config(config)
    return format_cut_pressure_note(
        context.profile.selected_lens,
        card_name,
        reason=reason,
        language_type=language_type,
    )


def cut_language_registry_as_dict() -> Dict[str, Dict[str, str]]:
    """Serialize the full cut-language registry."""
    return {
        definition.lens: definition.to_dict()
        for definition in CUT_LANGUAGE_DEFINITIONS
    }


def validate_cut_language_registry_alignment() -> bool:
    """Return True when cut-language entries align with the philosophy registry."""
    from .philosophy_registry import PHILOSOPHY_LENS_DEFINITIONS

    philosophy_names = tuple(definition.name for definition in PHILOSOPHY_LENS_DEFINITIONS)
    cut_names = tuple(definition.lens for definition in CUT_LANGUAGE_DEFINITIONS)
    return philosophy_names == cut_names
