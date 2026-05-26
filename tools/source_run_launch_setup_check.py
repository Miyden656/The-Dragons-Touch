"""Source-run launch/setup health helper.

v1.5.15.1 recovers the passive launch/setup helper without using dataclasses so
it stays safe under Python 3.14 importlib/spec loading. It does not launch the
UI, run analysis, download data, or modify deck-building behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


REQUIRED_LAUNCH_SURFACES = {
    "main.py": "Main source-run backend entrypoint.",
    "desktop_ui_launcher.py": "Desktop UI launcher helper.",
    "Launch_The_Dragons_Touch.py": "User-facing Python launcher.",
    "download_scryfall_data.py": "Scryfall data setup/download helper.",
    "app_io/project_paths.py": "Backend-owned runtime path contract.",
    "ui/services/backend_boundary.py": "UI-facing backend status boundary.",
}


def project_root() -> Path:
    """Return the project root based on this helper location."""

    return Path(__file__).resolve().parents[1]


def launch_surface_status(root: Path | None = None) -> List[Dict[str, object]]:
    """Return launch/setup surface status without executing launch behavior."""

    base = root or project_root()
    return [
        {
            "path": relative,
            "exists": (base / relative).exists(),
            "purpose": purpose,
        }
        for relative, purpose in REQUIRED_LAUNCH_SURFACES.items()
    ]


def launch_setup_health(root: Path | None = None) -> Dict[str, object]:
    """Return JSON-safe launch/setup health."""

    statuses = launch_surface_status(root)
    missing = [str(status["path"]) for status in statuses if not status["exists"]]
    return {
        "service": "source_run_launch_setup",
        "service_version": "v1.5.15.1",
        "status": "ready" if not missing else "missing_surfaces",
        "missing": missing,
        "surfaces": statuses,
        "behavior_changed": False,
        "launch_executed": False,
        "analysis_executed": False,
        "data_download_executed": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(launch_setup_health(), indent=2))
