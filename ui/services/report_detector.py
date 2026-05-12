"""Report output detection helpers for The Dragon's Touch desktop UI.

This module is intentionally narrow: it parses backend stdout for generated
report paths and derives folders/categories for the UI to display. It does not
read report contents, move files, run main.py, or perform deck analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


NOT_DETECTED = "Not detected"


@dataclass
class ReportDetectionResult:
    """Pure detection result for a guarded backend run."""

    output_files: List[str] = field(default_factory=list)
    normal_report_files: List[str] = field(default_factory=list)
    debug_report_files: List[str] = field(default_factory=list)
    output_folder: str = NOT_DETECTED
    normal_report_folder: str = NOT_DETECTED
    debug_report_folder: str = NOT_DETECTED
    original_output_folder: str = NOT_DETECTED
    backend_unique_output_status: str = "No backend unique output detection attempted yet."
    status: str = "No guarded run report output detected yet."
    mode: str = "not_attempted"
    warning: str = "No report detection warning."
    expected_normal: bool = True
    expected_debug: bool = True


def resolve_backend_output_path(raw_path: str, backend_working_directory: str) -> Optional[Path]:
    """Resolve a backend printed path relative to the guarded run working directory."""
    cleaned = (raw_path or "").strip().strip('"').strip("'")
    if not cleaned:
        return None
    normalized = cleaned.replace("\\", "/")
    path = Path(normalized)
    if not path.is_absolute():
        path = Path(backend_working_directory) / path
    return path


def expected_report_categories(output_mode: str) -> Tuple[bool, bool]:
    """Describe which report categories are expected based on the staged Output Mode."""
    mode = (output_mode or "").lower()
    expect_normal = "normal" in mode or "both" in mode
    expect_debug = "debug" in mode or "stress" in mode or "both" in mode
    if not expect_normal and not expect_debug:
        # Be conservative for any future custom wording.
        expect_normal = True
    return expect_normal, expect_debug


def path_contains_folder(path_text: str, folder_name: str) -> bool:
    """Return True if a path contains the given folder name as a path part."""
    try:
        return folder_name.lower() in [part.lower() for part in Path(path_text).parts]
    except Exception:
        return False


def derive_output_folder_from_detected_files(detected_files: Iterable[str]) -> str:
    """Infer the deck output root from detected backend files without reading report contents."""
    for path_text in detected_files:
        path = Path(path_text)
        parts_lower = [part.lower() for part in path.parts]
        if "outputs" in parts_lower:
            idx = parts_lower.index("outputs")
            if len(path.parts) > idx + 1:
                return str(Path(*path.parts[:idx + 2]))
        parent = path.parent
        if parent.name.lower() in {"normal", "debug"}:
            return str(parent.parent)
    return NOT_DETECTED


def normalize_detected_output_files(detected_files: Iterable[str]) -> Tuple[List[str], str]:
    """Return detected files unchanged and report backend-unique-output status.

    This preserves the v0.6.7.9.17+ behavior where the backend writes directly
    into a unique, deck-file-distinguished run folder. The UI must not move
    report contents.
    """
    detected = [str(Path(path)) for path in (detected_files or [])]
    if not detected:
        return [], "No files detected; backend unique output status was not evaluated."
    return detected, (
        "Skipped: backend now writes directly to a unique deck-file-distinguished run folder; "
        "UI relocation is no longer needed."
    )


def extract_files_written_paths(stdout_text: str, backend_working_directory: str) -> List[str]:
    """Return backend file paths printed under the Files written block.

    This function parses stdout only. It does not read files.
    """
    lines = (stdout_text or "").splitlines()
    in_files_block = False
    detected: List[str] = []
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower().rstrip(":")
        if lower == "files written" or lower.endswith("files written") or stripped.lower().startswith("files written"):
            in_files_block = True
            continue
        if not in_files_block:
            continue
        if not stripped:
            continue
        bullet = None
        for prefix in ("- ", "• ", "* "):
            if stripped.startswith(prefix):
                bullet = stripped[len(prefix):].strip()
                break
        if bullet is None:
            if detected:
                break
            continue
        resolved = resolve_backend_output_path(bullet, backend_working_directory)
        if resolved is not None:
            suffix = resolved.suffix.lower()
            if suffix in {".md", ".txt", ".markdown", ".log"}:
                resolved_text = str(resolved)
                if resolved_text not in detected:
                    detected.append(resolved_text)
    return detected


def detect_report_outputs(stdout_text: str, output_mode: str, backend_working_directory: str) -> ReportDetectionResult:
    """Parse report paths from stdout and return hardened status messaging."""
    result = ReportDetectionResult()
    detected = extract_files_written_paths(stdout_text, backend_working_directory)
    detected, unique_status = normalize_detected_output_files(detected)
    result.backend_unique_output_status = unique_status
    result.output_files = detected
    result.normal_report_files = [p for p in detected if path_contains_folder(p, "normal")]
    result.debug_report_files = [p for p in detected if path_contains_folder(p, "debug")]

    if detected:
        result.output_folder = derive_output_folder_from_detected_files(detected)
    if result.normal_report_files:
        result.normal_report_folder = str(Path(result.normal_report_files[0]).parent)
    if result.debug_report_files:
        result.debug_report_folder = str(Path(result.debug_report_files[0]).parent)

    expect_normal, expect_debug = expected_report_categories(output_mode)
    result.expected_normal = expect_normal
    result.expected_debug = expect_debug

    warnings: List[str] = []
    if expect_normal and not result.normal_report_files:
        warnings.append("expected normal report output for current Output Mode, but none was detected")
    if expect_debug and not result.debug_report_files:
        warnings.append("expected debug report output for current Output Mode, but none was detected")
    if detected and result.output_folder == NOT_DETECTED:
        warnings.append("files were detected, but output folder root could not be inferred")

    if detected:
        result.mode = "stdout_files_written_block"
        result.status = (
            f"Detected {len(detected)} output file(s): "
            f"{len(result.normal_report_files)} normal, "
            f"{len(result.debug_report_files)} debug."
        )
    else:
        result.mode = "no_files_written_block_detected"
        result.status = (
            "No report paths detected from guarded-run stdout. "
            "If the backend completed successfully, check the CLI output folder manually."
        )
        warnings.append("no Files written block or report path bullets were detected")

    result.warning = "; ".join(warnings) if warnings else "No report detection warnings."
    return result


def folder_path_is_openable(folder_path: str) -> bool:
    """Return True only when a detected folder path exists locally."""
    path_text = folder_path or NOT_DETECTED
    if path_text == NOT_DETECTED:
        return False
    path = Path(path_text)
    return path.exists() and path.is_dir()
