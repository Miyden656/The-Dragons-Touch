#!/usr/bin/env python3
"""
v0.11.9.2.6-dev — EXE Runtime Data Seeding / Repair Test Helper.

Purpose:
- Dev-only helper for technical EXE runtime-path testing.
- Copies known-good source runtime data into the built EXE runtime data folder.
- Useful when Smart App Control blocks the EXE from performing Settings -> Data Setup downloads.

This does NOT bundle heavy data into the source package.
It only copies local files that already exist on the developer machine.

Default source files:
  data/scryfall_cards.json
  data/combo.json
  data/commander_spellbook/combo_index.json
  data/commander_spellbook/combo_index_parity.json optional

Default destination:
  dist/The Dragon's Touch/data/
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE_ROOT = ROOT / "dist" / "The Dragon's Touch"


@dataclass(frozen=True)
class SeedFile:
    label: str
    source: Path
    destination: Path
    required: bool
    minimum_size: int


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def format_size(size: int) -> str:
    if size >= 1_000_000_000:
        return f"{size / 1_000_000_000:.2f} GB"
    if size >= 1_000_000:
        return f"{size / 1_000_000:.2f} MB"
    if size >= 1_000:
        return f"{size / 1_000:.2f} KB"
    return f"{size} bytes"


def build_seed_plan(exe_root: Path) -> list[SeedFile]:
    source_data = ROOT / "data"
    destination_data = exe_root / "data"

    return [
        SeedFile(
            label="Scryfall card data",
            source=source_data / "scryfall_cards.json",
            destination=destination_data / "scryfall_cards.json",
            required=True,
            minimum_size=10_000_000,
        ),
        SeedFile(
            label="Commander Spellbook combo bulk data",
            source=source_data / "combo.json",
            destination=destination_data / "combo.json",
            required=True,
            minimum_size=10_000_000,
        ),
        SeedFile(
            label="Normal combo index",
            source=source_data / "commander_spellbook" / "combo_index.json",
            destination=destination_data / "commander_spellbook" / "combo_index.json",
            required=True,
            minimum_size=1_000_000,
        ),
        SeedFile(
            label="Parity combo index",
            source=source_data / "commander_spellbook" / "combo_index_parity.json",
            destination=destination_data / "commander_spellbook" / "combo_index_parity.json",
            required=False,
            minimum_size=1_000_000,
        ),
    ]


def print_plan(plan: list[SeedFile]) -> None:
    print("Seed plan:")
    for item in plan:
        source_exists = item.source.exists()
        destination_exists = item.destination.exists()
        source_size = file_size(item.source)
        destination_size = file_size(item.destination)

        requirement = "required" if item.required else "optional"
        print(f"- {item.label} ({requirement})")
        print(f"  source:      {item.source}")
        print(f"  source ok:   {source_exists} ({format_size(source_size)})")
        print(f"  destination: {item.destination}")
        print(f"  dest exists: {destination_exists} ({format_size(destination_size)})")


def validate_sources(plan: list[SeedFile]) -> int:
    failed = 0

    for item in plan:
        if not item.source.exists():
            if item.required:
                print(f"FAIL — Missing required source file for {item.label}: {item.source}")
                failed += 1
            else:
                print(f"NOTE — Optional source file missing for {item.label}: {item.source}")
            continue

        size = file_size(item.source)
        if size < item.minimum_size:
            if item.required:
                print(
                    f"FAIL — Required source file for {item.label} looks too small: "
                    f"{item.source} ({format_size(size)})"
                )
                failed += 1
            else:
                print(
                    f"NOTE — Optional source file for {item.label} looks small: "
                    f"{item.source} ({format_size(size)})"
                )
        else:
            print(f"PASS — Source ready for {item.label}: {format_size(size)}")

    return failed


def seed_files(plan: list[SeedFile], overwrite: bool) -> int:
    failed = validate_sources(plan)
    if failed:
        return failed

    for item in plan:
        if not item.source.exists() and not item.required:
            print(f"SKIP — Optional source missing: {item.label}")
            continue

        if item.destination.exists() and not overwrite:
            print(f"SKIP — Destination exists and --overwrite was not used: {item.destination}")
            continue

        item.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.source, item.destination)

        copied_size = file_size(item.destination)
        if copied_size < item.minimum_size and item.required:
            print(f"FAIL — Copied file looks too small for {item.label}: {format_size(copied_size)}")
            failed += 1
        else:
            print(f"PASS — Seeded {item.label}: {item.destination} ({format_size(copied_size)})")

    return failed


def verify_destinations(plan: list[SeedFile]) -> int:
    failed = 0

    for item in plan:
        if not item.destination.exists():
            if item.required:
                print(f"FAIL — Missing required EXE runtime file for {item.label}: {item.destination}")
                failed += 1
            else:
                print(f"NOTE — Optional EXE runtime file missing for {item.label}: {item.destination}")
            continue

        size = file_size(item.destination)
        if size < item.minimum_size:
            if item.required:
                print(
                    f"FAIL — EXE runtime file for {item.label} looks too small: "
                    f"{item.destination} ({format_size(size)})"
                )
                failed += 1
            else:
                print(
                    f"NOTE — Optional EXE runtime file for {item.label} looks small: "
                    f"{item.destination} ({format_size(size)})"
                )
        else:
            print(f"PASS — EXE runtime file ready for {item.label}: {format_size(size)}")

    return failed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed built EXE runtime data from local source data for dev-only testing."
    )
    parser.add_argument(
        "--exe-root",
        default=str(DEFAULT_EXE_ROOT),
        help="Built EXE root folder. Default: dist/The Dragon's Touch",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Copy source runtime data into the built EXE runtime data folder.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify required EXE runtime data files exist.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Print the seed plan without copying.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing destination files when seeding.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    exe_root = Path(args.exe_root).resolve()
    plan = build_seed_plan(exe_root)

    print("v0.11.9.2.6 — EXE Runtime Data Seeding / Repair Test Helper")
    print("===========================================================")
    print(f"Project root: {ROOT}")
    print(f"EXE root:     {exe_root}")
    print()

    if not exe_root.exists():
        print(f"FAIL — EXE root does not exist: {exe_root}")
        return 1

    if args.plan or not (args.seed or args.verify):
        print_plan(plan)
        return 0

    failed = 0

    if args.seed:
        failed += seed_files(plan, overwrite=args.overwrite)

    if args.verify:
        failed += verify_destinations(plan)

    if failed:
        print(f"\nFAIL — {failed} check(s) failed.")
        return 1

    print("\nPASS — EXE runtime data seed/verify completed cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
