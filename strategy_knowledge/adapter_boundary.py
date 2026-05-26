"""Strategy Knowledge adapter boundary.

v1.5.12 creates a safe adapter facade around the active Strategy Knowledge
baseline. It does not move profiles, rewrite scoring, or mutate the live
249-profile index.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class StrategyKnowledgeStatus:
    """JSON-safe status for Strategy Knowledge adapter health checks."""

    service_version: str
    index_path: Path
    index_exists: bool
    active_profile_count: int = 0
    behavior_changed: bool = False
    status: str = "foundation_ready"

    def as_dict(self) -> Dict[str, object]:
        return {
            "service_version": self.service_version,
            "index_path": str(self.index_path),
            "index_exists": self.index_exists,
            "active_profile_count": self.active_profile_count,
            "behavior_changed": self.behavior_changed,
            "status": self.status,
        }


class StrategyKnowledgeAdapter:
    """Facade for future Strategy Knowledge service/report cleanup.

    The active Strategy Knowledge implementation remains in place. This adapter
    gives future report/build modules a stable place to ask for status without
    directly reaching into lock/index internals.
    """

    service_version = "v1.5.12"

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[1]
        self.index_path = (
            self.project_root
            / "strategy_knowledge"
            / "index"
            / "strategy_profile_index.latest.json"
        )

    def active_profile_count(self) -> int:
        """Return best-effort active profile count without mutating the index."""

        if not self.index_path.exists():
            return 0
        try:
            import json

            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return 0

        if isinstance(payload, dict):
            for key in ("profile_count", "active_profile_count", "indexed_profiles", "total_profiles"):
                value = payload.get(key)
                if isinstance(value, int):
                    return value
            profiles = payload.get("profiles")
            if isinstance(profiles, list):
                return len(profiles)
            index = payload.get("index")
            if isinstance(index, list):
                return len(index)
            strategies = payload.get("strategies")
            if isinstance(strategies, list):
                return len(strategies)
        return 0

    def status(self) -> StrategyKnowledgeStatus:
        """Return adapter status without changing scoring behavior."""

        return StrategyKnowledgeStatus(
            service_version=self.service_version,
            index_path=self.index_path,
            index_exists=self.index_path.exists(),
            active_profile_count=self.active_profile_count(),
        )


def service_health(project_root: Optional[Path] = None) -> Dict[str, object]:
    """Return lightweight Strategy Knowledge adapter health for verifiers."""

    return StrategyKnowledgeAdapter(project_root=project_root).status().as_dict()
