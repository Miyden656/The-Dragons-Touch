"""Replacement Engine service boundary.

v1.5.11.1 recovers the v1.5.11 Replacement Engine boundary after the original
package failed to create replacements/service_boundary.py. This file is a facade
only and does not move or change active replacement behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    from collection_services import CollectionService
except Exception:  # pragma: no cover - defensive compatibility boundary
    CollectionService = None  # type: ignore


@dataclass(frozen=True)
class ReplacementReviewRequest:
    """Safe request contract for future replacement-review workflows."""

    deck_path: Optional[Path] = None
    collection_dir: Optional[Path] = None
    commander_name: str = ""
    strategy_id: str = ""
    prefer_collection_first: bool = True
    allow_outside_collection_upgrades: bool = True
    replacement_categories: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplacementEngineStatus:
    """JSON-safe status for replacement boundary health checks."""

    service_version: str
    collection_services_available: bool
    behavior_changed: bool = False
    status: str = "foundation_ready"

    def as_dict(self) -> Dict[str, object]:
        return {
            "service_version": self.service_version,
            "collection_services_available": self.collection_services_available,
            "behavior_changed": self.behavior_changed,
            "status": self.status,
        }


class ReplacementEngineService:
    """Facade for future replacement-engine cleanup.

    Existing modules remain in place. Future patches can move replacement
    candidate generation/scoring behind this service after dedicated regression
    gates are in place.
    """

    service_version = "v1.5.11.1"

    def status(self) -> ReplacementEngineStatus:
        return ReplacementEngineStatus(
            service_version=self.service_version,
            collection_services_available=CollectionService is not None,
        )

    def describe_request(self, request: ReplacementReviewRequest) -> Dict[str, object]:
        return {
            "service_version": self.service_version,
            "deck_path": str(request.deck_path) if request.deck_path else "",
            "collection_dir": str(request.collection_dir) if request.collection_dir else "",
            "commander_name": request.commander_name,
            "strategy_id": request.strategy_id,
            "prefer_collection_first": request.prefer_collection_first,
            "allow_outside_collection_upgrades": request.allow_outside_collection_upgrades,
            "replacement_category_count": len(request.replacement_categories),
            "behavior_changed": False,
        }

    def collection_status(self) -> Dict[str, object]:
        if CollectionService is None:
            return {
                "collection_services_available": False,
                "behavior_changed": False,
                "status": "collection_services_unavailable",
            }
        service = CollectionService()
        status = service.status()
        status["collection_services_available"] = True
        status["behavior_changed"] = False
        return status


def service_health() -> Dict[str, object]:
    """Return lightweight service health for verifiers."""

    return ReplacementEngineService().status().as_dict()
