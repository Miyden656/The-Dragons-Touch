"""Collection candidate placeholder layer.

The legacy monolith has fuller collection/card-pool candidate behavior. This round
keeps the module boundary in place so future cleanup can move exact candidate
ranking here without mixing it into report building.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CollectionCandidateSummary:
    collection_file: Path | None = None
    candidates: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def build_collection_candidate_summary(collection_file: Path | None = None) -> CollectionCandidateSummary:
    notes = [
        "Collection/card-pool exact candidate ranking has a module boundary now, but full legacy candidate migration is deferred.",
        "Use category recommendations from the report until the collection ranking logic is moved from the monolith.",
    ]
    return CollectionCandidateSummary(collection_file=collection_file, candidates=[], notes=notes)
