"""Philosophy-aware protected-card language helpers for The Dragon's Touch.

Version: v1.1.7

This module provides reusable language for explaining why an already-protected
card deserves protection through the selected philosophy lens.

Important boundary:
- This module does not decide which cards are protected.
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
from .runtime_config_mapping import context_from_runtime_config


PROTECTED_LANGUAGE_TYPES = (
    "standard",
    "core",
    "support",
    "low_power_high_synergy",
    "user_intent",
    "manual_review",
)


@dataclass(frozen=True)
class ProtectedLanguageDefinition:
    """Protected-card language bundle for one philosophy lens."""

    lens: str
    standard: str
    core: str
    support: str
    low_power_high_synergy: str
    user_intent: str
    manual_review: str

    def get(self, language_type: str = "standard") -> str:
        return getattr(self, normalize_protected_language_type(language_type))

    def to_dict(self) -> Dict[str, str]:
        return {
            "lens": self.lens,
            "standard": self.standard,
            "core": self.core,
            "support": self.support,
            "low_power_high_synergy": self.low_power_high_synergy,
            "user_intent": self.user_intent,
            "manual_review": self.manual_review,
        }


def normalize_protected_language_type(language_type: Optional[str]) -> str:
    text = str(language_type or "standard").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "": "standard",
        "normal": "standard",
        "default": "standard",
        "protected": "standard",
        "standard": "standard",
        "core": "core",
        "key": "core",
        "essential": "core",
        "critical": "core",
        "support": "support",
        "enabler": "support",
        "infrastructure": "support",
        "setup": "support",
        "low_power": "low_power_high_synergy",
        "high_synergy": "low_power_high_synergy",
        "low_power_high_synergy": "low_power_high_synergy",
        "weak_but_synergistic": "low_power_high_synergy",
        "context": "low_power_high_synergy",
        "intent": "user_intent",
        "user": "user_intent",
        "user_intent": "user_intent",
        "pet": "user_intent",
        "declared": "user_intent",
        "manual": "manual_review",
        "review": "manual_review",
        "manual_review": "manual_review",
    }
    if text not in aliases:
        raise ValueError(
            f"Unknown protected language type: {language_type!r}. Expected one of: "
            + ", ".join(PROTECTED_LANGUAGE_TYPES)
        )
    return aliases[text]


def _definition(
    lens: str,
    standard: str,
    core: str,
    support: str,
    low_power_high_synergy: str,
    user_intent: str,
    manual_review: str,
) -> ProtectedLanguageDefinition:
    canonical = get_lens_definition(lens).name
    return ProtectedLanguageDefinition(
        lens=canonical,
        standard=standard,
        core=core,
        support=support,
        low_power_high_synergy=low_power_high_synergy,
        user_intent=user_intent,
        manual_review=manual_review,
    )


_PROTECTED_ROWS = [
    ("Balanced / Unknown", "I would protect this because it supports one of the deck's clearest visible trail signs.", "I would protect this as a core card because it directly supports the commander, primary strategy, or strongest visible path.", "I would protect this as practical infrastructure while the final philosophy direction is still being clarified.", "This may look modest by raw power, but it deserves protection if it clearly supports the deck's visible plan.", "I would protect this because the user identified it as important, even if the decklist alone would not prove that context.", "This should be reviewed before cutting because its value may depend on theme, meta, combo, or personal intent that is not visible from the list alone."),
    ("Timmy / Tammy", "I would protect this because it helps create the memorable experience, theme, payoff, or table story the deck is trying to preserve.", "I would protect this as part of the deck's emotional center: it helps the deck feel like the experience the pilot wants.", "I would protect this because it helps the deck reach, protect, or repeat the experience that makes the deck fun.", "This may not be efficient by raw rate, but it can belong if it protects the deck's joy, theme, or intended experience.", "I would protect this because the pilot has given it personal or experiential importance, and the deck is allowed to make room for that honestly.", "Review this before cutting because it may be carrying theme, favorite-card value, emotional payoff, or the table story the user wants."),
    ("Johnny / Jenny", "I would protect this because it appears to support the deck's idea, engine, experiment, constraint, or unusual interaction.", "I would protect this as a core idea piece because it helps prove what the deck is trying to prove.", "I would protect this because it connects pieces, supplies fuel, enables the experiment, or keeps the machine moving.", "This may look weak alone, but it deserves protection if it is a real connector inside the deck's engine or interaction.", "I would protect this because the pilot chose this idea or experiment intentionally, even if the card is unusual by generic standards.", "Review this before cutting because it may have a hidden role as fuel, outlet, converter, bridge, combo piece, or constraint-compliant role-filler."),
    ("Spike", "I would protect this because it improves the deck's consistency, efficiency, interaction, win conversion, resilience, or table fit.", "I would protect this as a core performance card because it helps the deck execute its plan reliably at the intended table.", "I would protect this because it fills a necessary role efficiently or reduces a common fail state.", "This may look low-impact, but it deserves protection if it is strategy-critical and improves the deck's actual performance.", "I would protect this if the user has chosen it as part of the deck's identity, while still naming any performance cost honestly.", "Review this before cutting if its value depends on table speed, power band, combo tolerance, or specific matchup needs."),
    ("Big Moment", "I would protect this because it helps create, protect, amplify, or convert the deck's unforgettable payoff moment.", "I would protect this as part of the payoff structure. It is one of the cards that makes the big moment real.", "I would protect this because it sets the stage for the payoff turn, even if it is not the flashy part.", "This may look quiet, but it deserves protection if it helps the deck actually reach or protect the big moment.", "I would protect this if it is personally tied to the moment the pilot wants to experience.", "Review this before cutting because it may be part of the specific payoff moment the deck is built to remember."),
    ("Big Creature / Stompy", "I would protect this because it helps large creatures become real battlefield pressure.", "I would protect this as a key threat or payoff because it turns the deck's size into damage, cards, removal, or board dominance.", "I would protect this because Stompy decks need ramp, evasion, haste, trample, protection, or draw to make big threats matter.", "This may be small or modest, but it deserves protection if it helps the big creatures arrive, survive, connect, or pay off.", "I would protect this if it is part of the creature identity the pilot wants the deck to express.", "Review this before cutting because it may be a theme piece, pet threat, commander payoff, or pressure enabler."),
    ("Theme / Vibe", "I would protect this because it carries part of the deck's identity while still contributing to the game plan.", "I would protect this as an identity anchor. It helps define what the deck is supposed to feel like.", "I would protect this because it fills a needed role without breaking the deck's theme.", "This may be below rate, but it deserves protection if it is theme with function rather than flavor alone.", "I would protect this if it is central to the deck's story, joke, aesthetic, emotional concept, or pilot attachment.", "Review this before cutting because its theme value may not be visible from mechanical role alone."),
    ("Pet Card", "I would protect this because the pilot identified it as personally important.", "I would protect this as a declared joy slot. Its purpose is not to be the most efficient card; its purpose is to preserve something that matters.", "I would protect this support piece only if it is necessary to make the declared pet card function.", "This may not be optimal, but it can belong if the pilot is intentionally making room for it.", "I would protect this because the user gave it a reason to stay; the deck should account for the cost honestly.", "Review this before cutting because it may be a pet card, pet-card support piece, or temporary protected experience card."),
    ("Let Me Do My Thing", "I would protect this because it helps the deck actually reach the experience it was built for.", "I would protect this as core structure because it helps the deck do the thing instead of just hoping the thing happens.", "I would protect this because it helps the deck get started, keep playing, protect the commander, recover, or add needed redundancy.", "This may not be flashy, but it deserves protection if it helps the deck participate and reach the fun part.", "I would protect this if the pilot says it is part of the specific experience they want the deck to have.", "Review this before cutting because it may be the practical support that makes the deck's intended experience possible."),
    ("Battlecruiser", "I would protect this because it supports the deck's late-game Commander identity.", "I would protect this as a meaningful late-game payoff or fair finisher that makes the big game worth building toward.", "I would protect this because Battlecruiser decks need ramp, draw, recovery, resilience, and mana sinks to make scale realistic.", "This may be slow by optimized standards, but it deserves protection if it creates meaningful big-game texture.", "I would protect this if it defines the slower, larger Commander experience the pilot wants.", "Review this before cutting because its value depends on whether the table wants the same big-game texture."),
    ("Engine Builder", "I would protect this because it helps the deck's machine keep turning.", "I would protect this as a core engine piece because it creates fuel, provides an outlet, converts resources, repeats value, or pays off the engine.", "I would protect this because it connects resources, recurs pieces, protects the engine, or solves an engine bottleneck.", "This may look weak alone, but it deserves protection if it is a real gear in the machine.", "I would protect this if the pilot is intentionally building around this engine line or resource loop.", "Review this before cutting because it may be a hidden fuel, outlet, converter, payoff, recursion piece, or connector."),
    ("Commander Exploiter", "I would protect this because it directly interacts with the commander's specific text.", "I would protect this as core commander support because it pushes what this commander can do that other commanders cannot.", "I would protect this because it helps the deck exploit the commander's unique text, scaling pattern, or payoff structure.", "This may look narrow, but it deserves protection if it meaningfully exploits the commander's exact wording.", "I would protect this if the pilot wants the deck to be about the commander's unique text rather than generic archetype strength.", "Review this before cutting because its commander-specific role may not be obvious without reading the commander's text carefully."),
    ("Weird Card Rescuer", "I would protect this if it is the strange card the deck is intentionally trying to make meaningful.", "I would protect this as the declared experiment if the deck is built to prove this overlooked card has a home.", "I would protect this support piece if it makes the rescued card realistic instead of just cute.", "This may look bad by normal standards, but it deserves protection if the shell actually makes it function.", "I would protect this if the pilot specifically wants to rescue or prove this card.", "Review this before cutting because the card may be unusual on purpose and needs to be judged by whether the experiment works."),
    ("Theme Mechanic Inventor", "I would protect this because it bridges the deck's mechanics or themes into one coherent plan.", "I would protect this as a core bridge card because it is where the deck's unusual ideas actually touch.", "I would protect this because it supports more than one package and helps the deck avoid becoming two half-decks.", "This may look modest alone, but it deserves protection if it creates real overlap between the deck's ideas.", "I would protect this if the pilot intentionally wants these mechanics or themes blended together.", "Review this before cutting because its value may come from being a bridge rather than a standalone payoff."),
    ("Self-Imposed Constraint Builder", "I would protect this because it fills a needed role inside the chosen rule or limitation.", "I would protect this as a premise-integrity card if it preserves the deck's restriction while keeping the deck functional.", "I would protect this because constrained decks sometimes need unusual role-fillers that are correct inside the limited pool.", "This may be weaker than the unrestricted option, but it deserves protection if it is correct within the constraint.", "I would protect this if the user chose the restriction and this card helps honor that premise.", "Review this before cutting because its value depends on the declared rule, card pool, budget, or self-imposed limitation."),
    ("Combo Builder", "I would protect this through the combo lens only if it has a defined role in an actual combo line or combo-adjacent engine.", "I would protect this as a core combo piece only when the relevant line cannot function without it and the line respects the pilot's combo tolerance.", "I would protect this when it is clearly an enabler, tutor, protector, recursion piece, mana converter, outlet, or win condition for the combo; unsupported fragments should remain reviewable.", "This may be weak alone, but it deserves protection if it is a required role-player in the combo package.", "I would protect this if the pilot declared this combo package and it respects their combo tolerance.", "Review this before cutting because combo pieces often look replaceable until their exact line role is identified."),
    ("Consistency Maximizer", "I would protect this through the consistency lens when it makes the deck do its intended thing more often, rather than merely being a card the deck likes.", "I would protect this as a core consistency piece when it directly reduces fail states, dead draws, awkward hands, or non-games.", "I would protect this when it provides real redundancy, draw, selection, fixing, or backup access to key effects; if that role is unclear, keep it in manual review.", "This may not be exciting, but it deserves protection if it improves the deck's average game pattern.", "I would protect this if the pilot's stated goal is to make the deck smoother and more reliable.", "Review this before cutting because boring consistency cards are often what make the fun cards happen."),
    ("Efficiency Optimizer", "I would protect this through the efficiency lens when it clearly justifies its slot by rate, flexibility, role compression, or a strong contribution to the deck's actual plan.", "I would protect this as a core efficient role-filler only when it performs an important job cleanly for its cost and is not simply protected by familiarity.", "I would protect this when it actually compresses roles, lowers opportunity cost, or improves the deck's baseline performance; otherwise compare it against alternatives.", "This may not look flashy, but it deserves protection if it is the cleanest efficient version of the role this deck needs.", "I would protect this if the pilot wants the deck tightened around efficiency and cleaner slot use.", "Review this before cutting because replaceability depends on available alternatives, role density, and deck constraints."),
    ("Curve and Mana Discipline", "I would protect this in the context of curve and mana discipline when it supports cleaner sequencing, smoother mana, or a realistic path to casting the deck's important spells.", "I would protect this as core curve or mana infrastructure only when it directly prevents the deck from stumbling on color, timing, ramp, or sequencing.", "I would protect this when its role is land quality, fixing, ramp, early setup, cost reduction, or mana use; if it is not actually serving one of those jobs, review it normally.", "This may be boring, but it deserves protection if it makes the deck's curve and sequencing work.", "I would protect this if the pilot's goal is smoother mana, cleaner sequencing, and fewer non-games.", "Review this before cutting because mana infrastructure often looks replaceable until the deck starts missing early turns."),
    ("Competitive Closer", "I would protect this because it helps the deck actually end the game.", "I would protect this as a core closer because it converts the deck's resources, board state, or advantage into a win.", "I would protect this because it turns setup into lethal pressure, inevitability, drain, burn, mill, combat, or an allowed combo finish.", "This may look narrow, but it deserves protection if it is the deck's cleanest route from advantage to victory.", "I would protect this if the pilot wants the deck to stop durdling and close games more decisively.", "Review this before cutting because some finishers only look weak until the deck's resource engine is considered."),
    ("Power-Level Calibrator", "I would protect this in the context of table fit when it helps the deck land at the intended power level without pushing above or falling below the target environment.", "I would protect this as a table-fit card only if it meaningfully supports the desired bracket, pace, resilience, or win pattern without overshooting or undershooting.", "I would protect this when the improvement is appropriate for the chosen bracket, budget, combo tolerance, and pod expectations; otherwise it should stay open to review.", "This may not be the strongest option, but it deserves protection if it is the right strength for the intended table.", "I would protect this if the pilot chose it to preserve table fit, identity, or social expectations.", "Review this before cutting because power-level fit depends heavily on the user's actual pod."),
    ("Interaction Controller", "I would protect this through the interaction lens when it answers the problems this deck actually expects to face or protects the plan at the right point in the game.", "I would protect this as core interaction when it prevents the deck from losing to problems it realistically needs to answer.", "I would protect this when its answer, protection, wipe, graveyard hate, or flexible interaction role is relevant to the intended table; otherwise review its slot pressure.", "This may look narrow, but it deserves protection if it answers the specific problems the deck expects to face.", "I would protect this if the pilot's table or meta makes this answer important.", "Review this before cutting because interaction value depends on the actual threats the deck needs to answer."),
]

PROTECTED_LANGUAGE_DEFINITIONS = tuple(_definition(*row) for row in _PROTECTED_ROWS)
PROTECTED_LANGUAGE_REGISTRY: Dict[str, ProtectedLanguageDefinition] = {
    definition.lens: definition for definition in PROTECTED_LANGUAGE_DEFINITIONS
}


def get_protected_language_definition(lens: str) -> ProtectedLanguageDefinition:
    canonical = get_lens_definition(lens).name
    try:
        return PROTECTED_LANGUAGE_REGISTRY[canonical]
    except KeyError as exc:
        raise ValueError(f"No protected-card language definition is registered for {lens!r}.") from exc


def get_protected_card_language(lens: str, language_type: str = "standard") -> str:
    return get_protected_language_definition(lens).get(language_type)


def get_protected_card_language_from_profile(profile: PhilosophyProfile, language_type: str = "standard") -> str:
    return get_protected_card_language(profile.selected_lens, language_type)


def get_protected_card_language_from_runtime_config(config: Optional[Mapping[str, Any]], language_type: str = "standard") -> str:
    context = context_from_runtime_config(config)
    return get_protected_card_language(context.profile.selected_lens, language_type)


def format_protected_card_note(lens: str, card_name: Optional[str] = None, *, reason: Optional[str] = None, language_type: str = "standard") -> str:
    base = get_protected_card_language(lens, language_type)
    prefix = f"**{card_name}:** " if card_name else ""
    suffix = f" {str(reason).strip()}" if reason else ""
    return f"{prefix}{base}{suffix}".strip()


def format_protected_card_note_from_profile(profile: PhilosophyProfile, card_name: Optional[str] = None, *, reason: Optional[str] = None, language_type: str = "standard") -> str:
    return format_protected_card_note(profile.selected_lens, card_name, reason=reason, language_type=language_type)


def format_protected_card_note_from_runtime_config(config: Optional[Mapping[str, Any]], card_name: Optional[str] = None, *, reason: Optional[str] = None, language_type: str = "standard") -> str:
    context = context_from_runtime_config(config)
    return format_protected_card_note(context.profile.selected_lens, card_name, reason=reason, language_type=language_type)


def protected_language_registry_as_dict() -> Dict[str, Dict[str, str]]:
    return {definition.lens: definition.to_dict() for definition in PROTECTED_LANGUAGE_DEFINITIONS}


def validate_protected_language_registry_alignment() -> bool:
    from .philosophy_registry import PHILOSOPHY_LENS_DEFINITIONS
    return tuple(d.name for d in PHILOSOPHY_LENS_DEFINITIONS) == tuple(d.lens for d in PROTECTED_LANGUAGE_DEFINITIONS)
