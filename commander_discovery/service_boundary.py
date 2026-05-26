"""Commander Discovery service boundary.

v1.5.10.1 recovers the v1.5.10 Commander Discovery boundary after the original
packaging failed to create commander_discovery/service_boundary.py. This file
is a facade only and does not move or change active discovery behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

try:
    from collection_services import CollectionService
except Exception:  # pragma: no cover - defensive compatibility boundary
    CollectionService = None  # type: ignore


@dataclass(frozen=True)
class CommanderDiscoveryRequest:
    """Safe request contract for commander discovery workflows."""

    collection_dir: Optional[Path] = None
    include_partners: bool = True
    include_backgrounds: bool = True
    include_doctors_companions: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CommanderDiscoveryStatus:
    """JSON-safe status for discovery boundary health checks."""

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


class CommanderDiscoveryService:
    """Facade for future Commander Discovery cleanup.

    Existing modules such as discovery.py, collection_scanner.py, eligibility.py,
    and candidate_rules.py remain in place. Future patches can move/adapt
    behavior behind this boundary after regression gates are in place.
    """

    service_version = "v1.5.10.1"

    def status(self) -> CommanderDiscoveryStatus:
        return CommanderDiscoveryStatus(
            service_version=self.service_version,
            collection_services_available=CollectionService is not None,
        )

    def describe_request(self, request: CommanderDiscoveryRequest) -> Dict[str, object]:
        return {
            "service_version": self.service_version,
            "collection_dir": str(request.collection_dir) if request.collection_dir else "",
            "include_partners": request.include_partners,
            "include_backgrounds": request.include_backgrounds,
            "include_doctors_companions": request.include_doctors_companions,
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

    return CommanderDiscoveryService().status().as_dict()
