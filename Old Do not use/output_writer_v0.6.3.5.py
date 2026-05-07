"""Output filename, folder routing, and file-writing helpers for The Dragon's Touch.

Clean.8.5 rebuild note:
- There is exactly one output routing path.
- Normal reports always go to outputs/<Deck>/normal/.
- Debug/stress-test reports always go to outputs/<Deck>/debug/.
- Existing root-level files from older runs never cause a new numbered deck folder.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import MAX_OUTPUT_FILENAME_LENGTH, MAX_OUTPUT_STEM_LENGTH


@dataclass(frozen=True)
class DeckOutputFolders:
    deck_root: Path
    normal: Path
    debug: Path


def sanitize_filename(name: object, max_length: int = 120) -> str:
    safe = str(name or "Unknown_Deck").strip()
    for ch in '<>:"/\\|?*':
        safe = safe.replace(ch, "_")
    safe = re.sub(r"\s+", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("._ ")
    if not safe:
        safe = "Unknown_Deck"
    return safe[:max_length].rstrip("._ ") or "Unknown_Deck"


def make_safe_filename(name: object) -> str:
    safe = str(name or "Unknown_Deck")
    for ch in [" ", ",", "'", '"', "/", "\\", ":", ";", "?", "!", "."]:
        safe = safe.replace(ch, "_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_") or "Unknown_Deck"


def shorten_output_stem(name: object, max_length: int = MAX_OUTPUT_STEM_LENGTH) -> str:
    return sanitize_filename(name or "Unknown_Deck", max_length=max_length) or "Unknown_Deck"


def safe_output_filename(base_name: object, extension: str = ".txt", max_length: int = MAX_OUTPUT_FILENAME_LENGTH) -> str:
    ext = extension if extension.startswith(".") else f".{extension}"
    safe_base = sanitize_filename(base_name or "output", max_length=max(12, max_length - len(ext)))
    return f"{safe_base}{ext}"


def get_unique_output_path(folder: Path | str, base_name: object, extension: str = ".txt") -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    ext = extension if extension.startswith(".") else f".{extension}"
    output_path = folder / safe_output_filename(base_name, ext)
    counter = 2
    while output_path.exists():
        suffix = f"_{counter}"
        max_base = max(12, MAX_OUTPUT_FILENAME_LENGTH - len(ext) - len(suffix))
        safe_base = sanitize_filename(base_name or "output", max_length=max_base)
        output_path = folder / f"{safe_base}{suffix}{ext}"
        counter += 1
    return output_path


def create_deck_output_folder(deck_name: object, output_root: Path | str, subfolder: str | None = None) -> Path:
    """Create/reuse a deck output folder.

    Important: this intentionally reuses outputs/<Deck_Name> even if old files are
    already sitting in that root from previous broken runs. It does not create
    <Deck_Name>_02 just because the folder is non-empty.
    """
    base = Path(output_root) / shorten_output_stem(deck_name)
    if subfolder:
        base = base / subfolder
    base.mkdir(parents=True, exist_ok=True)
    return base


def create_deck_output_folders(deck_name: object, output_root: Path | str) -> DeckOutputFolders:
    deck_root = create_deck_output_folder(deck_name, output_root)
    normal = deck_root / "normal"
    debug = deck_root / "debug"
    normal.mkdir(parents=True, exist_ok=True)
    debug.mkdir(parents=True, exist_ok=True)
    return DeckOutputFolders(deck_root=deck_root, normal=normal, debug=debug)


def write_text_file(path: Path | str, content: object) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content).rstrip() + "\n", encoding="utf-8")
    return path


def merge_debug_reports(debug_folder: Path | str, deck_name: object, debug_file_paths: Iterable[Path | str]) -> Path:
    merged_path = get_unique_output_path(Path(debug_folder), f"{shorten_output_stem(deck_name)}_full_debug_report", ".txt")
    section_titles = [
        "01 - LEGALITY REPORT",
        "02 - STRATEGY REPORT",
        "03 - BRACKET REPORT",
        "04 - CUT PRESSURE REPORT",
        "05 - REPLACEMENT PROMPT",
        "06 - DIAGNOSTICS",
    ]
    parts: list[str] = []
    for title, file_path in zip(section_titles, debug_file_paths):
        file_path = Path(file_path)
        parts.append("=" * 50)
        parts.append(title)
        parts.append("=" * 50)
        parts.append(
            file_path.read_text(encoding="utf-8")
            if file_path.exists() and file_path != merged_path
            else "[Missing debug section]"
        )
        parts.append("")
    write_text_file(merged_path, "\n".join(parts))
    return merged_path


def assert_output_routing(paths: Iterable[Path | str], normal_folder: Path | str, debug_folder: Path | str) -> None:
    normal_folder = Path(normal_folder).resolve()
    debug_folder = Path(debug_folder).resolve()
    for raw in paths:
        path = Path(raw).resolve()
        name = path.name.lower()
        is_debug = name.endswith("_debug.md") or name.endswith("_full_debug_report.txt")
        if is_debug and path.parent != debug_folder:
            raise RuntimeError(f"Debug output routed incorrectly: {path}")
        if (not is_debug) and path.parent != normal_folder:
            raise RuntimeError(f"Normal output routed incorrectly: {path}")
