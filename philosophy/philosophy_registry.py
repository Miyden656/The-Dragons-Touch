"""Canonical philosophy lens registry for The Dragon's Touch.

Version: v1.1.2

This module defines implementation-safe metadata for the supported philosophy
lenses. It intentionally does not change deck analysis, cut logic, UI behavior,
prompt generation, or report rendering.

The registry answers questions such as:
- What is the canonical name for this lens?
- Is this lens Balanced / Unknown, a Big 3 philosophy, or a subtype?
- What parent philosophy does it belong to?
- What primary question should later report/prompt code use?
- What guide role should later persona code map toward?

Important boundary:
The selected philosophy/subtype is the rules object. The persona name is a
presentation detail handled by later persona registry work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Tuple

from .philosophy_profile import (
    BALANCED_UNKNOWN,
    BIG_THREE_PHILOSOPHIES,
    JOHNNY_JENNY_SUBTYPES,
    PHILOSOPHY_SUBTYPES,
    SPIKE_SUBTYPES,
    TIMMY_TAMMY_SUBTYPES,
    normalize_lens,
    resolve_parent_philosophy,
)

DEPTH_BALANCED = "balanced"
DEPTH_BIG_THREE = "big_three"
DEPTH_SUBTYPE = "subtype"

VALID_DEPTHS = (
    DEPTH_BALANCED,
    DEPTH_BIG_THREE,
    DEPTH_SUBTYPE,
)


@dataclass(frozen=True)
class PhilosophyLensDefinition:
    """Canonical metadata for one philosophy lens.

    This is intentionally small and stable. Later patches may add scoring or
    report text elsewhere, but this registry should remain the safe lookup
    layer for identity, parent philosophy, primary question, and guide role.
    """

    name: str
    parent_philosophy: str
    depth: str
    guide_role: str
    primary_question: str
    short_description: str

    @property
    def is_balanced(self) -> bool:
        return self.depth == DEPTH_BALANCED

    @property
    def is_big_three(self) -> bool:
        return self.depth == DEPTH_BIG_THREE

    @property
    def is_subtype(self) -> bool:
        return self.depth == DEPTH_SUBTYPE

    def to_dict(self) -> Dict[str, str]:
        """Serialize the lens definition to a plain dictionary."""
        return {
            "name": self.name,
            "parent_philosophy": self.parent_philosophy,
            "depth": self.depth,
            "guide_role": self.guide_role,
            "primary_question": self.primary_question,
            "short_description": self.short_description,
        }


# Ordered by the intended UI/report presentation order.
PHILOSOPHY_LENS_DEFINITIONS: Tuple[PhilosophyLensDefinition, ...] = (
    PhilosophyLensDefinition(
        name=BALANCED_UNKNOWN,
        parent_philosophy=BALANCED_UNKNOWN,
        depth=DEPTH_BALANCED,
        guide_role="Trail Guide",
        primary_question="What path does this deck naturally want to follow?",
        short_description="Balanced exploratory review when no specific philosophy is selected.",
    ),
    PhilosophyLensDefinition(
        name="Timmy / Tammy",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_BIG_THREE,
        guide_role="Heart Guide",
        primary_question="What kind of memorable game is this deck trying to create?",
        short_description="Experience-focused review that protects joy, spectacle, theme, and table stories.",
    ),
    PhilosophyLensDefinition(
        name="Johnny / Jenny",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_BIG_THREE,
        guide_role="Inventor Guide",
        primary_question="What idea is this deck trying to prove?",
        short_description="Idea-focused review that protects engines, experiments, interactions, and hidden synergy.",
    ),
    PhilosophyLensDefinition(
        name="Spike",
        parent_philosophy="Spike",
        depth=DEPTH_BIG_THREE,
        guide_role="Performance Guide",
        primary_question="What is preventing this deck from performing better at its intended table?",
        short_description="Performance-focused review that improves consistency, efficiency, interaction, and table fit.",
    ),
    PhilosophyLensDefinition(
        name="Big Moment",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_SUBTYPE,
        guide_role="Big Moment Mentor",
        primary_question="What is the unforgettable play this deck wants to create?",
        short_description="Protects and supports one memorable payoff, explosive turn, or table-shaking moment.",
    ),
    PhilosophyLensDefinition(
        name="Big Creature / Stompy",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_SUBTYPE,
        guide_role="Stompy Mentor",
        primary_question="How does this deck turn huge creatures into overwhelming battlefield pressure?",
        short_description="Helps large creatures become real combat pressure through ramp, evasion, protection, and payoffs.",
    ),
    PhilosophyLensDefinition(
        name="Theme / Vibe",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_SUBTYPE,
        guide_role="Theme Mentor",
        primary_question="Does this card make the deck feel more like itself?",
        short_description="Preserves story, aesthetic, typal identity, joke, or emotional concept while keeping the deck functional.",
    ),
    PhilosophyLensDefinition(
        name="Pet Card",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_SUBTYPE,
        guide_role="Pet Card Mentor",
        primary_question="How can this deck make room for the cards that matter personally?",
        short_description="Protects declared personally meaningful cards while naming their deck-building cost honestly.",
    ),
    PhilosophyLensDefinition(
        name="Let Me Do My Thing",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_SUBTYPE,
        guide_role="Experience Mentor",
        primary_question="What helps this deck actually do the thing it was built to do?",
        short_description="Focuses on practical support that lets the deck reach its intended experience more often.",
    ),
    PhilosophyLensDefinition(
        name="Battlecruiser",
        parent_philosophy="Timmy / Tammy",
        depth=DEPTH_SUBTYPE,
        guide_role="Battlecruiser Mentor",
        primary_question="How does this deck create a big, dramatic, fully developed Commander game?",
        short_description="Supports slower, larger Commander games with scale, resilience, recovery, and fair finishers.",
    ),
    PhilosophyLensDefinition(
        name="Engine Builder",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_SUBTYPE,
        guide_role="Engine Mentor",
        primary_question="What keeps this deck's machine turning?",
        short_description="Protects fuel, outlets, converters, payoffs, recursion, and repeatable resource flow.",
    ),
    PhilosophyLensDefinition(
        name="Commander Exploiter",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_SUBTYPE,
        guide_role="Commander Mentor",
        primary_question="What can this commander do that other commanders cannot?",
        short_description="Pushes the commander's exact text, trigger, activated ability, restriction, or unusual angle.",
    ),
    PhilosophyLensDefinition(
        name="Weird Card Rescuer",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_SUBTYPE,
        guide_role="Weird Card Mentor",
        primary_question="Can this strange card become meaningful in this shell?",
        short_description="Protects declared unusual-card experiments when the shell actually supports them.",
    ),
    PhilosophyLensDefinition(
        name="Theme Mechanic Inventor",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_SUBTYPE,
        guide_role="Hybrid Theme Mentor",
        primary_question="How do these mechanics overlap into one coherent deck?",
        short_description="Finds bridge cards and overlap between mechanics, themes, or archetypes that do not normally combine.",
    ),
    PhilosophyLensDefinition(
        name="Self-Imposed Constraint Builder",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_SUBTYPE,
        guide_role="Constraint Mentor",
        primary_question="What is the best version of this deck inside the chosen rule?",
        short_description="Improves a deck while respecting budget, card-pool, flavor, or personal deck-building restrictions.",
    ),
    PhilosophyLensDefinition(
        name="Combo Builder",
        parent_philosophy="Johnny / Jenny",
        depth=DEPTH_SUBTYPE,
        guide_role="Combo Mentor",
        primary_question="What role does this card play in the combo line?",
        short_description="Protects defined combo pieces, support, protection, redundancy, and win outlets within user tolerance.",
    ),
    PhilosophyLensDefinition(
        name="Consistency Maximizer",
        parent_philosophy="Spike",
        depth=DEPTH_SUBTYPE,
        guide_role="Consistency Mentor",
        primary_question="How often does this deck actually do what it is supposed to do?",
        short_description="Reduces dead draws, awkward hands, unsupported packages, and high-variance choices.",
    ),
    PhilosophyLensDefinition(
        name="Efficiency Optimizer",
        parent_philosophy="Spike",
        depth=DEPTH_SUBTYPE,
        guide_role="Efficiency Mentor",
        primary_question="Is this card worth its slot compared to the alternatives?",
        short_description="Pressures replaceable slots, overcosted effects, narrow cards, and low-impact choices.",
    ),
    PhilosophyLensDefinition(
        name="Curve and Mana Discipline",
        parent_philosophy="Spike",
        depth=DEPTH_SUBTYPE,
        guide_role="Mana Mentor",
        primary_question="Can this deck cast its cards on time and use its mana well?",
        short_description="Focuses on land count, fixing, ramp, curve, sequencing, and early-game structure.",
    ),
    PhilosophyLensDefinition(
        name="Competitive Closer",
        parent_philosophy="Spike",
        depth=DEPTH_SUBTYPE,
        guide_role="Closing Mentor",
        primary_question="How does this deck actually end the game?",
        short_description="Helps the deck convert advantage into a decisive win instead of generating value forever.",
    ),
    PhilosophyLensDefinition(
        name="Power-Level Calibrator",
        parent_philosophy="Spike",
        depth=DEPTH_SUBTYPE,
        guide_role="Table-Fit Mentor",
        primary_question="Is this deck the correct strength for where it is actually played?",
        short_description="Tunes the deck to the intended table without making it too weak, too fast, or socially mismatched.",
    ),
    PhilosophyLensDefinition(
        name="Interaction Controller",
        parent_philosophy="Spike",
        depth=DEPTH_SUBTYPE,
        guide_role="Interaction Mentor",
        primary_question="What can this deck currently not answer?",
        short_description="Improves answers, protection, resilience, and prevention against common failure points.",
    ),
)

PHILOSOPHY_REGISTRY: Dict[str, PhilosophyLensDefinition] = {
    definition.name: definition for definition in PHILOSOPHY_LENS_DEFINITIONS
}


def _validate_registry() -> None:
    expected_names = (
        BALANCED_UNKNOWN,
        *BIG_THREE_PHILOSOPHIES,
        *PHILOSOPHY_SUBTYPES,
    )
    registry_names = tuple(PHILOSOPHY_REGISTRY)

    missing = set(expected_names) - set(registry_names)
    extra = set(registry_names) - set(expected_names)
    if missing or extra:
        raise RuntimeError(
            "Philosophy registry does not match profile model lenses. "
            f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
        )

    for definition in PHILOSOPHY_LENS_DEFINITIONS:
        if definition.depth not in VALID_DEPTHS:
            raise RuntimeError(f"Invalid philosophy depth for {definition.name!r}: {definition.depth!r}")
        resolved_parent = resolve_parent_philosophy(definition.name)
        if definition.parent_philosophy != resolved_parent:
            raise RuntimeError(
                f"Parent mismatch for {definition.name!r}: registry={definition.parent_philosophy!r}, "
                f"profile_model={resolved_parent!r}"
            )
        if not definition.primary_question.strip():
            raise RuntimeError(f"Missing primary question for {definition.name!r}")
        if not definition.guide_role.strip():
            raise RuntimeError(f"Missing guide role for {definition.name!r}")


_validate_registry()


def get_lens_definition(value: str) -> PhilosophyLensDefinition:
    """Return the canonical definition for a philosophy lens or alias."""
    canonical = normalize_lens(value)
    return PHILOSOPHY_REGISTRY[canonical]


def get_lens_definition_dict(value: str) -> Dict[str, str]:
    """Return a serializable definition dictionary for a lens or alias."""
    return get_lens_definition(value).to_dict()


def get_all_lens_definitions() -> Tuple[PhilosophyLensDefinition, ...]:
    """Return every supported lens definition in canonical order."""
    return PHILOSOPHY_LENS_DEFINITIONS


def get_supported_lens_names() -> Tuple[str, ...]:
    """Return every supported lens name in canonical order."""
    return tuple(definition.name for definition in PHILOSOPHY_LENS_DEFINITIONS)


def is_supported_lens(value: str) -> bool:
    """Return True if value resolves to a supported philosophy lens."""
    try:
        get_lens_definition(value)
    except (KeyError, ValueError):
        return False
    return True


def is_balanced_lens(value: str) -> bool:
    """Return True if value resolves to Balanced / Unknown."""
    return get_lens_definition(value).is_balanced


def is_big_three_lens(value: str) -> bool:
    """Return True if value resolves to a broad Big 3 philosophy."""
    return get_lens_definition(value).is_big_three


def is_subtype_lens(value: str) -> bool:
    """Return True if value resolves to one of the 18 subtype lenses."""
    return get_lens_definition(value).is_subtype


def get_parent_for_lens(value: str) -> str:
    """Return the parent philosophy for a lens or alias."""
    return get_lens_definition(value).parent_philosophy


def get_primary_question(value: str) -> str:
    """Return the primary question for a lens or alias."""
    return get_lens_definition(value).primary_question


def get_guide_role(value: str) -> str:
    """Return the guide role label for a lens or alias."""
    return get_lens_definition(value).guide_role


def list_lenses_by_parent(parent_philosophy: str, *, include_parent: bool = True) -> Tuple[PhilosophyLensDefinition, ...]:
    """Return lenses under a parent philosophy in canonical order.

    Args:
        parent_philosophy: Timmy / Tammy, Johnny / Jenny, Spike, or Balanced / Unknown.
        include_parent: When True, include the broad parent lens itself for Big 3 philosophies.
    """
    parent = normalize_lens(parent_philosophy)
    if parent == BALANCED_UNKNOWN:
        return (PHILOSOPHY_REGISTRY[BALANCED_UNKNOWN],)
    if parent not in BIG_THREE_PHILOSOPHIES:
        parent = resolve_parent_philosophy(parent)

    result: List[PhilosophyLensDefinition] = []
    for definition in PHILOSOPHY_LENS_DEFINITIONS:
        if definition.parent_philosophy != parent:
            continue
        if not include_parent and definition.name == parent:
            continue
        result.append(definition)
    return tuple(result)


def list_subtypes_by_parent(parent_philosophy: str) -> Tuple[PhilosophyLensDefinition, ...]:
    """Return only subtype lenses for a parent philosophy."""
    return tuple(
        definition
        for definition in list_lenses_by_parent(parent_philosophy, include_parent=False)
        if definition.is_subtype
    )


def get_subtype_names_by_parent(parent_philosophy: str) -> Tuple[str, ...]:
    """Return only subtype names for a parent philosophy."""
    return tuple(definition.name for definition in list_subtypes_by_parent(parent_philosophy))


def registry_as_dict() -> Dict[str, Dict[str, str]]:
    """Return the full registry as serializable dictionaries keyed by lens name."""
    return {definition.name: definition.to_dict() for definition in PHILOSOPHY_LENS_DEFINITIONS}
