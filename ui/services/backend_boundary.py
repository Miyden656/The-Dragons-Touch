"""UI backend boundary service.

v1.5.14 creates a small UI-facing facade that can safely report backend service
availability without making UI pages import internal implementation details.

This patch does not change UI visuals, interaction behavior, deck-building
behavior, report wording, Strategy Knowledge scoring, or Combo Awareness logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


def _safe_service_health(module_name: str) -> Dict[str, object]:
    """Import a service_health function safely and return a JSON-safe payload."""

    try:
        module = __import__(module_name, fromlist=["service_health"])
        health_func = getattr(module, "service_health")
        health = health_func()
        if isinstance(health, dict):
            return dict(health)
        return {"status": "unknown_payload", "behavior_changed": False}
    except Exception as exc:  # pragma: no cover - defensive UI boundary
        return {
            "status": "unavailable",
            "error": f"{type(exc).__name__}: {exc}",
            "behavior_changed": False,
        }


@dataclass(frozen=True)
class BackendServiceStatus:
    """JSON-safe backend service status for UI pages."""

    service_name: str
    available: bool
    health: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return {
            "service_name": self.service_name,
            "available": self.available,
            "health": dict(self.health),
        }


class UIBackendBoundaryService:
    """Thin UI-facing facade for backend service availability.

    Future UI pages should depend on this boundary instead of reaching directly
    into strategy, combo, collection, replacement, or commander-building internals.
    """

    service_version = "v1.5.14"

    SERVICE_MODULES = {
        "runtime_paths": "app_io.project_paths",
        "commander_building": "commander_building.service_boundary",
        "collection_services": "collection_services.service_boundary",
        "commander_discovery": "commander_discovery.service_boundary",
        "replacements": "replacements.service_boundary",
        "strategy_knowledge": "strategy_knowledge.adapter_boundary",
        "combo_awareness": "combo_awareness.service_boundary",
        "reports_sections": "reports.sections.registry",
    }

    def backend_status(self) -> Dict[str, BackendServiceStatus]:
        statuses: Dict[str, BackendServiceStatus] = {}
        for service_name, module_name in self.SERVICE_MODULES.items():
            health = self._module_health(service_name, module_name)
            available = health.get("status") not in {"unavailable", "missing"}
            statuses[service_name] = BackendServiceStatus(
                service_name=service_name,
                available=bool(available),
                health=health,
            )
        return statuses

    def _module_health(self, service_name: str, module_name: str) -> Dict[str, object]:
        if service_name == "runtime_paths":
            try:
                from app_io.project_paths import runtime_data_status

                status = runtime_data_status()
                if isinstance(status, dict):
                    status = dict(status)
                else:
                    status = {"status": "available"}
                status.setdefault("status", "available")
                status.setdefault("behavior_changed", False)
                return status
            except Exception as exc:  # pragma: no cover
                return {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}", "behavior_changed": False}

        if service_name == "reports_sections":
            try:
                from reports.sections.registry import registry_health

                health = registry_health()
                if isinstance(health, dict):
                    payload = dict(health)
                else:
                    payload = {"status": "available"}
                payload.setdefault("status", "available")
                payload.setdefault("behavior_changed", False)
                return payload
            except Exception as exc:  # pragma: no cover
                return {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}", "behavior_changed": False}

        return _safe_service_health(module_name)

    def as_dict(self) -> Dict[str, object]:
        statuses = self.backend_status()
        return {
            "service": "ui_backend_boundary",
            "service_version": self.service_version,
            "behavior_changed": False,
            "ui_visuals_changed": False,
            "backend_services": {name: status.as_dict() for name, status in statuses.items()},
        }


def service_health() -> Dict[str, object]:
    """Return UI backend boundary health for verifiers."""

    return UIBackendBoundaryService().as_dict()
