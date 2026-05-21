#!/usr/bin/env python3
"""Clean source-run beta package verifier for The Dragon's Touch.

Run this from the clean handoff/staging folder, not from the full development
archive root. If you keep historical folders, first run:

    py tools\create_source_run_beta_staging.py --overwrite

Then cd into the staging folder and run this verifier there.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_FILES = [
    "requirements.txt",
    "README_START_HERE.txt",
    "README.md",
    "desktop_ui_launcher.py",
    "main.py",
    "config.py",
]

REQUIRED_FOLDERS = [
    "ui",
    "combo_awareness",
    "analysis",
    "app_io",
    "cuts",
    "data",
    "io",
    "legality",
    "parsing",
    "replacements",
    "reports",
    "rules",
    "Decklists",
    "collection",
    "Outputs",
    "settings",
    "tools",
]

REQUIRED_TOOLS = [
    "tools/data_setup.py",
    "tools/build_combo_index.py",
    "tools/download_commander_spellbook_bulk_json.py",
    "tools/check_source_run_environment.py",
]

FORBIDDEN_DIR_NAMES = {
    "__pycache__",
    "dist",
    "build",
    "build_specs",
    "_internal",
}

FORBIDDEN_TOP_LEVEL_NAMES = {
    "Retired UI",
    "Old Do Not Use",
    "Old do not use",
    "Old Do not use",
    "MockUP",
    "Mockups",
    "exe tests",
    "EXE tests",
    "Files outside",
}

FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".exe", ".bat"}
KNOWN_HUGE_DATA_FILES = {
    "data/scryfall_cards.json",
    "data/combo.json",
    "data/commander_spellbook/combo_index.json",
    "data/commander_spellbook/combo_index_parity.json",
}
LARGE_FILE_WARN_BYTES = 100 * 1024 * 1024


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a clean source-run beta handoff package.")
    parser.add_argument("--root", default=".", help="Package root to verify. Default: current folder.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    blockers: list[str] = []
    warnings: list[str] = []

    print("The Dragon's Touch — Source-Run Beta Package Verifier")
    print("=====================================================")
    print(f"Package root: {root}")
    print()

    if not root.exists():
        print("RESULT — FAIL")
        print("Package root does not exist.")
        return 1

    print("Required files")
    print("--------------")
    for rel in REQUIRED_FILES:
        path = root / rel
        if path.is_file():
            print(f"PASS — Required file found: {rel}")
        else:
            msg = f"Required file missing: {rel}"
            blockers.append(msg)
            print(f"FAIL — {msg}")

    print()
    print("Required folders")
    print("----------------")
    for rel in REQUIRED_FOLDERS:
        path = root / rel
        if path.is_dir():
            print(f"PASS — Required folder found: {rel}/")
        else:
            msg = f"Required folder missing: {rel}/"
            blockers.append(msg)
            print(f"FAIL — {msg}")

    print()
    print("Required tools")
    print("--------------")
    for rel in REQUIRED_TOOLS:
        path = root / rel
        if path.is_file():
            print(f"PASS — Required tool found: {rel}")
        else:
            msg = f"Required tool missing: {rel}"
            blockers.append(msg)
            print(f"FAIL — {msg}")

    print()
    print("Forbidden handoff artifacts")
    print("---------------------------")
    forbidden_count = 0
    for item in root.rglob("*"):
        rel = rel_posix(item, root)
        parts = item.relative_to(root).parts

        if parts and parts[0] in FORBIDDEN_TOP_LEVEL_NAMES:
            msg = f"Forbidden archived/development folder found in package: {parts[0]}/"
            if msg not in blockers:
                blockers.append(msg)
                print(f"FAIL — {msg}")
                forbidden_count += 1
            continue

        if item.is_dir() and item.name in FORBIDDEN_DIR_NAMES:
            msg = f"Forbidden folder found: {rel}/"
            blockers.append(msg)
            print(f"FAIL — {msg}")
            forbidden_count += 1
            continue

        if any("mockup" in part.lower() for part in parts):
            msg = f"Forbidden MockUP/old handoff style file or folder found: {rel}"
            blockers.append(msg)
            print(f"FAIL — {msg}")
            forbidden_count += 1
            continue

        if item.is_file():
            if item.suffix.lower() in FORBIDDEN_SUFFIXES:
                msg = f"Forbidden file type found: {rel}"
                blockers.append(msg)
                print(f"FAIL — {msg}")
                forbidden_count += 1
            if rel in KNOWN_HUGE_DATA_FILES:
                msg = f"Huge generated data file should not be bundled in clean source-run handoff: {rel}"
                blockers.append(msg)
                print(f"FAIL — {msg}")
                forbidden_count += 1
            elif item.stat().st_size >= LARGE_FILE_WARN_BYTES:
                size_mb = item.stat().st_size / (1024 * 1024)
                msg = f"Large file found; confirm it belongs in the handoff: {rel} ({size_mb:.1f} MB)"
                warnings.append(msg)
                print(f"WARN — {msg}")

    if forbidden_count == 0:
        print("PASS — No forbidden handoff artifacts found")

    print()
    print("Expected absences")
    print("-----------------")
    for rel in sorted(KNOWN_HUGE_DATA_FILES):
        if not (root / rel).exists():
            print(f"PASS — Expected generated data is absent: {rel}")

    print()
    print("Result")
    print("------")
    if blockers:
        print(f"RESULT — FAIL ({len(blockers)} blocker issue(s), {len(warnings)} warning(s))")
        print("Fix blocker items before creating a beta handoff ZIP.")
        print()
        print("If these blockers are only from historical folders, run:")
        print("py tools\\create_source_run_beta_staging.py --overwrite")
        print("Then cd into the staging folder and run this verifier again.")
        return 1

    if warnings:
        print(f"RESULT — PASS WITH WARNINGS ({len(warnings)} warning(s))")
        print("Review warnings before handoff.")
        return 0

    print("RESULT — PASS")
    print("Clean source-run beta handoff package is ready for ZIP creation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
