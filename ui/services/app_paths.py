"""
v0.11.2-dev — Runtime path helpers for The Dragon's Touch.

Purpose:
- Provide one central place for source-mode and EXE-mode paths.
- Keep writable runtime folders beside the EXE when frozen by PyInstaller.
- Keep source-mode behavior stable when running from the project folder.

Important:
- This module does not download data.
- This module does not build indexes.
- This module only defines and creates expected runtime paths.
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


def executable_folder() -> Path:
    """
    Folder containing the running EXE in frozen mode.

    In source mode, this falls back to the project root.
    """
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    return project_root()


def project_root() -> Path:
    """
    Resolve the project root in source mode.

    This file lives at:
      ui/services/app_paths.py

    So parents[2] is the project root:
      app_paths.py -> services -> ui -> project root
    """
    return Path(__file__).resolve().parents[2]


def runtime_root() -> Path:
    """
    Root folder for user-writable runtime files.

    Source mode:
      project root

    EXE mode:
      folder beside The Dragon's Touch.exe
    """
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
    """
    Create writable runtime folders if they do not already exist.

    Safe in source mode and EXE mode.
    """
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
    """
    Return a small status dictionary for future Settings/Data Setup UI.

    This is intentionally simple and JSON-friendly.
    """
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
        print(f"  path: {item['path']}")
        print(f"  exists: {item['exists']}")
        print(f"  size: {item['size_bytes']} bytes")
        print()
