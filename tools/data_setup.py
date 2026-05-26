#!/usr/bin/env python3
r"""
v0.11.4.2-dev — Data Setup CLI Tool.

This is a developer/tester CLI wrapper around data.data_setup_service.

Examples:

  py tools\data_setup.py --status
  py tools\data_setup.py --download-scryfall --overwrite
  py tools\data_setup.py --download-combos --overwrite
  py tools\data_setup.py --commands
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from data.data_setup_service import (  # noqa: E402
    combo_index_build_commands,
    download_commander_spellbook_combo_bulk,
    download_scryfall_cards,
    get_data_setup_status,
    print_data_setup_status,
    status_to_dict,
    write_data_setup_status_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="The Dragon's Touch runtime data setup helper.")

    parser.add_argument("--status", action="store_true", help="Print runtime data status.")
    parser.add_argument("--json", action="store_true", help="Print runtime data status as JSON.")
    parser.add_argument("--write-status", action="store_true", help="Write runtime data setup status JSON.")
    parser.add_argument("--download-scryfall", action="store_true", help="Download Scryfall card data.")
    parser.add_argument("--download-combos", action="store_true", help="Download Commander Spellbook combo bulk data.")
    parser.add_argument("--commands", action="store_true", help="Print combo index build commands.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing downloaded data files.")

    args = parser.parse_args()

    did_action = False

    try:
        if args.download_scryfall:
            did_action = True
            path = download_scryfall_cards(overwrite=args.overwrite)
            print(f"Downloaded Scryfall card data: {path}")

        if args.download_combos:
            did_action = True
            path = download_commander_spellbook_combo_bulk(overwrite=args.overwrite)
            print(f"Downloaded Commander Spellbook combo data: {path}")

        if args.write_status:
            did_action = True
            path = write_data_setup_status_json()
            print(f"Wrote data setup status: {path}")

        if args.commands:
            did_action = True
            commands = combo_index_build_commands()
            print("Combo index build commands:")
            for label, command in commands.items():
                print(f"{label}:")
                print(f"  {command}")

        if args.json:
            did_action = True
            print(json.dumps(status_to_dict(), indent=2))

        if args.status or not did_action:
            print_data_setup_status()

    except Exception as exc:
        print()
        print(f"ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
