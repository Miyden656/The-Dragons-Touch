"""Round 8 smoke test for the modular MTG Deck Helper cleanup.

This test creates a tiny temporary project workspace with a miniature Scryfall
JSON and a small decklist, then runs the modular helper pipeline directly.

It is intentionally not a full parity test. Its purpose is to catch broken
imports, obvious parser failures, and output-writing failures.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import RuntimeConfig  # noqa: E402
from data.scryfall_loader import load_scryfall_lookup  # noqa: E402
from main import process_single_deck  # noqa: E402


def card(name, type_line, oracle_text="", color_identity=None, cmc=0, legal=True):
    return {
        "name": name,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "color_identity": color_identity or [],
        "cmc": cmc,
        "mana_cost": "",
        "legalities": {"commander": "legal" if legal else "banned"},
    }


def build_mini_scryfall(path: Path) -> None:
    cards = [
        card("Test Commander", "Legendary Creature — Human Wizard", "Whenever you cast an instant or sorcery spell, draw a card.", ["U", "R"], 3),
        card("Island", "Basic Land — Island", "", ["U"], 0),
        card("Mountain", "Basic Land — Mountain", "", ["R"], 0),
        card("Lightning Bolt", "Instant", "Lightning Bolt deals 3 damage to any target.", ["R"], 1),
        card("Opt", "Instant", "Scry 1. Draw a card.", ["U"], 1),
        card("Arcane Signet", "Artifact", "{T}: Add one mana of any color in your commander's color identity.", [], 2),
        card("Goblin Token", "Token Creature — Goblin", "", ["R"], 0),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cards, indent=2), encoding="utf-8")


def build_test_deck(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """Commander
1 Test Commander

Deck
1 Island
1 Mountain
1 Lightning Bolt
1 Opt
1 Arcane Signet

Tokens
1 Goblin Token
""".strip()
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="deck_helper_smoke_") as tmp:
        tmp_path = Path(tmp)
        os.chdir(tmp_path)
        try:
            scryfall_path = tmp_path / "data" / "scryfall_cards.json"
            deck_path = tmp_path / "decklists" / "smoke_test_deck.txt"
            build_mini_scryfall(scryfall_path)
            build_test_deck(deck_path)

            _, lookup = load_scryfall_lookup(scryfall_path)
            config = RuntimeConfig(
                output_mode="both",
                review_direction="cut_down",
                build_up_config={"mode": "not_applicable", "label": "Not applicable", "alpha": False},
                cut_depth_config={
                    "mode": "normal",
                    "optional_cut_target": 5,
                    "include_low_confidence": False,
                    "include_bracket_pressure": False,
                    "include_removal": False,
                    "include_manual_review": True,
                    "include_playable_replaceable": True,
                },
                prompt_interaction_mode="interactive",
            )
            written = process_single_deck(deck_path, config, lookup)
            if not written:
                raise AssertionError("No output files were written.")
            missing = [p for p in written if not Path(p).exists()]
            if missing:
                raise AssertionError(f"Missing output paths: {missing}")
            output_text = "\n".join(str(p) for p in written)
            required_markers = ["deck_report", "user_guided_prompt", "full_debug_report"]
            for marker in required_markers:
                if marker not in output_text:
                    raise AssertionError(f"Expected an output path containing {marker!r}. Got:\n{output_text}")

            print("Round 8 smoke test passed.")
            print("Files written:")
            for path in written:
                print(f"- {path}")
            return 0
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
