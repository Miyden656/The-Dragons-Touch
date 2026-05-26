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
