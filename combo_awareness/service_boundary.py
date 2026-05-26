"""Combo Awareness core service contract.

v1.5.13 updates the architecture contract: Combo Awareness is no longer treated
as an optional side feature. It is a core service the main system should have
available for normal deck review/build workflows.

This patch creates the core service boundary and default runtime contract. It
does not rewrite combo matching algorithms or mutate combo data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class ComboAwarenessRequest:
    """Safe request contract for combo-aware deck review/build workflows."""

    deck_path: Optional[Path] = None
    collection_dir: Optional[Path] = None
    commander_name: str = ""
    include_breakdown_artifact: bool = True
    include_report_summary: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ComboAwarenessStatus:
    """JSON-safe status for combo-awareness service health checks."""

    service_version: str
    mandatory_core_service: bool = True
    default_enabled: bool = True
    legacy_env_override_supported_for_debug: bool = True
    behavior_changed: bool = False
    status: str = "core_service_ready"

    def as_dict(self) -> Dict[str, object]:
        return {
            "service_version": self.service_version,
            "mandatory_core_service": self.mandatory_core_service,
            "default_enabled": self.default_enabled,
            "legacy_env_override_supported_for_debug": self.legacy_env_override_supported_for_debug,
            "behavior_changed": self.behavior_changed,
            "status": self.status,
        }


class ComboAwarenessService:
    """Facade for Combo Awareness as a core system service.

    Existing modules such as combo_config.py, combo_matcher.py, deck_parser.py,
    and collection_loader.py remain in place. Future patches can wire active
    run-analysis/report paths through this service after regression gates are
    in place.
    """

    service_version = "v1.5.13"

    def status(self) -> ComboAwarenessStatus:
        return ComboAwarenessStatus(service_version=self.service_version)

    def describe_request(self, request: ComboAwarenessRequest) -> Dict[str, object]:
        return {
            "service_version": self.service_version,
            "deck_path": str(request.deck_path) if request.deck_path else "",
            "collection_dir": str(request.collection_dir) if request.collection_dir else "",
            "commander_name": request.commander_name,
            "include_breakdown_artifact": request.include_breakdown_artifact,
            "include_report_summary": request.include_report_summary,
            "mandatory_core_service": True,
            "default_enabled": True,
            "behavior_changed": False,
        }

    def runtime_policy(self) -> Dict[str, object]:
        """Return the normalized v1.5.13 combo-awareness runtime policy."""

        return {
            "combo_awareness_is_optional": False,
            "combo_awareness_runs_with_main_system": True,
            "legacy_environment_flags_are_debug_only": True,
            "expected_main_system_behavior": (
                "Normal deck review/build workflows should have combo awareness available by default."
            ),
            "behavior_changed": False,
        }


def service_health() -> Dict[str, object]:
    """Return lightweight core-service health for verifiers."""

    service = ComboAwarenessService()
    health = service.status().as_dict()
    health["runtime_policy"] = service.runtime_policy()
    return health
