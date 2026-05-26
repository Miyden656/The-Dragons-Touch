"""Collection Source Preference UI model for Build From Collection v1.3.16.

This module records how Commander’s Call should treat the user collection when
future Build From Collection outputs begin selecting or suggesting cards.

Marker: Collection Source Preference UI.
Marker: collection_source_preference.
Marker: outside_collection_upgrades_allowed.
Marker: user-controlled outside-collection upgrades.
Marker: Owned cards only, except assumed basic lands.
Marker: Prefer owned cards, show missing categories.
Marker: Prefer owned cards, suggest exact outside-collection upgrades.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No mana-base generation.
Marker: No land insertion.
Marker: No shell generation.
Marker: No deck generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

COLLECTION_SOURCE_OWNED_ONLY = "owned_only"
COLLECTION_SOURCE_OWNED_MISSING = "owned_first_missing_categories"
COLLECTION_SOURCE_OWNED_UPGRADES = "owned_first_exact_outside_upgrades"

COLLECTION_SOURCE_PREFERENCE_OPTIONS: tuple[tuple[str, str, bool], ...] = (
    (COLLECTION_SOURCE_OWNED_ONLY, "Owned cards only, except assumed basic lands", False),
    (COLLECTION_SOURCE_OWNED_MISSING, "Prefer owned cards, show missing categories", False),
    (COLLECTION_SOURCE_OWNED_UPGRADES, "Prefer owned cards, suggest exact outside-collection upgrades", True),
)

_COLLECTION_SOURCE_ALIASES = {
    "a": COLLECTION_SOURCE_OWNED_ONLY,
    "owned": COLLECTION_SOURCE_OWNED_ONLY,
    "owned only": COLLECTION_SOURCE_OWNED_ONLY,
    "owned cards only": COLLECTION_SOURCE_OWNED_ONLY,
    COLLECTION_SOURCE_OWNED_ONLY: COLLECTION_SOURCE_OWNED_ONLY,
    "b": COLLECTION_SOURCE_OWNED_MISSING,
    "missing": COLLECTION_SOURCE_OWNED_MISSING,
    "show missing categories": COLLECTION_SOURCE_OWNED_MISSING,
    COLLECTION_SOURCE_OWNED_MISSING: COLLECTION_SOURCE_OWNED_MISSING,
    "c": COLLECTION_SOURCE_OWNED_UPGRADES,
    "upgrades": COLLECTION_SOURCE_OWNED_UPGRADES,
    "outside upgrades": COLLECTION_SOURCE_OWNED_UPGRADES,
    "exact outside upgrades": COLLECTION_SOURCE_OWNED_UPGRADES,
    COLLECTION_SOURCE_OWNED_UPGRADES: COLLECTION_SOURCE_OWNED_UPGRADES,
}

def collection_source_preference_labels() -> tuple[str, ...]:
    """Return user-facing labels for collection source behavior."""
    return tuple(label for _, label, _ in COLLECTION_SOURCE_PREFERENCE_OPTIONS)

def normalize_collection_source_preference(value: str | None) -> str:
    """Normalize user/UI collection source preference input to a stable key."""
    raw = str(value or "").strip()
    lowered = raw.lower()
    if lowered in _COLLECTION_SOURCE_ALIASES:
        return _COLLECTION_SOURCE_ALIASES[lowered]
    for key, label, _ in COLLECTION_SOURCE_PREFERENCE_OPTIONS:
        if raw == label or lowered == label.lower():
            return key
    return COLLECTION_SOURCE_OWNED_UPGRADES

def collection_source_preference_label(key_or_label: str | None) -> str:
    """Return the user-facing label for a normalized collection source key."""
    key = normalize_collection_source_preference(key_or_label)
    for option_key, label, _ in COLLECTION_SOURCE_PREFERENCE_OPTIONS:
        if option_key == key:
            return label
    return "Prefer owned cards, suggest exact outside-collection upgrades"

def collection_source_allows_outside_upgrades(key_or_label: str | None) -> bool:
    """Return whether exact outside-collection upgrades are allowed by the user."""
    key = normalize_collection_source_preference(key_or_label)
    for option_key, _label, allowed in COLLECTION_SOURCE_PREFERENCE_OPTIONS:
        if option_key == key:
            return allowed
    return True

@dataclass(slots=True)
class CollectionSourcePreferencePreview:
    """Preview-only collection source preference payload."""
    collection_source_preference: str = COLLECTION_SOURCE_OWNED_UPGRADES
    collection_source_label: str = "Prefer owned cards, suggest exact outside-collection upgrades"
    outside_collection_upgrades_allowed: bool = True
    basic_lands_assumed_available: bool = True
    nonbasic_lands_collection_first: bool = True
    user_controlled: bool = True
    preview_name: str = "Collection Source Preference UI"
    preview_version: str = "v1.3.16"
    preview_only: bool = True
    exact_card_selection: bool = False
    role_count_target_generated: bool = False
    mana_base_generated: bool = False
    land_inserted: bool = False
    shell_generated: bool = False
    deck_generated: bool = False
    deferred_behavior: tuple[str, ...] = field(default_factory=lambda: (
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell generation",
        "No deck generation",
        "No normal deck review changes",
        "Outside-collection upgrades are user-controlled",
    ))
    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_name": self.preview_name,
            "preview_version": self.preview_version,
            "preview_only": self.preview_only,
            "collection_source_preference": self.collection_source_preference,
            "collection_source_label": self.collection_source_label,
            "outside_collection_upgrades_allowed": self.outside_collection_upgrades_allowed,
            "basic_lands_assumed_available": self.basic_lands_assumed_available,
            "nonbasic_lands_collection_first": self.nonbasic_lands_collection_first,
            "user_controlled": self.user_controlled,
            "exact_card_selection": self.exact_card_selection,
            "role_count_target_generated": self.role_count_target_generated,
            "mana_base_generated": self.mana_base_generated,
            "land_inserted": self.land_inserted,
            "shell_generated": self.shell_generated,
            "deck_generated": self.deck_generated,
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_16_boundary": (
                "Collection Source Preference UI records whether the user wants owned-only cards, owned-first missing-category guidance, or owned-first exact outside-collection upgrades. "
                "It does not select exact cards, create role-count targets, generate a mana base, insert lands, generate a shell, generate a deck, score cards, recommend cuts, or change normal deck review behavior. "
                "Basic lands are assumed available. Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
            ),
        }

def create_collection_source_preference_preview(collection_source_preference: str = COLLECTION_SOURCE_OWNED_UPGRADES) -> CollectionSourcePreferencePreview:
    """Create a preview-only collection source preference payload."""
    key = normalize_collection_source_preference(collection_source_preference)
    return CollectionSourcePreferencePreview(
        collection_source_preference=key,
        collection_source_label=collection_source_preference_label(key),
        outside_collection_upgrades_allowed=collection_source_allows_outside_upgrades(key),
    )

def collection_source_preference_lines(preview: CollectionSourcePreferencePreview) -> tuple[str, ...]:
    """Return concise UI/report lines for collection source behavior."""
    data = preview.to_dict()
    allowed = "Yes" if data.get("outside_collection_upgrades_allowed") else "No"
    return (
        "Collection Source Preference Preview created.",
        "This is collection-behavior setup context only; it does not build the deck.",
        f"Collection source behavior: {data.get('collection_source_label')}",
        f"Outside-collection upgrades allowed: {allowed}",
        "Basic lands are assumed available.",
        "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.",
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell generation.",
        "No deck generation.",
    )
