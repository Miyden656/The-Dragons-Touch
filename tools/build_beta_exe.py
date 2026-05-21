# v0.11.9.2.1: desktop_ui_launcher.py is the EXE entrypoint; main.py remains backend runtime source.
#!/usr/bin/env python3
"""
v0.11.1.5-dev — PyInstaller Docs Staging Cleanup for The Dragon's Touch.

Purpose:
- Build the beta EXE from a clean staging folder.
- Do not bundle the full docs folder into _internal.
- Keep dev docs, alpha docs, tester feedback, and combo tester docs out of the EXE package.
- Keep only README_FIRST.txt beside the EXE root.
- Preserve the apostrophe-safe final app name:
    The Dragon's Touch.exe

Build output:
    dist/The Dragon's Touch/The Dragon's Touch.exe
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DISPLAY_APP_NAME = "The Dragon's Touch"
PYINSTALLER_APP_NAME = "The Dragons Touch"

ENTRY_SCRIPT = PROJECT_ROOT / "desktop_ui_launcher.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_DIR = PROJECT_ROOT / "build_specs"
STAGING_DIR = BUILD_DIR / "tdt_pyinstaller_staging"
SPEC_FILE = SPEC_DIR / f"{PYINSTALLER_APP_NAME}.spec"

SAFE_BUILD_FOLDER = DIST_DIR / PYINSTALLER_APP_NAME
FINAL_BUILD_FOLDER = DIST_DIR / DISPLAY_APP_NAME
FINAL_EXE_PATH = FINAL_BUILD_FOLDER / f"{DISPLAY_APP_NAME}.exe"


HEAVY_OR_PRIVATE_RUNTIME_PATHS = {
    "data/combo.json",
    "data/scryfall_oracle_cards.json",
    "data/commander_spellbook/combo.json",
    "data/commander_spellbook/combo_index.json",
    "data/commander_spellbook/combo_index_parity.json",
    "Outputs",
    "Retired UI",
    "Old Do Not Use",
    "__pycache__",
}

# Keep this deliberately small.
# Do not stage the full docs folder for the EXE bundle.
STAGED_DATA_FOLDERS = [
    "ui",
    "combo_awareness",
]

RUNTIME_FOLDERS_BESIDE_EXE = [
    "data",
    "data/commander_spellbook",
    "Decklists",
    "collection",
    "Outputs",
    "settings",
]


def normalize_rel(path: Path) -> str:
    return path.as_posix()


def should_exclude_from_staging(path: Path) -> bool:
    """Return True if this source path should not be copied into staging."""
    try:
        rel = path.relative_to(PROJECT_ROOT)
    except ValueError:
        return True

    rel_posix = normalize_rel(rel)
    parts = {part.lower() for part in rel.parts}

    if "__pycache__" in parts:
        return True

    if path.suffix.lower() in {".pyc", ".pyo"}:
        return True

    lowered = rel_posix.lower()

    excluded_exact = {
        item.lower()
        for item in HEAVY_OR_PRIVATE_RUNTIME_PATHS
        if "." in Path(item).name
    }
    if lowered in excluded_exact:
        return True

    excluded_roots = {
        item.lower()
        for item in HEAVY_OR_PRIVATE_RUNTIME_PATHS
        if "." not in Path(item).name
    }
    if rel.parts and rel.parts[0].lower() in excluded_roots:
        return True

    if "mockup" in lowered:
        return True

    return False


def copy_tree_clean(source: Path, destination: Path) -> None:
    if not source.exists():
        return

    if destination.exists():
        shutil.rmtree(destination)

    for item in source.rglob("*"):
        if should_exclude_from_staging(item):
            continue

        rel = item.relative_to(source)
        target = destination / rel

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def prepare_clean_staging() -> None:
    if STAGING_DIR.exists():
        print(f"Removing old staging folder: {STAGING_DIR}")
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    for folder_name in STAGED_DATA_FOLDERS:
        source = PROJECT_ROOT / folder_name
        destination = STAGING_DIR / folder_name
        print(f"Staging clean folder: {folder_name}")
        copy_tree_clean(source, destination)

    # Create empty runtime folder placeholders in staging if later code expects them as data.
    # Do not copy user/private contents into these folders.
    for folder_name in ["data", "data/commander_spellbook", "Decklists", "collection", "settings"]:
        path = STAGING_DIR / folder_name
        path.mkdir(parents=True, exist_ok=True)


def run_command(command: list[str], *, cwd: Path) -> int:
    print()
    print("Running:")
    print(" ".join(command))
    print()

    completed = subprocess.run(command, cwd=str(cwd))
    return int(completed.returncode)


def pyinstaller_available() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--version"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0


def ensure_pyinstaller_available() -> None:
    if pyinstaller_available():
        return

    raise RuntimeError(
        "PyInstaller is not installed in this Python environment.\n\n"
        "Install it with:\n"
        "  py -m pip install pyinstaller\n\n"
        "Then rerun:\n"
        "  py tools\\build_beta_exe.py --console"
    )


def clean_build_outputs() -> None:
    """Clean only generated PyInstaller build outputs."""
    paths_to_remove = [
        SAFE_BUILD_FOLDER,
        FINAL_BUILD_FOLDER,
        BUILD_DIR / PYINSTALLER_APP_NAME,
        BUILD_DIR / DISPLAY_APP_NAME,
        STAGING_DIR,
        SPEC_FILE,
        SPEC_DIR / f"{DISPLAY_APP_NAME}.spec",
    ]

    for path in paths_to_remove:
        if path.exists():
            if path.is_dir():
                print(f"Removing folder: {path}")
                shutil.rmtree(path)
            else:
                print(f"Removing file: {path}")
                path.unlink()


def make_source_runtime_folders() -> None:
    expected_dirs = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "commander_spellbook",
        PROJECT_ROOT / "Decklists",
        PROJECT_ROOT / "collection",
        PROJECT_ROOT / "Outputs",
        PROJECT_ROOT / "settings",
    ]

    for path in expected_dirs:
        path.mkdir(parents=True, exist_ok=True)


def make_exe_runtime_folders() -> None:
    for folder_name in RUNTIME_FOLDERS_BESIDE_EXE:
        (FINAL_BUILD_FOLDER / folder_name).mkdir(parents=True, exist_ok=True)


def write_beta_readme() -> None:
    text = """The Dragon's Touch — v0.11 Beta EXE Proof

