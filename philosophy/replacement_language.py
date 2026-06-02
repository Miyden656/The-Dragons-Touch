"""Philosophy-aware replacement-direction language helpers for The Dragon's Touch.

Version: v1.1.8

This module provides reusable language for explaining what kind of replacement
a deck should look for through the selected philosophy lens.

Important boundary:
- This module does not recommend exact cards.
- This module does not score replacement candidates.
- This module does not change deck analysis behavior.
- This module does not wire itself into existing replacement reports.
- This module only formats replacement-direction explanation text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .philosophy_profile import PhilosophyProfile
from .philosophy_registry import get_lens_definition
from .runtime_config_mapping import context_from_runtime_config


REPLACEMENT_LANGUAGE_TYPES = (
    "standard",
    "ramp",
    "draw",
    "interaction",
    "protection",
    "finisher",
    "synergy",
    "curve",
)


@dataclass(frozen=True)
class ReplacementLanguageDefinition:
    """Replacement-direction language bundle for one philosophy lens."""

    lens: str
    standard: str
    ramp: str
    draw: str
    interaction: str
    protection: str
    finisher: str
    synergy: str
    curve: str

    def get(self, language_type: str = "standard") -> str:
        return getattr(self, normalize_replacement_language_type(language_type))

    def to_dict(self) -> Dict[str, str]:
        return {
            "lens": self.lens,
            "standard": self.standard,
            "ramp": self.ramp,
            "draw": self.draw,
            "interaction": self.interaction,
            "protection": self.protection,
            "finisher": self.finisher,
            "synergy": self.synergy,
            "curve": self.curve,
        }


def normalize_replacement_language_type(language_type: Optional[str]) -> str:
    text = str(language_type or "standard").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "": "standard",
        "normal": "standard",
        "default": "standard",
        "replacement": "standard",
        "standard": "standard",
        "ramp": "ramp",
        "mana": "ramp",
        "mana_ramp": "ramp",
        "fixing": "ramp",
        "draw": "draw",
        "card_draw": "draw",
        "card_advantage": "draw",
        "selection": "draw",
        "interaction": "interaction",
        "removal": "interaction",
        "answer": "interaction",
        "answers": "interaction",
        "protection": "protection",
        "protect": "protection",
        "resilience": "protection",
        "finisher": "finisher",
        "closer": "finisher",
        "wincon": "finisher",
        "win_condition": "finisher",
        "synergy": "synergy",
        "engine": "synergy",
        "commander_synergy": "synergy",
        "theme": "synergy",
        "curve": "curve",
        "mana_curve": "curve",
        "lower_curve": "curve",
        "efficiency": "curve",
    }
    if text not in aliases:
        raise ValueError(
            f"Unknown replacement language type: {language_type!r}. Expected one of: "
            + ", ".join(REPLACEMENT_LANGUAGE_TYPES)
        )
    return aliases[text]


def _definition(
    lens: str,
    standard: str,
    ramp: str,
    draw: str,
    interaction: str,
    protection: str,
    finisher: str,
    synergy: str,
    curve: str,
) -> ReplacementLanguageDefinition:
    canonical = get_lens_definition(lens).name
    return ReplacementLanguageDefinition(
        lens=canonical,
        standard=standard,
        ramp=ramp,
        draw=draw,
        interaction=interaction,
        protection=protection,
        finisher=finisher,
        synergy=synergy,
        curve=curve,
    )


_REPLACEMENT_ROWS = [
    (
        "Balanced / Unknown",
        "Look for a replacement that fills a clear missing role along the deck's clearest path, without assuming a stronger philosophy than the pilot has chosen.",
        "Prefer practical ramp or fixing that helps the deck execute its visible plan more reliably.",
        "Prefer card draw or selection that helps the deck find its main pieces without pushing it into a different identity.",
        "Prefer flexible interaction that answers common problems while preserving the deck's proactive plan.",
        "Prefer protection or resilience only if the deck has visible commander, engine, or payoff dependency.",
        "Prefer a finisher only if the deck appears to generate resources without a clear way to convert them into a win.",
        "Prefer synergy that reinforces the commander or primary strategy rather than creating a new unsupported package.",
        "Prefer a replacement that smooths the curve without removing cards that may be important to user intent.",
    ),
    (
        "Timmy / Tammy",
        "Look for a replacement that improves function while preserving the deck's experience, theme, payoff, or table story.",
        "Prefer ramp that helps the deck reach its exciting turns more often.",
        "Prefer draw that helps the pilot see the cards that make the deck feel memorable.",
        "Prefer interaction that keeps the game fun and protects the deck's ability to participate.",
        "Prefer protection that keeps the important payoff, theme, or favorite card from disappearing before it matters.",
        "Prefer finishers that create a satisfying table moment rather than generic efficiency alone.",
        "Prefer synergy that makes the deck feel more like itself.",
        "Prefer curve improvements that help the deck reach its fun turns without cutting the joy out of the list.",
    ),
    (
        "Johnny / Jenny",
        "Look for a replacement that strengthens the deck's idea, engine, interaction, constraint, or experiment.",
        "Prefer ramp that feeds the engine or enables the key interaction rather than generic acceleration alone.",
        "Prefer draw or selection that finds the build-around pieces and keeps the machine moving.",
        "Prefer interaction that protects the idea or doubles as a combo, engine, or constraint piece.",
        "Prefer protection that keeps the build-around, engine, or unusual interaction online.",
        "Prefer finishers that emerge naturally from the engine or prove the deck's central idea.",
        "Prefer synergy that connects packages, converts resources, or gives the strange pieces a real job.",
        "Prefer curve improvements that make the engine assemble earlier and with fewer dead pieces.",
    ),
    (
        "Spike",
        "Look for a replacement that improves consistency, efficiency, interaction, win conversion, resilience, or table fit.",
        "Prefer efficient ramp or fixing that improves opening hands and lets the deck use mana cleanly.",
        "Prefer efficient draw, selection, or role-compressed card advantage that reduces dead draws.",
        "Prefer flexible, efficient interaction that answers the threats the deck is most likely to face.",
        "Prefer protection that efficiently defends the commander, engine, or win condition without becoming narrow.",
        "Prefer finishers that convert advantage into wins at the intended power level.",
        "Prefer synergy only when it improves performance, not when it is merely cute.",
        "Prefer lower-cost, flexible replacements that improve the deck's average draw and sequencing.",
    ),
    (
        "Big Moment",
        "Look for a replacement that makes the payoff moment more likely, more protected, bigger, or more decisive.",
        "Prefer ramp that gets the deck to the payoff turn faster and with enough mana to matter.",
        "Prefer draw that finds the payoff, the setup, or the amplification piece.",
        "Prefer interaction that clears the way for the big turn or stops the deck from losing before it happens.",
        "Prefer protection that keeps the payoff, commander, or setup from being answered at the worst moment.",
        "Prefer finishers that are the big moment or make the big moment lethal.",
        "Prefer synergy that copies, doubles, scales, amplifies, or converts the payoff.",
        "Prefer curve improvements that make the setup smoother without shrinking the payoff identity.",
    ),
    (
        "Big Creature / Stompy",
        "Look for a replacement that helps big creatures become real battlefield pressure.",
        "Prefer ramp that gets major threats onto the battlefield ahead of schedule.",
        "Prefer creature-based draw or draw that rewards power, combat, or board presence.",
        "Prefer interaction that is stapled to creatures or clears blockers without diluting the threat plan.",
        "Prefer protection, haste, evasion, or trample so large creatures actually connect.",
        "Prefer finishers that turn size into lethal damage, cards, removal, or overwhelming combat.",
        "Prefer synergy that rewards power, toughness, attacking, combat damage, or creature size.",
        "Prefer curve improvements that balance early ramp with enough meaningful top-end.",
    ),
    (
        "Theme / Vibe",
        "Look for a replacement that improves the deck without erasing its story, aesthetic, tribe, joke, or emotional identity.",
        "Prefer ramp that fits the theme when possible while still functioning.",
        "Prefer draw that feels on-theme or supports the deck's identity without being dead weight.",
        "Prefer removal or answers that preserve the deck's flavor when functional options exist.",
        "Prefer protection that keeps the theme-defining cards around long enough to matter.",
        "Prefer finishers that match the deck's story or emotional payoff.",
        "Prefer synergy that is theme with function, not flavor alone.",
        "Prefer curve improvements that keep the deck playable without turning it into generic good-stuff.",
    ),
    (
        "Pet Card",
        "Look for a replacement that reduces the performance cost of keeping a protected joy slot — the cards the pilot personally cares about.",
        "Prefer ramp that helps the pet card or its package become castable and relevant.",
        "Prefer draw or selection that helps the pilot find the protected card without overbuilding around it.",
        "Prefer interaction that buys time for the pet card plan without consuming too many slots.",
        "Prefer protection that keeps the declared pet card from being removed before the pilot gets to experience it.",
        "Prefer finishers that work with the pet card if that is part of the pilot's goal.",
        "Prefer synergy that supports the pet card while still contributing to the main plan.",
        "Prefer curve improvements around the pet card rather than cutting the pet card by default.",
    ),
    (
        "Let Me Do My Thing",
        "Look for a replacement that helps the deck actually do the thing it was built to do.",
        "Prefer ramp that gets the deck to its intended experience more reliably.",
        "Prefer draw that keeps the deck from running out before it reaches the fun part.",
        "Prefer interaction that prevents opponents from shutting the deck out of the game.",
        "Prefer protection that keeps the commander, engine, or main payoff online.",
        "Prefer finishers only if they help convert the deck's intended experience into an actual win.",
        "Prefer synergy that adds redundancy or support for the main experience.",
        "Prefer curve improvements that make the deck start doing its thing sooner.",
    ),
    (
        "Battlecruiser",
        "Look for a replacement that supports a large, dramatic, fair Commander game without making the deck nonfunctional.",
        "Prefer ramp that supports bigger late-game turns without jumping to the wrong power level.",
        "Prefer late-game draw or scalable advantage that keeps the big game going.",
        "Prefer interaction that prevents early losses or oppressive endings while preserving battlecruiser texture.",
        "Prefer protection and recovery tools that let big payoffs matter after board wipes.",
        "Prefer fair finishers that feel large, dramatic, and satisfying.",
        "Prefer synergy that makes big mana, large spells, or huge boards matter.",
        "Prefer curve improvements that add early setup without removing the deck's late-game identity.",
    ),
    (
        "Engine Builder",
        "Look for a replacement that feeds, protects, connects, converts, repeats, or pays off the engine.",
        "Prefer ramp that is also fuel, a converter, or an engine piece when possible.",
        "Prefer repeatable draw or card flow that keeps the machine turning.",
        "Prefer interaction that doubles as an engine piece or protects the engine from disruption.",
        "Prefer recursion, redundancy, or protection for the engine's most fragile pieces.",
        "Prefer finishers that naturally emerge from the engine's resource loop.",
        "Prefer synergy that connects fuel, outlet, converter, payoff, and recursion pieces.",
        "Prefer curve improvements that lower the cost of assembling the machine.",
    ),
    (
        "Commander Exploiter",
        "Look for a replacement that interacts with the commander's specific text rather than generic color identity.",
        "Prefer ramp that helps cast, recast, or activate the commander on time.",
        "Prefer draw that is triggered, enabled, or improved by what the commander already does.",
        "Prefer interaction that protects the commander or converts the commander's unique resource into control.",
        "Prefer protection, haste, untap, blink, copy, reset, or recursion if those effects exploit the commander.",
        "Prefer finishers that convert the commander's unique output into a win.",
        "Prefer synergy that multiplies the commander's trigger, ability, restriction, or unusual angle.",
        "Prefer curve improvements that keep the commander central rather than making the deck function without caring about it.",
    ),
    (
        "Weird Card Rescuer",
        "Look for a replacement that helps the strange card become meaningful rather than simply replacing it with a normal staple.",
        "Prefer ramp only if it helps cast or enable the rescued card's unusual line.",
        "Prefer draw or selection that finds the weird card and the support pieces together.",
        "Prefer interaction that protects the experiment or buys time to prove it works.",
        "Prefer protection or recursion that lets the rescued card survive long enough to matter.",
        "Prefer finishers that use the rescued card's strange effect instead of bypassing it.",
        "Prefer synergy that gives the weird card a real job in the deck.",
        "Prefer curve improvements that support the experiment without making the shell too clunky.",
    ),
    (
        "Theme Mechanic Inventor",
        "Look for a replacement that bridges the deck's themes or mechanics instead of supporting only one isolated half.",
        "Prefer ramp that supports both sides of the hybrid concept when possible.",
        "Prefer draw that rewards the overlap between the deck's themes.",
        "Prefer interaction that also counts toward one of the deck's mechanical packages.",
        "Prefer protection that keeps the bridge cards or hybrid payoff online.",
        "Prefer finishers that use the combined theme rather than only one package.",
        "Prefer synergy that makes the deck feel like one coherent invention.",
        "Prefer curve improvements that reduce package collision and make the hybrid plan smoother.",
    ),
    (
        "Self-Imposed Constraint Builder",
        "Look for a replacement that works inside the declared rule, budget, card pool, or limitation.",
        "Prefer the best legal ramp or fixing available within the constraint.",
        "Prefer draw options that respect the constraint while keeping the deck functional.",
        "Prefer interaction that satisfies the restriction and still answers real problems.",
        "Prefer protection that keeps scarce constraint-compliant engines or payoffs alive.",
        "Prefer finishers that honor the premise instead of breaking the deck's chosen rule.",
        "Prefer synergy that is correct inside the limited pool, even if it is not best-in-slot normally.",
        "Prefer curve improvements that solve structural weakness created by the constraint.",
    ),
    (
        "Combo Builder",
        "Look for a replacement that clarifies, protects, completes, or improves the combo package while respecting combo tolerance.",
        "Prefer ramp that helps assemble or execute the combo turn without being dead outside it.",
        "Prefer draw, selection, or tutors appropriate to the deck's intended power level.",
        "Prefer interaction that protects the combo turn or stops opponents from breaking the line.",
        "Prefer protection or recursion for fragile combo pieces.",
        "Prefer clear win outlets or compact finishers that complete the declared line.",
        "Prefer synergy that overlaps with the main plan when the deck is not comboing.",
        "Prefer curve improvements that reduce dead combo fragments and make the line easier to assemble.",
    ),
    (
        "Consistency Maximizer",
        "Look for a replacement that raises the deck's floor so it does its intended thing more often.",
        "Prefer reliable ramp and fixing that improves opening hands.",
        "Prefer draw or selection that reduces dead draws and finds key effects.",
        "Prefer flexible interaction that avoids narrow cards and bad-from-behind situations.",
        "Prefer protection only if it reduces a real fail state.",
        "Prefer finishers that require fewer perfect conditions to work.",
        "Prefer synergy that adds redundancy rather than fragile novelty.",
        "Prefer curve improvements that reduce awkward hands and non-games.",
    ),
    (
        "Efficiency Optimizer",
        "Look for a replacement that gives better rate, flexibility, role compression, or lower opportunity cost.",
        "Prefer cheaper or more flexible ramp that fits the deck's curve.",
        "Prefer efficient card advantage that produces value without excessive setup.",
        "Prefer low-cost, flexible interaction over narrow or overcosted answers.",
        "Prefer protection that is cheap, flexible, or attached to another useful role.",
        "Prefer finishers that close efficiently without requiring too many extra pieces.",
        "Prefer synergy only if the rate or role compression justifies the slot.",
        "Prefer lower-cost replacements that improve average draw quality.",
    ),
    (
        "Curve and Mana Discipline",
        "Look for a replacement that improves castability — mana, curve, color requirements, or sequencing.",
        "Prefer ramp and fixing that matches the deck's actual curve and color needs.",
        "Prefer draw that fits into turns where the deck can realistically spend mana.",
        "Prefer interaction that is cheap enough to hold up while advancing the plan.",
        "Prefer protection that fits the deck's sequencing and does not clog the same mana slot.",
        "Prefer finishers that the mana base can realistically support.",
        "Prefer synergy that does not add unnecessary color or mana-value pressure.",
        "Prefer replacements that lower crowded mana values or improve early-turn plays.",
    ),
    (
        "Competitive Closer",
        "Look for a replacement that gives the deck a finish line — converting advantage into a decisive win instead of another lap.",
        "Prefer ramp only if it accelerates toward a real closing turn.",
        "Prefer draw that finds payoff pieces instead of adding endless setup.",
        "Prefer interaction that clears the way for the win or protects the closing line.",
        "Prefer protection that defends the finisher, combo turn, or lethal combat step.",
        "Prefer finishers that turn the deck's main resource into lethal pressure or inevitability.",
        "Prefer synergy that converts value into victory rather than more value.",
        "Prefer curve improvements that make the closing plan arrive before the deck stalls out.",
    ),
    (
        "Power-Level Calibrator",
        "Look for a replacement that lands at the correct strength for the intended table, bracket, budget, and combo tolerance — not the maximum.",
        "Prefer ramp that improves the deck without overshooting the pod's speed.",
        "Prefer draw that matches the table's expected power and resource pace.",
        "Prefer interaction that is appropriate for the threats the pod actually presents.",
        "Prefer protection that keeps the deck functional without creating a play experience mismatch.",
        "Prefer finishers that are strong enough to close but not stronger than the table wants.",
        "Prefer synergy and consistency over raw power when that better fits the table.",
        "Prefer curve improvements that tune the deck to the table rather than maximizing in a vacuum.",
    ),
    (
        "Interaction Controller",
        "Look for a replacement that closes a coverage gap the deck currently cannot answer, or protects the plan from common failure points.",
        "Prefer ramp only if the deck already has enough answers or the ramp helps hold up interaction later.",
        "Prefer draw that finds answers while still supporting the proactive plan.",
        "Prefer flexible removal, protection, wipes, graveyard hate, or stack interaction based on the deck's weak points.",
        "Prefer protection that defends the commander, engine, or payoff from common disruption.",
        "Prefer finishers only after the deck has enough ways to survive and interact.",
        "Prefer synergy-based interaction that answers threats without diluting the deck's plan.",
        "Prefer curve improvements that let the deck interact earlier and still advance its plan.",
    ),
]

REPLACEMENT_LANGUAGE_DEFINITIONS = tuple(_definition(*row) for row in _REPLACEMENT_ROWS)
REPLACEMENT_LANGUAGE_REGISTRY: Dict[str, ReplacementLanguageDefinition] = {
    definition.lens: definition for definition in REPLACEMENT_LANGUAGE_DEFINITIONS
}


def get_replacement_language_definition(lens: str) -> ReplacementLanguageDefinition:
    canonical = get_lens_definition(lens).name
    try:
        return REPLACEMENT_LANGUAGE_REGISTRY[canonical]
    except KeyError as exc:
        raise ValueError(f"No replacement-direction language definition is registered for {lens!r}.") from exc


def get_replacement_direction_language(lens: str, language_type: str = "standard") -> str:
    return get_replacement_language_definition(lens).get(language_type)


def get_replacement_direction_language_from_profile(profile: PhilosophyProfile, language_type: str = "standard") -> str:
    return get_replacement_direction_language(profile.selected_lens, language_type)


def get_replacement_direction_language_from_runtime_config(config: Optional[Mapping[str, Any]], language_type: str = "standard") -> str:
    context = context_from_runtime_config(config)
    return get_replacement_direction_language(context.profile.selected_lens, language_type)


def format_replacement_direction_note(lens: str, role: Optional[str] = None, *, reason: Optional[str] = None, language_type: str = "standard") -> str:
    base = get_replacement_direction_language(lens, language_type)
    prefix = f"**Replacement Direction — {role}:** " if role else "**Replacement Direction:** "
    suffix = f" {str(reason).strip()}" if reason else ""
    return f"{prefix}{base}{suffix}".strip()


def format_replacement_direction_note_from_profile(profile: PhilosophyProfile, role: Optional[str] = None, *, reason: Optional[str] = None, language_type: str = "standard") -> str:
    return format_replacement_direction_note(profile.selected_lens, role, reason=reason, language_type=language_type)


def format_replacement_direction_note_from_runtime_config(config: Optional[Mapping[str, Any]], role: Optional[str] = None, *, reason: Optional[str] = None, language_type: str = "standard") -> str:
    context = context_from_runtime_config(config)
    return format_replacement_direction_note(context.profile.selected_lens, role, reason=reason, language_type=language_type)


def replacement_language_registry_as_dict() -> Dict[str, Dict[str, str]]:
    return {definition.lens: definition.to_dict() for definition in REPLACEMENT_LANGUAGE_DEFINITIONS}


def validate_replacement_language_registry_alignment() -> bool:
    from .philosophy_registry import PHILOSOPHY_LENS_DEFINITIONS
    return tuple(d.name for d in PHILOSOPHY_LENS_DEFINITIONS) == tuple(d.lens for d in REPLACEMENT_LANGUAGE_DEFINITIONS)
