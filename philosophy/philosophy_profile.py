"""Structured philosophy profile model for The Dragon's Touch.

Version: v1.1.1

This module intentionally defines a small, dependency-free data model for
carrying the user's philosophy choices through later v1.1 work.

Important boundary:
- This module does not change analysis behavior.
- This module does not score cards.
- This module does not apply cut pressure.
- This module does not generate reports.

It only represents the user's selected philosophy lens, guide presentation,
intensity, notes, protected cards, and declared constraints in a validated form.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

BALANCED_UNKNOWN = "Balanced / Unknown"

BIG_THREE_PHILOSOPHIES = (
    "Timmy / Tammy",
    "Johnny / Jenny",
    "Spike",
)

TIMMY_TAMMY_SUBTYPES = (
    "Big Moment",
    "Big Creature / Stompy",
    "Theme / Vibe",
    "Pet Card",
    "Let Me Do My Thing",
    "Battlecruiser",
)

JOHNNY_JENNY_SUBTYPES = (
    "Engine Builder",
    "Commander Exploiter",
    "Weird Card Rescuer",
    "Theme Mechanic Inventor",
    "Self-Imposed Constraint Builder",
    "Combo Builder",
)

SPIKE_SUBTYPES = (
    "Consistency Maximizer",
    "Efficiency Optimizer",
    "Curve and Mana Discipline",
    "Competitive Closer",
    "Power-Level Calibrator",
    "Interaction Controller",
)

PHILOSOPHY_SUBTYPES = (
    *TIMMY_TAMMY_SUBTYPES,
    *JOHNNY_JENNY_SUBTYPES,
    *SPIKE_SUBTYPES,
)

ALL_LENSES = (
    BALANCED_UNKNOWN,
    *BIG_THREE_PHILOSOPHIES,
    *PHILOSOPHY_SUBTYPES,
)

PARENT_BY_LENS: Dict[str, str] = {
    BALANCED_UNKNOWN: BALANCED_UNKNOWN,
    "Timmy / Tammy": "Timmy / Tammy",
    "Johnny / Jenny": "Johnny / Jenny",
    "Spike": "Spike",
    **{lens: "Timmy / Tammy" for lens in TIMMY_TAMMY_SUBTYPES},
    **{lens: "Johnny / Jenny" for lens in JOHNNY_JENNY_SUBTYPES},
    **{lens: "Spike" for lens in SPIKE_SUBTYPES},
}

INTENSITY_LEVELS = ("light", "normal", "strong")

GUIDE_PRESENTATIONS = (
    "masculine",
    "feminine",
    "either",
    "no_named_guide",
)

_LENS_ALIASES: Dict[str, str] = {
    "": BALANCED_UNKNOWN,
    "none": BALANCED_UNKNOWN,
    "no philosophy": BALANCED_UNKNOWN,
    "balanced": BALANCED_UNKNOWN,
    "balanced / unknown": BALANCED_UNKNOWN,
    "unknown": BALANCED_UNKNOWN,
    "rowan": BALANCED_UNKNOWN,
    "timmy": "Timmy / Tammy",
    "tammy": "Timmy / Tammy",
    "timmy/tammy": "Timmy / Tammy",
    "timmy / tammy": "Timmy / Tammy",
    "johnny": "Johnny / Jenny",
    "jenny": "Johnny / Jenny",
    "johnny/jenny": "Johnny / Jenny",
    "johnny / jenny": "Johnny / Jenny",
    "spike": "Spike",
    "big moment": "Big Moment",
    "big creature": "Big Creature / Stompy",
    "stompy": "Big Creature / Stompy",
    "big creature / stompy": "Big Creature / Stompy",
    "theme": "Theme / Vibe",
    "vibe": "Theme / Vibe",
    "theme / vibe": "Theme / Vibe",
    "pet card": "Pet Card",
    "let me do my thing": "Let Me Do My Thing",
    "battlecruiser": "Battlecruiser",
    "battle cruiser": "Battlecruiser",
    "engine builder": "Engine Builder",
    "commander exploiter": "Commander Exploiter",
    "weird card rescuer": "Weird Card Rescuer",
    "theme mechanic inventor": "Theme Mechanic Inventor",
    "self-imposed constraint builder": "Self-Imposed Constraint Builder",
    "self imposed constraint builder": "Self-Imposed Constraint Builder",
    "constraint builder": "Self-Imposed Constraint Builder",
    "combo builder": "Combo Builder",
    "consistency maximizer": "Consistency Maximizer",
    "efficiency optimizer": "Efficiency Optimizer",
    "curve and mana discipline": "Curve and Mana Discipline",
    "competitive closer": "Competitive Closer",
    "power-level calibrator": "Power-Level Calibrator",
    "power level calibrator": "Power-Level Calibrator",
    "interaction controller": "Interaction Controller",
}


def _normalize_key(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def normalize_lens(value: Optional[str]) -> str:
    """Return the canonical philosophy lens name for a user/config value."""
    key = _normalize_key(value)
    if key in _LENS_ALIASES:
        return _LENS_ALIASES[key]

    for lens in ALL_LENSES:
        if _normalize_key(lens) == key:
            return lens

    raise ValueError(
        f"Unknown philosophy lens: {value!r}. Expected one of: "
        + ", ".join(ALL_LENSES)
    )


def resolve_parent_philosophy(selected_lens: Optional[str]) -> str:
    """Resolve the parent philosophy for a selected lens."""
    lens = normalize_lens(selected_lens)
    return PARENT_BY_LENS[lens]


def _coerce_string_list(values: Optional[Iterable[str]]) -> List[str]:
    if values is None:
        return []
    result: List[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            result.append(text)
    return result


def _normalize_intensity(value: Optional[str]) -> str:
    text = _normalize_key(value or "normal")
    if text not in INTENSITY_LEVELS:
        raise ValueError(
            f"Unknown philosophy intensity: {value!r}. Expected one of: "
            + ", ".join(INTENSITY_LEVELS)
        )
    return text


def _normalize_guide_presentation(value: Optional[str]) -> str:
    text = _normalize_key(value or "no_named_guide")
    aliases = {
        "none": "no_named_guide",
        "no guide": "no_named_guide",
        "no named guide": "no_named_guide",
        "no named guide just philosophy labels": "no_named_guide",
        "labels only": "no_named_guide",
        "either/random": "either",
        "either / random": "either",
        "random": "either",
        "masculine guide": "masculine",
        "feminine guide": "feminine",
    }
    text = aliases.get(text, text)
    if text not in GUIDE_PRESENTATIONS:
        raise ValueError(
            f"Unknown guide presentation: {value!r}. Expected one of: "
            + ", ".join(GUIDE_PRESENTATIONS)
        )
    return text


def _optional_clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(frozen=True)
class PhilosophyProfile:
    """Validated philosophy choices for a deck review.

    The profile is intentionally immutable. Later pipeline code can pass it
    around safely without wondering whether another step mutated the selected
    philosophy lens.
    """

    selected_lens: str = BALANCED_UNKNOWN
    parent_philosophy: str = ""
    intensity: str = "normal"
    guide_presentation: str = "no_named_guide"
    pilot_notes: str = ""
    protected_cards: List[str] = field(default_factory=list)
    declared_constraints: List[str] = field(default_factory=list)
    combo_tolerance: Optional[str] = None
    budget_note: Optional[str] = None
    table_power_note: Optional[str] = None

    def __post_init__(self) -> None:
        lens = normalize_lens(self.selected_lens)
        parent = resolve_parent_philosophy(lens)
        intensity = _normalize_intensity(self.intensity)
        guide_presentation = _normalize_guide_presentation(self.guide_presentation)

        if self.parent_philosophy:
            # Allow broad parent names, but prevent invalid subtype/parent combinations.
            supplied_parent = normalize_lens(self.parent_philosophy)
            if supplied_parent != parent:
                raise ValueError(
                    f"Parent philosophy mismatch: selected_lens={lens!r} resolves to "
                    f"{parent!r}, but parent_philosophy={self.parent_philosophy!r}."
                )

        object.__setattr__(self, "selected_lens", lens)
        object.__setattr__(self, "parent_philosophy", parent)
        object.__setattr__(self, "intensity", intensity)
        object.__setattr__(self, "guide_presentation", guide_presentation)
        object.__setattr__(self, "pilot_notes", str(self.pilot_notes or "").strip())
        object.__setattr__(self, "protected_cards", _coerce_string_list(self.protected_cards))
        object.__setattr__(self, "declared_constraints", _coerce_string_list(self.declared_constraints))
        object.__setattr__(self, "combo_tolerance", _optional_clean(self.combo_tolerance))
        object.__setattr__(self, "budget_note", _optional_clean(self.budget_note))
        object.__setattr__(self, "table_power_note", _optional_clean(self.table_power_note))

    @property
    def is_balanced(self) -> bool:
        return self.selected_lens == BALANCED_UNKNOWN

    @property
    def is_big_three_only(self) -> bool:
        return self.selected_lens in BIG_THREE_PHILOSOPHIES

    @property
    def is_subtype(self) -> bool:
        return self.selected_lens in PHILOSOPHY_SUBTYPES

    @property
    def uses_named_guide(self) -> bool:
        return self.guide_presentation != "no_named_guide"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the profile to a plain dictionary."""
        return {
            "selected_lens": self.selected_lens,
            "parent_philosophy": self.parent_philosophy,
            "intensity": self.intensity,
            "guide_presentation": self.guide_presentation,
            "pilot_notes": self.pilot_notes,
            "protected_cards": list(self.protected_cards),
            "declared_constraints": list(self.declared_constraints),
            "combo_tolerance": self.combo_tolerance,
            "budget_note": self.budget_note,
            "table_power_note": self.table_power_note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PhilosophyProfile":
        """Create a profile from a dictionary, ignoring unknown future keys."""
        return cls(
            selected_lens=data.get("selected_lens", BALANCED_UNKNOWN),
            parent_philosophy=data.get("parent_philosophy", ""),
            intensity=data.get("intensity", "normal"),
            guide_presentation=data.get("guide_presentation", "no_named_guide"),
            pilot_notes=data.get("pilot_notes", ""),
            protected_cards=data.get("protected_cards", []),
            declared_constraints=data.get("declared_constraints", []),
            combo_tolerance=data.get("combo_tolerance"),
            budget_note=data.get("budget_note"),
            table_power_note=data.get("table_power_note"),
        )


def create_balanced_profile() -> PhilosophyProfile:
    """Return the default Balanced / Unknown profile."""
    return PhilosophyProfile()


def create_profile(
    selected_lens: Optional[str] = None,
    *,
    intensity: str = "normal",
    guide_presentation: str = "no_named_guide",
    pilot_notes: str = "",
    protected_cards: Optional[Iterable[str]] = None,
    declared_constraints: Optional[Iterable[str]] = None,
    combo_tolerance: Optional[str] = None,
    budget_note: Optional[str] = None,
    table_power_note: Optional[str] = None,
) -> PhilosophyProfile:
    """Convenience constructor for a validated PhilosophyProfile."""
    return PhilosophyProfile(
        selected_lens=selected_lens or BALANCED_UNKNOWN,
        intensity=intensity,
        guide_presentation=guide_presentation,
        pilot_notes=pilot_notes,
        protected_cards=_coerce_string_list(protected_cards),
        declared_constraints=_coerce_string_list(declared_constraints),
        combo_tolerance=combo_tolerance,
        budget_note=budget_note,
        table_power_note=table_power_note,
    )
