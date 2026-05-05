"""Round 2 starter entry point. :D

This file is intentionally not the full deck helper yet.
Round 2 only separates runtime config, file picking, output helpers, and batch helpers.
The analysis engine remains in the legacy monolith until later rounds.
"""

from __future__ import annotations

from pathlib import Path

from deck_helper.config import get_runtime_config, print_runtime_config_summary
from deck_helper.io.batch_runner import run_batch
from deck_helper.io.deck_file_picker import resolve_deck_files



def main() -> None:
    print("RUNNING MTG DECK HELPER v0.6.2-clean.1 - MODULAR SKELETON CLEANUP")

    deck_files = resolve_deck_files()
    runtime_config = get_runtime_config()

    if len(deck_files) > 1:
        # Temporary bridge: in a real local checkout, point this at the current entry script.
        # During later rounds, this becomes the real modular runner.
        run_batch(deck_files, runtime_config, Path(__file__))
        return

    print()
    print(f"Selected deck file: {deck_files[0]}")
    print_runtime_config_summary(runtime_config)
    print()
    print("Round 2 checkpoint reached.")
    print("Next round will move parsing and Scryfall loading into modules.")
    print("For full reports during cleanup, continue using deck_helper_v0.6.2.6.py until later rounds are migrated.")



if __name__ == "__main__":
    main()
