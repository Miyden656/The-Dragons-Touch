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

def is_subtype_lens(value: str) -> bool:
    """Return True if value resolves to one of the 18 subtype lenses."""
    return get_lens_definition(value).is_subtype

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
