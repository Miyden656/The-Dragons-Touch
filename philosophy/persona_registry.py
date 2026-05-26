"""Canonical persona guide registry for The Dragon's Touch.

Version: v1.1.3

This module defines implementation-safe metadata for the user-facing guide
presentation layer. It intentionally does not change deck analysis, cut logic,
UI behavior, prompt generation, or report rendering.

Important boundary:
The selected philosophy/subtype is the rules object. The persona name is only a
presentation detail. For example, Big Moment is the lens; Michael/Michelle is
the resolved guide name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple

from .philosophy_profile import GUIDE_PRESENTATIONS, normalize_lens
from .philosophy_registry import (
    PHILOSOPHY_LENS_DEFINITIONS,
    get_lens_definition,
)


@dataclass(frozen=True)
class PersonaGuideDefinition:
    """User-facing guide metadata for one philosophy lens."""

    lens: str
    parent_philosophy: str
    guide_role: str
    primary_question: str
    masculine_name: Optional[str] = None
    feminine_name: Optional[str] = None
    neutral_name: Optional[str] = None
    no_named_label: Optional[str] = None
    short_guidance: str = ""

    @property
    def has_named_guide(self) -> bool:
        return bool(self.masculine_name or self.feminine_name or self.neutral_name)

    @property
    def is_paired(self) -> bool:
        return bool(self.masculine_name and self.feminine_name and self.masculine_name != self.feminine_name)

    def resolve_name(self, guide_presentation: str = "either") -> Optional[str]:
        """Resolve the visible guide name for a guide presentation preference.

        Returns None when named guides are disabled.
        """
        presentation = _normalize_guide_presentation(guide_presentation)
        if presentation == "no_named_guide":
            return None

        if presentation == "masculine":
            return self.masculine_name or self.neutral_name or self.feminine_name

        if presentation == "feminine":
            return self.feminine_name or self.neutral_name or self.masculine_name

        # "either" is deterministic here to keep tests and reports stable.
        if self.is_paired:
            return f"{self.masculine_name} / {self.feminine_name}"
        return self.neutral_name or self.masculine_name or self.feminine_name

    def display_label(self, guide_presentation: str = "either") -> str:
        """Return a compact display label for report headers."""
        name = self.resolve_name(guide_presentation)
        if name:
            return f"{name} — The {self.guide_role}"
        return self.no_named_label or f"{self.lens} lens"

    def to_dict(self, guide_presentation: str = "either") -> Dict[str, Optional[str]]:
        """Serialize persona metadata to a plain dictionary."""
        guide_name = self.resolve_name(guide_presentation)
        return {
            "lens": self.lens,
            "parent_philosophy": self.parent_philosophy,
            "guide_role": self.guide_role,
            "primary_question": self.primary_question,
            "guide_presentation": _normalize_guide_presentation(guide_presentation),
            "guide_name": guide_name,
            "display_label": self.display_label(guide_presentation),
            "named_guide_enabled": bool(guide_name),
            "masculine_name": self.masculine_name,
            "feminine_name": self.feminine_name,
            "neutral_name": self.neutral_name,
            "no_named_label": self.no_named_label,
            "short_guidance": self.short_guidance,
        }


def _normalize_guide_presentation(value: Optional[str]) -> str:
    text = " ".join(str(value or "either").strip().lower().replace("-", "_").replace(" ", "_").split())
    aliases = {
        "": "either",
        "random": "either",
        "either_random": "either",
        "either": "either",
        "masc": "masculine",
        "male": "masculine",
        "masculine": "masculine",
        "fem": "feminine",
        "female": "feminine",
        "feminine": "feminine",
        "none": "no_named_guide",
        "no_name": "no_named_guide",
        "no_named": "no_named_guide",
        "no_named_guide": "no_named_guide",
        "philosophy_labels": "no_named_guide",
        "labels_only": "no_named_guide",
    }
    if text in aliases:
        return aliases[text]
    if text in GUIDE_PRESENTATIONS:
        return text
    raise ValueError(
        f"Unknown guide presentation: {value!r}. Expected one of: "
        + ", ".join(GUIDE_PRESENTATIONS)
    )


def _base(lens: str) -> Dict[str, str]:
    definition = get_lens_definition(lens)
    return {
        "lens": definition.name,
        "parent_philosophy": definition.parent_philosophy,
        "guide_role": definition.guide_role,
        "primary_question": definition.primary_question,
    }


def _guide(
    lens: str,
    *,
    masculine_name: Optional[str] = None,
    feminine_name: Optional[str] = None,
    neutral_name: Optional[str] = None,
    no_named_label: Optional[str] = None,
    short_guidance: str = "",
) -> PersonaGuideDefinition:
    return PersonaGuideDefinition(
        **_base(lens),
        masculine_name=masculine_name,
        feminine_name=feminine_name,
        neutral_name=neutral_name,
        no_named_label=no_named_label or f"{lens} lens",
        short_guidance=short_guidance,
    )


PERSONA_GUIDE_DEFINITIONS: Tuple[PersonaGuideDefinition, ...] = (
    _guide(
        "Balanced / Unknown",
        neutral_name="Rowan",
        no_named_label="Balanced / Unknown lens",
        short_guidance="Map the deck's natural direction without applying strong philosophy-specific pressure.",
    ),
    _guide(
        "Timmy / Tammy",
        masculine_name="Timmy",
        feminine_name="Tammy",
        no_named_label="Timmy / Tammy lens",
        short_guidance="Protect memorable experiences, emotional payoff, theme, spectacle, and table stories.",
    ),
    _guide(
        "Johnny / Jenny",
        masculine_name="Johnny",
        feminine_name="Jenny",
        no_named_label="Johnny / Jenny lens",
        short_guidance="Protect ideas, engines, experiments, hidden synergies, and clever interactions.",
    ),
    _guide(
        "Spike",
        neutral_name="Spike",
        no_named_label="Spike lens",
        short_guidance="Focus on consistency, efficiency, interaction, win conversion, and table fit.",
    ),
    _guide("Big Moment", masculine_name="Michael", feminine_name="Michelle", short_guidance="Make the payoff moment real, not just exciting in theory."),
    _guide("Big Creature / Stompy", masculine_name="Alexander", feminine_name="Alexandria", short_guidance="Make size matter through pressure, evasion, protection, and payoff support."),
    _guide("Theme / Vibe", masculine_name="Benjamin", feminine_name="Bethany", short_guidance="Make the deck feel more like itself while keeping it functional."),
    _guide("Pet Card", masculine_name="Milo", feminine_name="Mia", short_guidance="Make room for what matters personally, honestly."),
    _guide("Let Me Do My Thing", masculine_name="William", feminine_name="Willow", short_guidance="Help the deck actually do the thing it was built to do."),
    _guide("Battlecruiser", masculine_name="Aaron", feminine_name="Ariana", short_guidance="Make the big Commander game worth building toward."),
    _guide("Engine Builder", masculine_name="Brad", feminine_name="Bria", short_guidance="Make sure every gear turns another gear."),
    _guide("Commander Exploiter", masculine_name="Kyle", feminine_name="Katie", short_guidance="Push the commander's unique text instead of generic color-goodstuff."),
    _guide("Weird Card Rescuer", masculine_name="Elund", feminine_name="Emily", short_guidance="Test whether the strange card can become meaningful in this shell."),
    _guide("Theme Mechanic Inventor", masculine_name="Brandon", feminine_name="Brenda", short_guidance="Find where unusual mechanics overlap into one coherent deck."),
    _guide("Self-Imposed Constraint Builder", masculine_name="Clark", feminine_name="Clarissa", short_guidance="Build the best deck inside the chosen rule."),
    _guide("Combo Builder", masculine_name="Jasper", feminine_name="Jennifer", short_guidance="Clarify each card's role in the combo line."),
    _guide("Consistency Maximizer", neutral_name="Avery", short_guidance="Help the deck do its intended thing more often."),
    _guide("Efficiency Optimizer", neutral_name="Jordan", short_guidance="Make sure each card justifies its slot."),
    _guide("Curve and Mana Discipline", neutral_name="River", short_guidance="Help the deck cast its cards on time and use mana well."),
    _guide("Competitive Closer", neutral_name="Charlie", short_guidance="Turn advantage into a decisive win."),
    _guide("Power-Level Calibrator", neutral_name="Kai", short_guidance="Tune the deck to the correct strength for the intended table."),
    _guide("Interaction Controller", neutral_name="Riley", short_guidance="Help the deck answer threats and protect its plan."),
)

PERSONA_REGISTRY: Dict[str, PersonaGuideDefinition] = {
    definition.lens: definition for definition in PERSONA_GUIDE_DEFINITIONS
}


def get_persona_definition(lens: str) -> PersonaGuideDefinition:
    """Return persona metadata for a philosophy lens."""
    canonical = normalize_lens(lens)
    try:
        return PERSONA_REGISTRY[canonical]
    except KeyError as exc:
        raise ValueError(f"No persona guide definition is registered for {lens!r}.") from exc


def is_persona_supported(lens: str) -> bool:
    """Return True if the lens has persona guide metadata."""
    try:
        get_persona_definition(lens)
    except ValueError:
        return False
    return True


def resolve_guide_name(lens: str, guide_presentation: str = "either") -> Optional[str]:
    """Resolve only the visible guide name for a lens/presentation preference."""
    return get_persona_definition(lens).resolve_name(guide_presentation)


def get_guide_display_label(lens: str, guide_presentation: str = "either") -> str:
    """Return a compact guide label suitable for a report header."""
    return get_persona_definition(lens).display_label(guide_presentation)


def get_persona_report_context(lens: str, guide_presentation: str = "either") -> Dict[str, Optional[str]]:
    """Return the metadata needed by later report generation code."""
    return get_persona_definition(lens).to_dict(guide_presentation)


def get_supported_persona_lenses() -> Tuple[str, ...]:
    """Return supported persona lens names in registry order."""
    return tuple(definition.lens for definition in PERSONA_GUIDE_DEFINITIONS)


def persona_registry_as_dict(guide_presentation: str = "either") -> Dict[str, Dict[str, Optional[str]]]:
    """Serialize the full persona registry using one guide presentation preference."""
    return {
        definition.lens: definition.to_dict(guide_presentation)
        for definition in PERSONA_GUIDE_DEFINITIONS
    }


def validate_persona_registry_alignment() -> bool:
    """Return True when persona entries align with the philosophy registry.

    This is a lightweight guard for verifiers and future tests.
    """
    philosophy_names = tuple(definition.name for definition in PHILOSOPHY_LENS_DEFINITIONS)
    persona_names = tuple(definition.lens for definition in PERSONA_GUIDE_DEFINITIONS)
    if philosophy_names != persona_names:
        return False

    for persona in PERSONA_GUIDE_DEFINITIONS:
        lens = get_lens_definition(persona.lens)
        if persona.parent_philosophy != lens.parent_philosophy:
            return False
        if persona.guide_role != lens.guide_role:
            return False
        if persona.primary_question != lens.primary_question:
            return False

    return True
