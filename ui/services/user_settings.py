"""Persistent user settings for The Dragon's Touch desktop UI.

v0.10.5.1-dev foundation:
- This module owns app-wide preferences only.
- It must not run deck analysis, call main.py, inspect reports, or mutate deck contents.
- Review Setup still owns per-run choices.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Commander AI (v1.7.x) settings defaults live in the ai/ layer so they are
# defined exactly once. This UI-services module only persists/normalizes them.
# Importing ai.commander_ai_config pulls in NO PySide6 — it is pure stdlib.
from ai.commander_ai_config import (
    AI_SETTINGS_DEFAULTS,
    from_settings as build_commander_ai_config,
    to_settings as _commander_ai_to_settings,
)


SETTINGS_SCHEMA_VERSION = 1

USER_MODE = "User Mode"
DEVELOPER_MODE = "Developer Mode"

LEGACY_USER_MODES = {"User Mode", "User-Facing Mode", "user", "user-facing"}
LEGACY_DEVELOPER_MODES = {"Developer Mode", "Dev-Facing Mode", "dev", "developer", "dev-facing"}

GUIDE_PRESENTATION_OPTIONS = [
    "Masculine guide",
    "Feminine guide",
    "Either / random",
    "Neither / no named guide",
]

COLLECTION_SOURCE_DEFAULT_OPTIONS = [
    "Local collection folder",
    "Specific local collection files",
    "CardMill CSV/export placeholder",
    "Moxfield export placeholder",
    "Future source placeholder",
]

UI_DENSITY_OPTIONS = [
    "Comfortable",
    "Normal",
    "Compact",
]

# How the local Commander AI guide is presented on Report Viewer / Commander's Call.
COMMANDER_AI_DISPLAY_OPTIONS = [
    "Slide-in panel",
    "Embedded panel",
]


def settings_path() -> Path:
    """Return the local settings path.

    The settings file intentionally lives under ui/ for now because this app is
    still a local alpha folder. If the file is deleted, defaults are recreated.
    """
    return Path(__file__).resolve().parents[1] / "user_settings.json"


def default_settings() -> dict[str, Any]:
    return {
        "schema_version": SETTINGS_SCHEMA_VERSION,
        "interface_mode": USER_MODE,
        "guide_presentation": "Either / random",
        "collection_source_default": "Local collection folder",
        "collection_source_path": "collection",
        "collection_source_files": [],
        "report_output_folder": "Outputs",
        "theme": "Dragon Forge",
        "ui_density": "Normal",
        "commander_ai_display_mode": "Slide-in panel",
        "developer_report_viewer_last_view": "User View",
        # Commander AI (Local Ollama guide) — keys + defaults owned by ai/.
        **AI_SETTINGS_DEFAULTS,
    }


def normalize_interface_mode(value: Any) -> str:
    text = str(value or "").strip()
    if text in LEGACY_DEVELOPER_MODES:
        return DEVELOPER_MODE
    if text in LEGACY_USER_MODES:
        return USER_MODE
    return USER_MODE


def normalize_guide_presentation(value: Any) -> str:
    text = str(value or "").strip()
    legacy_map = {
        # v0.10.5.1 brief-lived names -> restored gender/random/no-guide vocabulary.
        "Adventurer Guide": "Either / random",
        "Archivist Guide": "Masculine guide",
        "Strategist Guide": "Feminine guide",
        "Minimal Guide": "Neither / no named guide",
        "No named guide, just philosophy labels": "Neither / no named guide",
        "None": "Neither / no named guide",
        "Neither": "Neither / no named guide",
        "No guide": "Neither / no named guide",
    }
    text = legacy_map.get(text, text)
    return text if text in GUIDE_PRESENTATION_OPTIONS else "Either / random"


def normalize_collection_source_default(value: Any) -> str:
    text = str(value or "").strip()
    legacy_map = {
        "Entire collection folder": "Local collection folder",
        "Select collection files": "Specific local collection files",
    }
    text = legacy_map.get(text, text)
    return text if text in COLLECTION_SOURCE_DEFAULT_OPTIONS else "Local collection folder"


def normalize_ui_density(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in UI_DENSITY_OPTIONS else "Normal"


def normalize_commander_ai_display_mode(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in COMMANDER_AI_DISPLAY_OPTIONS else "Slide-in panel"


def normalize_developer_report_view(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in {"User View", "Dev View"} else "User View"


def normalize_commander_ai_settings(data: dict[str, Any]) -> None:
    """Validate/clamp the commander_ai_* keys in-place.

    Delegates all validation to ai/ (the single source of truth) so the rules
    are never duplicated here: build a validated config, then write its
    normalized values back over the flat settings dict.
    """
    normalized = _commander_ai_to_settings(build_commander_ai_config(data))
    data.update(normalized)


def load_app_settings() -> dict[str, Any]:
    path = settings_path()
    data = default_settings()

    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:
            # Preserve a broken settings file for user inspection and fall back safely.
            try:
                broken_path = path.with_suffix(".broken.json")
                path.replace(broken_path)
            except Exception:
                pass

    data["schema_version"] = SETTINGS_SCHEMA_VERSION
    data["interface_mode"] = normalize_interface_mode(data.get("interface_mode"))
    data["guide_presentation"] = normalize_guide_presentation(data.get("guide_presentation"))
    data["collection_source_default"] = normalize_collection_source_default(data.get("collection_source_default"))
    data["collection_source_path"] = str(data.get("collection_source_path") or "collection")
    files = data.get("collection_source_files")
    data["collection_source_files"] = files if isinstance(files, list) else []
    data["report_output_folder"] = str(data.get("report_output_folder") or "Outputs")
    data["theme"] = str(data.get("theme") or "Dragon Forge")
    data["ui_density"] = normalize_ui_density(data.get("ui_density"))
    data["commander_ai_display_mode"] = normalize_commander_ai_display_mode(data.get("commander_ai_display_mode"))
    data["developer_report_viewer_last_view"] = normalize_developer_report_view(data.get("developer_report_viewer_last_view"))
    normalize_commander_ai_settings(data)

    save_app_settings(data)
    return data


def save_app_settings(data: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    cleaned = default_settings()
    cleaned.update(data or {})
    cleaned["schema_version"] = SETTINGS_SCHEMA_VERSION
    cleaned["interface_mode"] = normalize_interface_mode(cleaned.get("interface_mode"))
    cleaned["guide_presentation"] = normalize_guide_presentation(cleaned.get("guide_presentation"))
    cleaned["collection_source_default"] = normalize_collection_source_default(cleaned.get("collection_source_default"))
    cleaned["ui_density"] = normalize_ui_density(cleaned.get("ui_density"))
    cleaned["commander_ai_display_mode"] = normalize_commander_ai_display_mode(cleaned.get("commander_ai_display_mode"))
    cleaned["developer_report_viewer_last_view"] = normalize_developer_report_view(cleaned.get("developer_report_viewer_last_view"))
    normalize_commander_ai_settings(cleaned)

    path.write_text(json.dumps(cleaned, indent=2, sort_keys=True), encoding="utf-8")


def reset_app_settings() -> dict[str, Any]:
    data = default_settings()
    save_app_settings(data)
    return data


def apply_settings_to_state(state: Any, data: dict[str, Any], dragon_forge_theme: dict, adventurers_map_theme: dict) -> None:
    """Apply persisted settings to the in-memory AppState.

    This intentionally applies app-wide defaults only.
    """
    mode = normalize_interface_mode(data.get("interface_mode"))
    state.interface_mode = mode

    state.guide_presentation = normalize_guide_presentation(data.get("guide_presentation"))

    collection_default = normalize_collection_source_default(data.get("collection_source_default"))
    if collection_default == "Specific local collection files":
        state.collection_source_mode = "Select collection files"
    else:
        state.collection_source_mode = "Entire collection folder"

    state.collection_folder = str(data.get("collection_source_path") or "collection")
    files = data.get("collection_source_files")
    state.selected_collection_files = files if isinstance(files, list) else []

    # Keep old collection source preview counts honest.
    try:
        if state.collection_source_mode == "Select collection files":
            state.collection_txt_file_count = len(state.selected_collection_files)
        else:
            state.collection_txt_file_count = len(list(Path(state.collection_folder).glob("*.txt")))
    except Exception:
        state.collection_txt_file_count = 0

    state.report_output_folder = str(data.get("report_output_folder") or "Outputs")
    state.ui_density = normalize_ui_density(data.get("ui_density"))
    state.developer_report_viewer_last_view = normalize_developer_report_view(data.get("developer_report_viewer_last_view"))

    theme_name = str(data.get("theme") or "Dragon Forge")
    state.theme = adventurers_map_theme if theme_name == "Adventurer's Map" else dragon_forge_theme
