"""
Central runtime path helpers for The Dragon's Touch.

v1.5.6 moves the canonical runtime-path service out of the UI package and into
app_io so backend, reports, setup tools, combo awareness, and the desktop UI can
all depend on the same non-UI path contract.

Boundary:
- This module does not download data.
- This module does not build indexes.
- This module does not run deck analysis.
- This module only resolves and creates expected runtime paths.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


SCRYFALL_CARDS_FILENAME = "scryfall_cards.json"
COMMANDER_SPELLBOOK_BULK_FILENAME = "combo.json"
COMMANDER_SPELLBOOK_INDEX_FILENAME = "combo_index.json"
COMMANDER_SPELLBOOK_PARITY_INDEX_FILENAME = "combo_index_parity.json"


def is_frozen_app() -> bool:
    """Return True when running from a PyInstaller-built EXE."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Resolve the project root in source mode.

    This file lives at app_io/project_paths.py, so parents[1] is the project
    root. Keeping this in app_io avoids making backend code depend on ui/.
    """
    return Path(__file__).resolve().parents[1]


def executable_folder() -> Path:
    """Return the folder containing the running executable or source project."""
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    return project_root()


def runtime_root() -> Path:
    """Return the writable runtime root for source mode or frozen EXE mode."""
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    return project_root()


@dataclass(frozen=True)
class RuntimePaths:
    """Concrete runtime paths used by the app and setup tools."""

    root: Path
    data_dir: Path
    commander_spellbook_dir: Path
    decklists_dir: Path
    collection_dir: Path
    outputs_dir: Path
    settings_dir: Path

    scryfall_cards_json: Path
    commander_spellbook_bulk_json: Path
    combo_index_json: Path
    combo_index_parity_json: Path


def get_runtime_paths() -> RuntimePaths:
    """Return runtime paths without creating folders."""
    root = runtime_root()
    data_dir = root / "data"
    commander_spellbook_dir = data_dir / "commander_spellbook"

    return RuntimePaths(
        root=root,
        data_dir=data_dir,
        commander_spellbook_dir=commander_spellbook_dir,
        decklists_dir=root / "Decklists",
        collection_dir=root / "collection",
        outputs_dir=root / "Outputs",
        settings_dir=root / "settings",
        scryfall_cards_json=data_dir / SCRYFALL_CARDS_FILENAME,
        commander_spellbook_bulk_json=data_dir / COMMANDER_SPELLBOOK_BULK_FILENAME,
        combo_index_json=commander_spellbook_dir / COMMANDER_SPELLBOOK_INDEX_FILENAME,
        combo_index_parity_json=commander_spellbook_dir / COMMANDER_SPELLBOOK_PARITY_INDEX_FILENAME,
    )


def ensure_runtime_folders() -> RuntimePaths:
    """Create writable runtime folders if they do not already exist."""
    paths = get_runtime_paths()

    folders = [
        paths.data_dir,
        paths.commander_spellbook_dir,
        paths.decklists_dir,
        paths.collection_dir,
        paths.outputs_dir,
        paths.settings_dir,
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    return paths


def runtime_data_status() -> dict[str, object]:
    """Return a JSON-friendly status dictionary for Settings/Data Setup UI."""
    paths = get_runtime_paths()

    def file_status(path: Path) -> dict[str, object]:
        exists = path.exists() and path.is_file()
        return {
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else 0,
        }

    return {
        "frozen": is_frozen_app(),
        "runtime_root": str(paths.root),
        "data_dir": str(paths.data_dir),
        "scryfall_cards_json": file_status(paths.scryfall_cards_json),
        "commander_spellbook_bulk_json": file_status(paths.commander_spellbook_bulk_json),
        "combo_index_json": file_status(paths.combo_index_json),
        "combo_index_parity_json": file_status(paths.combo_index_parity_json),
    }


def print_runtime_data_status() -> None:
    """Developer-facing helper for quick diagnostics."""
    status = runtime_data_status()

    print("The Dragon's Touch Runtime Data Status")
    print("=====================================")
    print(f"Frozen app: {status['frozen']}")
    print(f"Runtime root: {status['runtime_root']}")
    print(f"Data dir: {status['data_dir']}")
    print()

    for key in [
        "scryfall_cards_json",
        "commander_spellbook_bulk_json",
        "combo_index_json",
        "combo_index_parity_json",
    ]:
        item = status[key]
        print(f"{key}:")
        print(f"  Exists: {item['exists']}")
        print(f"  Size:   {item['size_bytes']}")
        print(f"  Path:   {item['path']}")
        print()


__all__ = [
    "COMMANDER_SPELLBOOK_BULK_FILENAME",
    "COMMANDER_SPELLBOOK_INDEX_FILENAME",
    "COMMANDER_SPELLBOOK_PARITY_INDEX_FILENAME",
    "SCRYFALL_CARDS_FILENAME",
    "RuntimePaths",
    "ensure_runtime_folders",
    "executable_folder",
    "get_runtime_paths",
    "is_frozen_app",
    "print_runtime_data_status",
    "project_root",
    "runtime_data_status",
    "runtime_root",
]
