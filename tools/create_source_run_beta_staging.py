#!/usr/bin/env python3
"""Create a clean source-run beta staging folder for The Dragon's Touch.

This helper copies only active source-run handoff files/folders into a clean
staging directory so package verification does not scan historical development
archives such as Retired UI, Old Do Not Use, exe tests, dist, or build.

No network calls. No app launch. No analysis run.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REQUIRED_FILES = [
    "requirements.txt",
    "README_START_HERE.txt",
    "README.md",
    "desktop_ui_launcher.py",
    "main.py",
    "config.py",
]

ACTIVE_FOLDERS = [
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
    "docs",
]

FORBIDDEN_DIR_NAMES = {
    "__pycache__",
    "dist",
    "build",
    "build_specs",
    "_internal",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
}

FORBIDDEN_TOP_LEVEL_NAMES = {
    "Retired UI",
    "Old Do Not Use",
    "Old do not use",
    "Old Do not use",
    "Old",
    "MockUP",
    "Mockups",
    "Mockups Do Not Use",
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


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: Path, source_root: Path) -> tuple[bool, str]:
    rel = rel_posix(path, source_root)
    parts = path.relative_to(source_root).parts

    if parts and parts[0] in FORBIDDEN_TOP_LEVEL_NAMES:
        return True, f"archived top-level folder: {parts[0]}"
    if any(part in FORBIDDEN_DIR_NAMES for part in parts):
        return True, "cache/build/internal folder"
    if any("mockup" in part.lower() for part in parts):
        return True, "MockUP/old handoff item"
    if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True, f"forbidden file type: {path.suffix}"
    if rel in KNOWN_HUGE_DATA_FILES:
        return True, "generated/downloaded data rebuilt by tester"
    return False, ""


def copy_tree_filtered(src: Path, dst: Path, source_root: Path) -> tuple[int, int]:
    copied = 0
    skipped = 0
    if not src.exists():
        dst.mkdir(parents=True, exist_ok=True)
        return copied, skipped

    for item in src.rglob("*"):
        skip, _reason = should_skip(item, source_root)
        if skip:
            skipped += 1
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied += 1
    dst.mkdir(parents=True, exist_ok=True)
    return copied, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean source-run beta staging folder.")
    parser.add_argument("--source", default=".", help="Project root to copy from. Default: current folder.")
    parser.add_argument(
        "--dest",
        default="_handoff_staging/The Dragon's Touch v0.12 Source-Run Beta",
        help="Destination staging folder. Default: _handoff_staging/The Dragon's Touch v0.12 Source-Run Beta",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace the destination if it already exists.")
    args = parser.parse_args()

    source_root = Path(args.source).resolve()
    dest_root = Path(args.dest)
    if not dest_root.is_absolute():
        dest_root = (source_root / dest_root).resolve()

    print("The Dragon's Touch — Clean Source-Run Beta Staging Helper")
    print("=========================================================")
    print(f"Source:      {source_root}")
    print(f"Destination: {dest_root}")

    if not source_root.exists():
        print("FAIL — Source folder does not exist.")
        return 1

    if dest_root.exists():
        if not args.overwrite:
            print("FAIL — Destination already exists.")
            print("Run again with --overwrite if you want to replace only the staging folder.")
            return 1
        try:
            dest_root.relative_to(source_root / "_handoff_staging")
        except ValueError:
            print("FAIL — Refusing to overwrite a destination outside _handoff_staging.")
            return 1
        shutil.rmtree(dest_root)

    dest_root.mkdir(parents=True, exist_ok=True)

    blockers = 0
    copied_files = 0
    skipped_items = 0

    for filename in REQUIRED_FILES:
        src = source_root / filename
        dst = dest_root / filename
        if src.exists() and src.is_file():
            shutil.copy2(src, dst)
            copied_files += 1
            print(f"PASS — Copied {filename}")
        else:
            blockers += 1
            print(f"FAIL — Required file missing: {filename}")

    for folder in ACTIVE_FOLDERS:
        src = source_root / folder
        dst = dest_root / folder
        c, s = copy_tree_filtered(src, dst, source_root)
        copied_files += c
        skipped_items += s
        if src.exists():
            print(f"PASS — Copied active folder: {folder} ({c} file(s), {s} skipped item(s))")
        else:
            print(f"WARN — Active folder not found, created empty folder: {folder}")

    print()
    print("Result")
    print("------")
    if blockers:
        print(f"RESULT — FAIL ({blockers} blocker issue(s))")
        return 1

    print(f"RESULT — PASS — Clean staging folder created with {copied_files} copied file(s).")
    print()
    print("Next commands:")
    print(f"cd \"{dest_root}\"")
    print("py tools\\verify_source_run_beta_package.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
