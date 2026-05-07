"""Smoke test for The Dragon's Touch cleanup pipeline.

Patch Batch 8 additions:
- Verify normal/debug output routing still works.
- Verify batch mode can process two different deck files with the same commander
  without merging their reports into the same output folder.
"""

from __future__ import annotations

import json
import os
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


def build_test_deck(path: Path, extra_comment: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""Commander
1 Test Commander

Deck
1 Island
1 Mountain
1 Lightning Bolt
1 Opt
1 Arcane Signet

Tokens
1 Goblin Token
{extra_comment}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def make_config() -> RuntimeConfig:
    return RuntimeConfig(
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


def assert_paths_exist(paths: list[Path]) -> None:
    if not paths:
        raise AssertionError("No output files were written.")
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        raise AssertionError(f"Missing output paths: {missing}")


def assert_root_has_no_files(deck_root: Path) -> None:
    root_files = [p for p in deck_root.iterdir() if p.is_file()]
    if root_files:
        raise AssertionError(f"Output files were incorrectly written directly into the deck root: {root_files}")


def assert_routing(written: list[Path], deck_root: Path) -> None:
    normal_dir = (deck_root / "normal").resolve()
    debug_dir = (deck_root / "debug").resolve()
    if not normal_dir.is_dir() or not debug_dir.is_dir():
        raise AssertionError(f"Expected normal/ and debug/ output folders were not created in {deck_root}.")
    assert_root_has_no_files(deck_root)
    for p in written:
        path = Path(p).resolve()
        stem = path.stem.lower()
        suffix = path.suffix.lower()
        is_debug = (suffix == ".md" and (stem.endswith("_debug") or "_debug_" in stem)) or (
            suffix == ".txt" and (stem.endswith("_full_debug_report") or "_full_debug_report_" in stem)
        )
        if is_debug and path.parent != debug_dir:
            raise AssertionError(f"Debug file routed outside debug folder: {p}")
        if not is_debug and path.parent != normal_dir:
            raise AssertionError(f"Normal file routed outside normal folder: {p}")


def main() -> int:
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="deck_helper_smoke_") as tmp:
        tmp_path = Path(tmp)
        os.chdir(tmp_path)
        try:
            scryfall_path = tmp_path / "data" / "scryfall_cards.json"
            deck_path = tmp_path / "decklists" / "smoke_test_deck.txt"
            duplicate_deck_path = tmp_path / "decklists" / "smoke_test_deck_companion_section.txt"
            build_mini_scryfall(scryfall_path)
            build_test_deck(deck_path)
            build_test_deck(duplicate_deck_path, extra_comment="# same commander, different source file")

            _, lookup = load_scryfall_lookup(scryfall_path)
            config = make_config()

            # Single-deck mode keeps the clean commander-only folder name.
            single_written = process_single_deck(deck_path, config, lookup)
            assert_paths_exist(single_written)
            single_root = (tmp_path / "outputs" / "Test_Commander").resolve()
            assert_routing(single_written, single_root)

            report_text = (single_root / "normal" / "Test_Commander_deck_report.md").read_text(encoding="utf-8")
            prompt_text = (single_root / "normal" / "Test_Commander_user_guided_prompt.md").read_text(encoding="utf-8")
            diagnostics_text = (single_root / "debug" / "Test_Commander_diagnostics_debug.md").read_text(encoding="utf-8")
            for expected in ["## Philosophy Guide", "Balanced / Unknown"]:
                if expected not in report_text:
                    raise AssertionError(f"Philosophy guide missing from report: {expected}")
            for expected in ["Full Decklist / Main Deck Cards for AI Review", "Annotated Decklist / Card Role Notes for AI Review"]:
                if expected not in report_text:
                    raise AssertionError(f"AI handoff decklist section missing from report: {expected}")
            if "Phase 0" not in prompt_text and "First, ask the user" not in prompt_text:
                raise AssertionError("Deck-report-first prompt guardrail missing from generated prompt.")
            if "Resolved philosophy lens: Balanced / Unknown" not in diagnostics_text:
                raise AssertionError("Philosophy diagnostics missing or incorrect.")

            # Batch mode should avoid merging two same-commander deck files into one output folder.
            batch_written_a = process_single_deck(deck_path, config, lookup, batch_output_folder=True)
            batch_written_b = process_single_deck(duplicate_deck_path, config, lookup, batch_output_folder=True)
            assert_paths_exist(batch_written_a)
            assert_paths_exist(batch_written_b)
            batch_root_a = Path(batch_written_a[0]).resolve().parents[1]
            batch_root_b = Path(batch_written_b[0]).resolve().parents[1]
            if batch_root_a == batch_root_b:
                raise AssertionError(f"Batch duplicate commander outputs merged into one folder: {batch_root_a}")
            assert_routing(batch_written_a, batch_root_a)
            assert_routing(batch_written_b, batch_root_b)

            print("The Dragon's Touch smoke test passed.")
            print("Single-deck folder:", single_root)
            print("Batch duplicate commander folders:")
            print("-", batch_root_a)
            print("-", batch_root_b)
            return 0
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
