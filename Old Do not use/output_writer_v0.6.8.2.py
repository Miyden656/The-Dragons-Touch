"""Output filename, folder routing, and file-writing helpers for The Dragon's Touch.

Patch Batch 8 note:
- There is exactly one output routing path.
- Normal reports always go to outputs/<Deck_File_Distinguished_Run>/normal/.
- Debug/stress-test reports always go to outputs/<Deck_File_Distinguished_Run>/debug/.
- Every backend run gets a unique timestamped output folder.
- Output folder names preserve commander identity, source deck-file distinction, and run timestamp.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
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


def run_folder_name_part(name: object, max_length: int = MAX_OUTPUT_STEM_LENGTH) -> str:
    """Return a readable folder-name segment for timestamped run folders."""
    part = shorten_output_stem(name or "Unknown_Deck", max_length=max_length)
    part = re.sub(r"[,.']+", "_", part)
    part = re.sub(r"_+", "_", part).strip("._ ")
    return part[:max_length].rstrip("._ ") or "Unknown_Deck"


def make_batch_output_deck_name(commander_name: object, deck_file: Path | str | None = None) -> str:
    """Return a batch-safe deck folder name.

    Single-deck mode should keep the clean commander-only folder name. In batch
    mode, two different files can share the same commander, so include the
    source deck file stem to prevent the second deck's reports from landing in
    the first deck's folder.

    The stem is intentionally preserved at the end of the name because test
    decks often share commander names but differ by file labels such as
    ``Companion Section`` or ``Reference Test``.
    """
    commander_part = shorten_output_stem(commander_name or "Unknown_Deck", max_length=60)
    if not deck_file:
        return commander_part

    remaining = max(20, MAX_OUTPUT_STEM_LENGTH - len(commander_part) - 2)
    file_part = run_folder_name_part(Path(deck_file).stem, max_length=remaining)
    if not file_part or file_part == commander_part:
        return commander_part
    return f"{commander_part}__{file_part}"


def safe_run_timestamp() -> str:
    """Return a filesystem-safe timestamp for one backend output run."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_run_output_deck_name(
    commander_name: object,
    deck_file: Path | str | None = None,
    *,
    timestamp: str | None = None,
) -> str:
    """Return the final per-run output folder name.

    v0.6.7.9.17 backend handoff fix:
    - preserve commander identity,
    - preserve source deck-file distinction when available,
    - add a timestamp so repeated runs of the same deck do not pile into the
      same folder or leave empty commander-shell folders for the UI to clean up.
    
    Example:
        Miirym_Sentinel_Wyrm_19_Miirym_Test_run_20260511_052140
    """
    stamp = sanitize_filename(timestamp or safe_run_timestamp(), max_length=24)
    commander_part = run_folder_name_part(commander_name or "Unknown_Deck", max_length=42)

    file_part = ""
    if deck_file:
        reserved = len(commander_part) + len(stamp) + len("__run__")
        remaining = max(18, MAX_OUTPUT_STEM_LENGTH - reserved)
        file_part = run_folder_name_part(Path(deck_file).stem, max_length=remaining)

    if file_part and file_part != commander_part:
        base = f"{commander_part}_{file_part}_run_{stamp}"
    else:
        base = f"{commander_part}_run_{stamp}"
    return run_folder_name_part(base, max_length=MAX_OUTPUT_STEM_LENGTH)


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
    """Create/reuse a specific output folder.

    Kept for compatibility with older helpers. New guarded/backend runs should
    prefer ``create_unique_run_output_folders`` with a timestamped run folder.
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


def create_unique_run_output_folders(deck_name: object, output_root: Path | str) -> DeckOutputFolders:
    """Create one unique output folder for a single backend run.

    The caller should pass a name that already includes commander/deck-file
    distinction and timestamp. A numeric suffix is added only if the timestamped
    folder already exists.
    """
    output_root = Path(output_root)
    base_name = shorten_output_stem(deck_name)
    deck_root = output_root / base_name
    counter = 2
    while deck_root.exists():
        suffix = f"_{counter}"
        max_base = max(18, MAX_OUTPUT_STEM_LENGTH - len(suffix))
        deck_root = output_root / f"{shorten_output_stem(base_name, max_length=max_base)}{suffix}"
        counter += 1

    normal = deck_root / "normal"
    debug = deck_root / "debug"
    normal.mkdir(parents=True, exist_ok=False)
    debug.mkdir(parents=True, exist_ok=False)
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


def _is_debug_output_file(path: Path) -> bool:
    """Return True for all debug output filename variants.

    Unique-path suffixes produce names like ``deck_legality_debug_2.md``. The
    older check only recognized names ending exactly in ``_debug.md``, which
    caused valid debug files in the debug folder to be misclassified as normal
    outputs during batch reruns or duplicate commander tests.
    """
    stem = path.stem.lower()
    suffix = path.suffix.lower()
    return (suffix == ".md" and (stem.endswith("_debug") or "_debug_" in stem)) or (
        suffix == ".txt" and (stem.endswith("_full_debug_report") or "_full_debug_report_" in stem)
    )


def assert_output_routing(paths: Iterable[Path | str], normal_folder: Path | str, debug_folder: Path | str) -> None:
    normal_folder = Path(normal_folder).resolve()
    debug_folder = Path(debug_folder).resolve()
    for raw in paths:
        path = Path(raw).resolve()
        is_debug = _is_debug_output_file(path)
        if is_debug and path.parent != debug_folder:
            raise RuntimeError(f"Debug output routed incorrectly: {path}")
        if (not is_debug) and path.parent != normal_folder:
            raise RuntimeError(f"Normal output routed incorrectly: {path}")
