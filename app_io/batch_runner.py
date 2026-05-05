"""Batch-run helper for multiple selected deck files.

This preserves the legacy pattern of spawning one child Python process per deck,
with runtime choices passed through environment variables.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from config import RuntimeConfig, PROMPT_INTERACTION_MODE_DISPLAY



def build_child_environment(deck_file: Path, runtime_config: RuntimeConfig) -> dict[str, str]:
    child_environment = os.environ.copy()
    child_environment["MTG_DECK_FILE"] = str(deck_file)
    child_environment["MTG_OUTPUT_MODE"] = runtime_config.output_mode
    child_environment["MTG_REVIEW_DIRECTION"] = runtime_config.review_direction
    child_environment["MTG_BUILD_UP_MODE"] = runtime_config.build_up_config.get("mode", "not_applicable")
    child_environment["MTG_CUT_DEPTH_MODE"] = runtime_config.cut_depth_config["mode"]
    child_environment["MTG_OPTIONAL_CUT_TARGET"] = str(runtime_config.cut_depth_config["optional_cut_target"])
    child_environment["MTG_INCLUDE_LOW_CONFIDENCE"] = "1" if runtime_config.cut_depth_config.get("include_low_confidence") else "0"
    child_environment["MTG_INCLUDE_BRACKET_PRESSURE"] = "1" if runtime_config.cut_depth_config.get("include_bracket_pressure") else "0"
    child_environment["MTG_INCLUDE_REMOVAL_CUTS"] = "1" if runtime_config.cut_depth_config.get("include_removal") else "0"
    child_environment["MTG_INCLUDE_MANUAL_REVIEW"] = "1" if runtime_config.cut_depth_config.get("include_manual_review") else "0"
    child_environment["MTG_INCLUDE_PLAYABLE_REPLACEABLE"] = "1" if runtime_config.cut_depth_config.get("include_playable_replaceable") else "0"
    child_environment["MTG_PROMPT_INTERACTION_MODE"] = runtime_config.prompt_interaction_mode
    return child_environment



def run_batch(deck_files: list[Path], runtime_config: RuntimeConfig, entry_script: Path) -> None:
    print()
    print(f"Batch mode: {len(deck_files)} deck files selected.")
    print(f"Output mode: {runtime_config.output_mode}")
    print(f"Review direction: {runtime_config.review_direction}")
    print(
        "Prompt interaction mode: "
        f"{PROMPT_INTERACTION_MODE_DISPLAY.get(runtime_config.prompt_interaction_mode, runtime_config.prompt_interaction_mode)}"
    )
    if runtime_config.review_direction == "build_up":
        print(f"Build-up mode: {runtime_config.build_up_config['label']}")
    else:
        print(f"Cut depth mode: {runtime_config.cut_depth_config['mode']} (target {runtime_config.cut_depth_config['optional_cut_target']})")
    print()

    batch_summary: list[tuple[Path, int]] = []
    for deck_file in deck_files:
        print(f"Running deck helper for: {deck_file}")
        result = subprocess.run(
            [sys.executable, str(entry_script)],
            env=build_child_environment(deck_file, runtime_config),
            check=False,
        )
        batch_summary.append((deck_file, result.returncode))
        print()

    print("Batch run complete.")
    print("Final Summary:")
    print(f"- Decks processed: {len(batch_summary)}")
    print(f"- Output mode used: {runtime_config.output_mode}")
    print(f"- Review direction used: {runtime_config.review_direction}")
    if runtime_config.review_direction == "build_up":
        print(f"- Build-up mode used: {runtime_config.build_up_config['label']}")
    else:
        print(f"- Cut depth mode used: {runtime_config.cut_depth_config['mode']}")
    print(
        "- Prompt interaction mode used: "
        f"{PROMPT_INTERACTION_MODE_DISPLAY.get(runtime_config.prompt_interaction_mode, runtime_config.prompt_interaction_mode)}"
    )
    print(f"- Successes: {sum(1 for _, code in batch_summary if code == 0)}")
    print(f"- Failures: {sum(1 for _, code in batch_summary if code != 0)}")
    for path, code in batch_summary:
        status = "succeeded" if code == 0 else f"failed with code {code}"
        print(f"  - {path.name}: {status}")
