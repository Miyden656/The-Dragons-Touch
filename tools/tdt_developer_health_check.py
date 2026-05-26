"""The Dragon's Touch developer health check.

v1.5.17 adds a passive troubleshooting helper that summarizes key project
surfaces without launching the UI, running analysis, downloading data, or
changing deck-building behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import importlib
import json
import sys


SERVICE_MODULES = {
    "runtime_paths": "app_io.project_paths",
    "ui_backend_boundary": "ui.services.backend_boundary",
    "commander_building": "commander_building.service_boundary",
    "collection_services": "collection_services.service_boundary",
    "commander_discovery": "commander_discovery.service_boundary",
    "replacement_engine": "replacements.service_boundary",
    "strategy_knowledge": "strategy_knowledge.adapter_boundary",
    "combo_awareness": "combo_awareness.service_boundary",
    "report_sections": "reports.sections.registry",
}

IMPORTANT_PATHS = [
    "main.py",
    "config.py",
    "README.md",
    "README_START_HERE.txt",
    "requirements.txt",
    "Launch_The_Dragons_Touch.py",
    "desktop_ui_launcher.py",
    "download_scryfall_data.py",
    "app_io/project_paths.py",
    "tools/source_run_launch_setup_check.py",
    "docs/user_docs/START_HERE_SOURCE_RUN_v1.5.15.md",
    "docs/patch_history/root_readmes/ROOT_README_ARCHIVE_MANIFEST_v1.5.16.md",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_import_path(root: Path) -> None:
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def safe_service_health(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        health_func = getattr(module, "service_health", None)
        registry_health = getattr(module, "registry_health", None)
        if callable(health_func):
            result = health_func()
        elif callable(registry_health):
            result = registry_health()
        else:
            result = {"status": "imported_no_health_function"}
        if not isinstance(result, dict):
            result = {"status": "non_dict_health_payload", "payload_type": type(result).__name__}
        result.setdefault("behavior_changed", False)
        return result
    except Exception as exc:
        return {
            "status": "unavailable",
            "error": f"{type(exc).__name__}: {exc}",
            "behavior_changed": False,
        }


def path_status(root: Path) -> List[Dict[str, Any]]:
    statuses = []
    for relative in IMPORTANT_PATHS:
        path = root / relative
        statuses.append(
            {
                "path": relative,
                "exists": path.exists(),
                "type": "directory" if path.is_dir() else "file" if path.is_file() else "missing",
                "size_bytes": path.stat().st_size if path.is_file() else None,
            }
        )
    return statuses


def folder_counts(root: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for folder_name in ["Decklists", "collection", "Outputs", "docs", "tools", "Old Do Not Use"]:
        folder = root / folder_name
        counts[folder_name] = sum(1 for p in folder.rglob("*") if p.is_file()) if folder.exists() else 0
    return counts


def root_surface(root: Path) -> Dict[str, Any]:
    entries = []
    for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        entries.append({"name": path.name, "type": "directory" if path.is_dir() else "file"})
    versioned_readmes = [
        p.name
        for p in root.iterdir()
        if p.is_file()
        and p.suffix.lower() == ".txt"
        and (p.name.startswith("README_v") or p.name.startswith("README_TDT_v") or p.name.startswith("README_INSTALL_v"))
    ]
    return {
        "root_item_count": len(entries),
        "entries": entries,
        "root_versioned_readmes": sorted(versioned_readmes),
    }


def developer_health(root: Path | None = None) -> Dict[str, Any]:
    base = root or project_root()
    ensure_import_path(base)

    service_statuses = {
        name: safe_service_health(module)
        for name, module in SERVICE_MODULES.items()
    }

    return {
        "service": "tdt_developer_health_check",
        "service_version": "v1.5.17",
        "status": "ready",
        "project_root": str(base),
        "behavior_changed": False,
        "launch_executed": False,
        "analysis_executed": False,
        "data_download_executed": False,
        "important_paths": path_status(base),
        "folder_counts": folder_counts(base),
        "root_surface": root_surface(base),
        "service_statuses": service_statuses,
    }


if __name__ == "__main__":
    print(json.dumps(developer_health(), indent=2))