This is an early beta EXE build.

Runtime folders beside this EXE:
- data/
- data/commander_spellbook/
- Decklists/
- collection/
- Outputs/
- settings/

Large runtime data is not bundled:
- data/combo.json
- data/scryfall_oracle_cards.json
- data/commander_spellbook/combo_index.json
- data/commander_spellbook/combo_index_parity.json

Development docs, alpha notes, tester feedback, and internal combo tester notes are not bundled in _internal.

Those data files will be downloaded/generated through later v0.11 data setup work.
"""
    (FINAL_BUILD_FOLDER / "README_FIRST.txt").write_text(text, encoding="utf-8")


def rename_safe_build_to_display_name() -> None:
    if not SAFE_BUILD_FOLDER.exists():
        raise FileNotFoundError(f"Expected PyInstaller output folder not found: {SAFE_BUILD_FOLDER}")

    if FINAL_BUILD_FOLDER.exists():
        shutil.rmtree(FINAL_BUILD_FOLDER)

    SAFE_BUILD_FOLDER.rename(FINAL_BUILD_FOLDER)

    safe_exe_after_folder_rename = FINAL_BUILD_FOLDER / f"{PYINSTALLER_APP_NAME}.exe"
    if safe_exe_after_folder_rename.exists():
        safe_exe_after_folder_rename.rename(FINAL_EXE_PATH)


def build_pyinstaller_command(*, windowed: bool, clean: bool) -> list[str]:
    stage_runtime_tool_files(STAGING_DIR, PROJECT_ROOT)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        PYINSTALLER_APP_NAME,
        "--onedir",
        "--noconfirm",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(SPEC_DIR),
    ]

    if clean:
        command.append("--clean")

    if windowed:
        command.append("--windowed")

    separator = ";" if sys.platform.startswith("win") else ":"

    add_data_pairs = [
        (STAGING_DIR / "ui", "ui"),
        (STAGING_DIR / "combo_awareness", "combo_awareness"),
        (STAGING_DIR / "data", "data"),
        (STAGING_DIR / "Decklists", "Decklists"),
        (STAGING_DIR / "collection", "collection"),
        (STAGING_DIR / "settings", "settings"),
    ]

    for source_path, dest in add_data_pairs:
        if source_path.exists():
            command.extend(["--add-data", f"{source_path}{separator}{dest}"])

    excludes = [
        "pytest",
        "unittest",
        "tkinter.test",
        "numpy",
        "pandas",
        "matplotlib",
    ]
    for module_name in excludes:
        command.extend(["--exclude-module", module_name])

    command.extend(["--collect-all", "PySide6"])
    command.extend(["--hidden-import", "PySide6"])
    command.extend(["--hidden-import", "PySide6.QtCore"])
    command.extend(["--hidden-import", "PySide6.QtGui"])
    command.extend(["--hidden-import", "PySide6.QtWidgets"])
    command.append(str(ENTRY_SCRIPT))
    return command


def verify_project_ready() -> None:
    if not ENTRY_SCRIPT.exists():
        raise FileNotFoundError(f"Entry script not found: {ENTRY_SCRIPT}")

    required_paths = [
        PROJECT_ROOT / "ui" / "dragons_touch_pyside6_workstation.py",
        PROJECT_ROOT / "ui" / "constants.py",
        PROJECT_ROOT / "combo_awareness" / "main_hook.py",
        PROJECT_ROOT / "combo_awareness" / "reporting.py",
        PROJECT_ROOT / "tools" / "download_commander_spellbook_bulk_json.py",
        PROJECT_ROOT / "tools" / "build_combo_index.py",
    ]

    missing = [path for path in required_paths if not path.exists()]
    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing required project files:\n{missing_text}")


# v0.11.9.2.3: stage build_combo_index.py for EXE runtime.
def stage_runtime_tool_files(staging_dir, project_root):
    """Copy runtime tool scripts needed by the packaged EXE."""
    from pathlib import Path
    import shutil

    staging_dir = Path(staging_dir)
    project_root = Path(project_root)

    runtime_tools_dir = staging_dir / "tools"
    runtime_tools_dir.mkdir(parents=True, exist_ok=True)

    required_tools = [
        "build_combo_index.py",
    ]

    for tool_name in required_tools:
        source = project_root / "tools" / tool_name
        destination = runtime_tools_dir / tool_name
        if source.exists():
            shutil.copy2(source, destination)

def main() -> int:
    parser = argparse.ArgumentParser(description="Build The Dragon's Touch beta EXE using PyInstaller.")

    parser.add_argument(
        "--console",
        action="store_true",
        help="Build with console visible. Useful for debugging first EXE launch issues.",
    )

    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not pass --clean to PyInstaller.",
    )

    parser.add_argument(
        "--skip-pyinstaller-check",
        action="store_true",
        help="Skip the PyInstaller availability check.",
    )

    args = parser.parse_args()

    print("v0.11.1.5-dev — PyInstaller Docs Staging Cleanup")
    print("===============================================")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Entry script: {ENTRY_SCRIPT}")
    print(f"Internal PyInstaller name: {PYINSTALLER_APP_NAME}")
    print(f"Final display name: {DISPLAY_APP_NAME}")
    print(f"Staging folder: {STAGING_DIR}")
    print(f"Target folder: {FINAL_BUILD_FOLDER}")
    print(f"Target EXE: {FINAL_EXE_PATH}")
    print()

    try:
        verify_project_ready()
        make_source_runtime_folders()

        if not args.skip_pyinstaller_check:
            ensure_pyinstaller_available()

        clean_build_outputs()
        prepare_clean_staging()

        command = build_pyinstaller_command(
            windowed=not args.console,
            clean=not args.no_clean,
        )

        return_code = run_command(command, cwd=PROJECT_ROOT)
        if return_code != 0:
            print()
            print(f"PyInstaller failed with exit code {return_code}.")
            return return_code

        rename_safe_build_to_display_name()
        make_exe_runtime_folders()
        write_beta_readme()

        if FINAL_EXE_PATH.exists():
            print()
            print("Build complete.")
            print(f"EXE: {FINAL_EXE_PATH}")
            return 0

        print()
        print("Build completed, but expected EXE was not found.")
        print(f"Expected: {FINAL_EXE_PATH}")
        return 2

    except Exception as exc:
        print()
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
