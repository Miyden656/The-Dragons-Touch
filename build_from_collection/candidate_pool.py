"""Collection candidate pool shape for Build From Collection v1.3.7.

This module defines the data shape that future collection parsing and owned-card
classification can use when preparing a build-from-collection candidate pool.
It is intentionally shape-only.

Marker: Collection Candidate Pool Shape.
Marker: No owned card classification.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No deck generation.
Marker: No 100-card shell generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy


@dataclass(frozen=True, slots=True)
class CollectionCandidateSource:
    """Source metadata for a future collection candidate pool entry."""

    source_name: str = "local_collection"
    source_kind: str = "collection"
    collection_first: bool = True
    source_note: str = (
        "Collection-first source metadata only. No owned card classification, "
        "exact card selection, shell generation, or deck generation."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_kind": self.source_kind,
            "collection_first": self.collection_first,
            "source_note": self.source_note,
        }


@dataclass(frozen=True, slots=True)
class CollectionCandidatePoolEntry:
    """Shape-only entry for a card that may be considered later from the user's collection."""

    card_name: str
    normalized_name: str
    owned_quantity: int = 0
    sources: tuple[CollectionCandidateSource, ...] = field(default_factory=lambda: (CollectionCandidateSource(),))
    scryfall_id: str | None = None
    type_line: str = ""
    oracle_text: str = ""
    color_identity: tuple[str, ...] = field(default_factory=tuple)
    mana_value: float | None = None
    raw_record: dict[str, Any] = field(default_factory=dict)
    role_tags: tuple[str, ...] = field(default_factory=tuple)
    candidate_notes: tuple[str, ...] = field(default_factory=lambda: (
        "Shape-only candidate entry",
        "No owned card classification",
        "No exact card selection",
    ))
    exact_card_selection: bool = False
    owned_card_classification_complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_name": self.card_name,
            "normalized_name": self.normalized_name,
            "owned_quantity": self.owned_quantity,
            "sources": [source.to_dict() for source in self.sources],
            "scryfall_id": self.scryfall_id,
            "type_line": self.type_line,
            "oracle_text": self.oracle_text,
            "color_identity": list(self.color_identity),
            "mana_value": self.mana_value,
            "raw_record": dict(self.raw_record),
            "role_tags": list(self.role_tags),
            "candidate_notes": list(self.candidate_notes),
            "exact_card_selection": self.exact_card_selection,
            "owned_card_classification_complete": self.owned_card_classification_complete,
        }


@dataclass(slots=True)
class CollectionCandidatePoolShape:
    """Display/testable pool shape for future owned-card candidate work."""

    entries: tuple[CollectionCandidatePoolEntry, ...] = field(default_factory=tuple)
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    pool_version: str = "v1.3.7"
    pool_name: str = "Collection Candidate Pool Shape"
    collection_first: bool = True
    planning_only: bool = True
    assumed_basic_lands_available: bool = True
    nonbasic_lands_remain_collection_first: bool = True
    deferred_behavior: tuple[str, ...] = (
        "No owned card classification",
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell generation",
        "No deck generation",
        "No 100-card shell generation",
        "No scoring changes",
        "No cut or replacement changes",
        "No normal deck review changes",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "pool_version": self.pool_version,
            "pool_name": self.pool_name,
            "collection_first": self.collection_first,
            "planning_only": self.planning_only,
            "assumed_basic_lands_available": self.assumed_basic_lands_available,
            "nonbasic_lands_remain_collection_first": self.nonbasic_lands_remain_collection_first,
            "entries": [entry.to_dict() for entry in self.entries],
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_7_boundary": (
                "Collection candidate pool shape is a data contract only. v1.3.7 does not parse "
                "the user collection, classify owned cards, select exact cards, create role-count "
                "targets, generate a mana base, insert lands, build a shell, generate a deck, score "
                "cards, recommend cuts, or change normal deck review behavior. Basic lands are "
                "assumed available; nonbasic lands remain collection-first."
            ),
        }


def normalize_collection_candidate_name(card_name: str | None) -> str:
    """Normalize a card name for future candidate-pool deduplication."""
    if not card_name:
        return ""
    return " ".join(str(card_name).strip().casefold().split())


def create_collection_candidate_pool_entry(
    card_name: str,
    owned_quantity: int = 0,
    source_name: str = "local_collection",
    type_line: str = "",
    oracle_text: str = "",
    color_identity: tuple[str, ...] | list[str] | None = None,
    mana_value: float | None = None,
    scryfall_id: str | None = None,
    raw_record: dict[str, Any] | None = None,
) -> CollectionCandidatePoolEntry:
    """Create a shape-only candidate pool entry without classifying or selecting the card."""
    safe_quantity = max(0, int(owned_quantity or 0))
    normalized = normalize_collection_candidate_name(card_name)
    colors = tuple(color_identity or ())
    return CollectionCandidatePoolEntry(
        card_name=str(card_name or "").strip(),
        normalized_name=normalized,
        owned_quantity=safe_quantity,
        sources=(CollectionCandidateSource(source_name=source_name),),
        scryfall_id=scryfall_id,
        type_line=type_line or "",
        oracle_text=oracle_text or "",
        color_identity=colors,
        mana_value=mana_value,
        raw_record=dict(raw_record or {}),
    )


def create_collection_candidate_pool_shape(
    entries: tuple[CollectionCandidatePoolEntry, ...] | list[CollectionCandidatePoolEntry] | None = None,
) -> CollectionCandidatePoolShape:
    """Create the v1.3.7 collection candidate pool shape without selecting cards."""
    return CollectionCandidatePoolShape(entries=tuple(entries or ()))
