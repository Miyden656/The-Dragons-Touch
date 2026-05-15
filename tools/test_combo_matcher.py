#!/usr/bin/env python3
"""
v0.8.7.2.1-dev — Isolated Combo Awareness Report Section Generator for The Dragon's Touch.

This script is manual-only and local-only.
It does not call an API, modify main.py, change the UI, or write normal reports.

New through v0.8.7.2.1-dev:
- Fixes quantity parsing so 1xXorn / Xorn is preserved as Xorn, not orn.
- Deck path is optional; if omitted, open a Tkinter file picker first.
- Falls back to terminal deck selection if Tkinter is unavailable.
- Writes a full reconciliation/debug markdown file for count mismatches.
- Can compare complete combo results against a Combo Finder text export.
- Adds filter-profile verification counts to find Combo Finder parity without writing full reports.
- Keeps the combined combo-count dashboard as the default output.
- Adds optional --write-breakdown to produce a combo awareness breakdown artifact.
- Caps detailed potential combos in breakdowns by default for readability.
- Adds --show-all-potentials for full dev/audit breakdown output.
- Excludes Maybeboard and Tokens & Extras from deck parsing by default.
- Keeps plain Tokens/Token package headings included as real deck package sections.
- Excludes Made Cuts variants as already-removed cards.
- Adds --stress-test to write all deck dashboard results into one markdown file.
- Full markdown reconciliation is optional with --write-reconciliation.
- Adds --write-report-section to write a concise future normal-report section artifact.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

# Allow running from project root without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from combo_awareness.combo_matcher import (  # noqa: E402
    build_combo_breakdown_markdown,
    build_combo_report_section_markdown,
    build_markdown_summary,
    canonical_identity,
    combo_card_names,
    format_combo_result,
    infer_commander_identity,
    identity_to_string,
    load_collection_index,
    load_combo_index,
    load_scryfall_name_identity_map,
    match_deck_to_combo_index,
    normalize_card_name,
    parse_decklist,
)

DEFAULT_INDEX_PATH = Path("data/commander_spellbook/combo_index.json")
DEFAULT_SCRYFALL_PATH = Path("data/scryfall_cards.json")
DEFAULT_COLLECTION_DIR = Path("collection")
DEFAULT_DECK_DIR = Path("Decklists")
DEFAULT_SUMMARY_PATH = Path("docs/combo_matcher_test_summary_v0.8.7.2.1-dev.md")
DEFAULT_RECONCILIATION_PATH = Path("docs/combo_matcher_reconciliation_v0.8.7.2.1-dev.md")
DEFAULT_BREAKDOWN_PATH = Path("docs/combo_awareness_breakdown_v0.8.7.2.1-dev.md")
DEFAULT_PARITY_INDEX_PATH = Path("data/commander_spellbook/combo_index_parity.json")
DEFAULT_STRESS_OUTPUT_PATH = Path("docs/combo_matcher_stress_test_v0.8.7.2.1-dev.md")
DEFAULT_REPORT_SECTION_PATH = Path("docs/combo_awareness_report_section_v0.8.7.2.1-dev.md")

COMBO_HEADER_RE = re.compile(r"^\s*Combo\s+\d+\s*$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run isolated local Commander Spellbook combo matching against one deck."
    )
    parser.add_argument(
        "--deck",
        default="",
        help="Path to one decklist .txt file. If omitted, choose a deck from --deck-dir.",
    )
    parser.add_argument(
        "--deck-dir",
        default=str(DEFAULT_DECK_DIR),
        help="Folder to open/list decklists from when --deck is omitted.",
    )
    parser.add_argument(
        "--terminal-picker",
        action="store_true",
        help="Skip the Tkinter file picker and use terminal deck-number selection instead.",
    )
    parser.add_argument("--index", default=str(DEFAULT_INDEX_PATH), help="Path to data/commander_spellbook/combo_index.json")
    parser.add_argument("--parity-index", default=str(DEFAULT_PARITY_INDEX_PATH), help="Optional all-OK combo index for verification counts, usually combo_index_parity.json")
    parser.add_argument(
        "--verification-counts",
        action="store_true",
        help="Deprecated alias. The dashboard output is now the default.",
    )
    parser.add_argument(
        "--combo-finder-check",
        action="store_true",
        help="Deprecated alias. The dashboard output is now the default.",
    )
    parser.add_argument("--scryfall", default=str(DEFAULT_SCRYFALL_PATH), help="Path to local Scryfall JSON data")
    parser.add_argument("--collection-dir", default=str(DEFAULT_COLLECTION_DIR), help="Optional collection folder to check missing cards against")
    parser.add_argument("--no-collection", action="store_true", help="Do not load collection files")
    parser.add_argument("--include-maybeboard", action="store_true", help="Debug only: include Maybeboard/Sideboard/Considering sections as deck cards.")
    parser.add_argument("--include-tokens", action="store_true", help="Debug only: include Tokens & Extras sections as deck cards.")
    parser.add_argument("--stress-test", action="store_true", help="Run the dashboard matcher across decklists and write all results into one markdown file.")
    parser.add_argument("--stress-output", default=str(DEFAULT_STRESS_OUTPUT_PATH), help="Path to write the stress-test markdown file.")
    parser.add_argument("--commander", action="append", default=[], help="Explicit commander name. Can be used more than once for partners.")
    parser.add_argument("--commander-identity", default="", help="Explicit commander color identity, e.g. WUBRG, UR, BG, or C")
    parser.add_argument("--include-spoilers", action="store_true", help="Include spoiler-tagged combos. Default hides them.")
    parser.add_argument("--no-strict-color", action="store_true", help="Do not filter by commander color identity")
    parser.add_argument("--show-complete", type=int, default=10, help="Number of complete combo samples to print/write in summary")
    parser.add_argument("--show-potential", type=int, default=25, help="Number of one-card-away combo samples to print/write in summary")
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH), help="Path to write markdown test summary")
    parser.add_argument(
        "--reconciliation",
        default=str(DEFAULT_RECONCILIATION_PATH),
        help="Path to write full reconciliation/debug markdown",
    )
    parser.add_argument(
        "--write-reconciliation",
        action="store_true",
        help="Write the full reconciliation/debug markdown file. Default dashboard mode writes no markdown reports.",
    )
    parser.add_argument(
        "--write-breakdown",
        action="store_true",
        help="Write the v0.8.7.2.1-dev combo awareness breakdown markdown artifact.",
    )
    parser.add_argument(
        "--write-report-section",
        action="store_true",
        help="Write the v0.8.7.2.1-dev concise combo awareness report-section artifact. This is isolated and not injected into normal reports.",
    )
    parser.add_argument(
        "--breakdown",
        default=str(DEFAULT_BREAKDOWN_PATH),
        help="Path to write the v0.8.7.2.1-dev combo awareness breakdown markdown artifact.",
    )
    parser.add_argument(
        "--report-section",
        default=str(DEFAULT_REPORT_SECTION_PATH),
        help="Path to write the v0.8.7.2.1-dev concise combo awareness report-section markdown artifact.",
    )
    parser.add_argument(
        "--report-section-complete-limit",
        type=int,
        default=10,
        help="Maximum current infinite combos to show in the concise report section. 0 means show all.",
    )
    parser.add_argument(
        "--report-section-potential-limit",
        type=int,
        default=10,
        help="Maximum collection-completable potential combos to show in the concise report section. 0 means show all.",
    )
    parser.add_argument(
        "--breakdown-complete-limit",
        type=int,
        default=0,
        help="Limit complete combos in breakdown. 0 means show all.",
    )
    parser.add_argument(
        "--breakdown-potential-limit",
        type=int,
        default=25,
        help="Limit detailed potential combos in breakdown. Default 25. Use 0 with --show-all-potentials to show all.",
    )
    parser.add_argument(
        "--show-all-potentials",
        action="store_true",
        help="Show every Dragon's Touch Potential Combo in the breakdown. Intended for dev/audit use.",
    )
    parser.add_argument(
        "--no-reconciliation",
        action="store_true",
        help="Deprecated compatibility flag. Default dashboard mode already writes no reconciliation report.",
    )
    parser.add_argument(
        "--combo-finder",
        default="",
        help="Optional path to a Combo Finder complete-combo text export for exact comparison.",
    )
    parser.add_argument(
        "--expected-complete-count",
        type=int,
        default=None,
        help="Optional known complete combo count from another tool, for reconciliation notes.",
    )
    parser.add_argument(
        "--expected-potential-count",
        type=int,
        default=None,
        help="Optional known potential combo count from another tool, for reconciliation notes.",
    )
    return parser.parse_args()


def choose_deck_file_with_tkinter(deck_dir: Path) -> Path | None:
    """Open a small native file picker for choosing one decklist.

    Returns None when Tkinter is unavailable so the caller can fall back to
    terminal selection. Raises KeyboardInterrupt when the user cancels the
    dialog intentionally.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    initial_dir = deck_dir
    if not initial_dir.is_absolute():
        initial_dir = PROJECT_ROOT / initial_dir

    try:
        root = tk.Tk()
        root.withdraw()
        root.update()
        selected = filedialog.askopenfilename(
            title="Select a Commander decklist",
            initialdir=str(initial_dir if initial_dir.exists() else PROJECT_ROOT),
            filetypes=[
                ("Text decklists", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
    except Exception:
        return None

    if not selected:
        raise KeyboardInterrupt("Deck selection cancelled.")

    return Path(selected)


def choose_deck_file_terminal(deck_dir: Path) -> Path:
    """Let the user choose one decklist from a folder without typing a path."""
    if not deck_dir.exists():
        raise FileNotFoundError(f"Deck folder not found: {deck_dir}")

    candidates = sorted(
        [
            path for path in deck_dir.rglob("*.txt")
            if path.is_file() and not is_probable_non_deck_file(path)
        ],
        key=lambda p: str(p).casefold(),
    )
    if not candidates:
        raise FileNotFoundError(f"No .txt decklists found in: {deck_dir}")

    print("\nSelect a decklist")
    print("-----------------")
    for index, path in enumerate(candidates, start=1):
        print(f"{index:>3}. {path}")

    while True:
        answer = input("\nEnter deck number, or Q to cancel: ").strip()
        if answer.casefold() in {"q", "quit", "cancel"}:
            raise KeyboardInterrupt("Deck selection cancelled.")
        if not answer.isdigit():
            print("Please enter a number from the list.")
            continue
        choice = int(answer)
        if 1 <= choice <= len(candidates):
            return candidates[choice - 1]
        print(f"Please enter a number between 1 and {len(candidates)}.")


def combo_set(card_names: Iterable[str]) -> frozenset[str]:
    return frozenset(normalize_card_name(name) for name in card_names if str(name).strip())


def parse_combo_finder_file(path: Path) -> list[list[str]]:
    """Parse a simple Combo Finder complete-combo list into card-name groups."""
    if not path.exists():
        raise FileNotFoundError(f"Combo Finder file not found: {path}")

    combos: list[list[str]] = []
    current: list[str] = []

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if COMBO_HEADER_RE.match(line):
            if current:
                combos.append(current)
                current = []
            continue
        current.append(line)

    if current:
        combos.append(current)

    return combos


def sorted_combo_names(card_names: Iterable[str]) -> str:
    return ", ".join(sorted([str(name) for name in card_names], key=lambda x: x.casefold()))


def build_reconciliation_markdown(
    *,
    deck,
    summary,
    commander_identity,
    index_metadata: dict,
    include_spoilers: bool,
    collection_loaded: bool,
    expected_complete_count: int | None,
    expected_potential_count: int | None,
    combo_finder_path: Path | None,
    combo_finder_combos: list[list[str]] | None,
) -> str:
    """Build full debug markdown for count reconciliation."""
    lines: list[str] = [
        "# v0.8.7.2.1-dev — Combo Matcher Dashboard / Reconciliation Debug",
        "",
        "## Scope Guard",
        "",
        "- No API calls were made.",
        "- No app integration was performed.",
        "- `main.py` was not changed.",
        "- UI and normal report generation were not changed.",
        "- This file is optional full debug output. The default v0.8.7.2.1-dev command prints a compact dashboard instead of writing this file.",
        "",
        "## Deck",
        "",
        f"- Deck file: `{deck.path}`",
        f"- Commanders detected: {', '.join(deck.commander_names) if deck.commander_names else 'Not detected'}",
        f"- Commander identity used: {identity_to_string(commander_identity) if commander_identity is not None else 'Unavailable/not applied'}",
        f"- Cards parsed including commanders: {len(deck.all_card_names):,}",
        f"- Unique normalized cards parsed: {len(deck.normalized_all_cards):,}",
        "",
        "## Combo Index",
        "",
        f"- Source version: {index_metadata.get('source_version', 'unknown')}",
        f"- Source timestamp: {index_metadata.get('source_timestamp', 'unknown')}",
        f"- Index schema version: {index_metadata.get('index_schema_version', 'unknown')}",
        "",
        "## Match Results",
        "",
        f"- Combos scanned: {summary.scanned_combos:,}",
        f"- Infinite combos in deck: {len(summary.complete_combos):,}",
        f"- Potential infinite combos: {len(summary.one_card_away_combos):,}",
        "- Potential infinite combos are missing only one named card.",
        f"- Spoiler-tagged combos included: {'Yes' if include_spoilers else 'No; hidden by default'}",
        f"- Collection files loaded: {'Yes' if collection_loaded else 'No'}",
        "",
        "## Expected Count Comparison",
        "",
    ]

    if expected_complete_count is not None:
        delta = len(summary.complete_combos) - expected_complete_count
        lines.append(f"- Expected complete combos: {expected_complete_count:,}")
        lines.append(f"- Matcher complete combos: {len(summary.complete_combos):,}")
        lines.append(f"- Complete combo delta: {delta:+,}")
    else:
        lines.append("- Expected complete combo count: not provided")

    if expected_potential_count is not None:
        delta = len(summary.one_card_away_combos) - expected_potential_count
        lines.append(f"- Expected potential combos: {expected_potential_count:,}")
        lines.append(f"- Matcher potential combos: {len(summary.one_card_away_combos):,}")
        lines.append(f"- Potential combo delta: {delta:+,}")
    else:
        lines.append("- Expected potential combo count: not provided")

    lines.extend([
        "",
        "## Filtered / Skipped During Matching",
        "",
        f"- Spoiler-tagged hidden: {summary.skipped_spoiler:,}",
        f"- Color-identity invalid hidden: {summary.skipped_color_identity:,}",
        f"- mustBeCommander invalid hidden: {summary.skipped_must_be_commander:,}",
        f"- Unusable combo shape skipped: {summary.skipped_unusable_shape:,}",
        "",
    ])

    if combo_finder_combos is not None:
        matcher_sets: dict[frozenset[str], list[str]] = {
            combo_set(combo_card_names(result.combo)): combo_card_names(result.combo)
            for result in summary.complete_combos
        }
        finder_sets: dict[frozenset[str], list[str]] = {
            combo_set(names): names
            for names in combo_finder_combos
        }
        missing_from_matcher = [finder_sets[key] for key in finder_sets.keys() - matcher_sets.keys()]
        extra_in_matcher = [matcher_sets[key] for key in matcher_sets.keys() - finder_sets.keys()]

        lines.extend([
            "## Combo Finder Complete-Combo Comparison",
            "",
            f"- Combo Finder file: `{combo_finder_path}`",
            f"- Combo Finder complete combos parsed: {len(combo_finder_combos):,}",
            f"- Complete combos missing from matcher: {len(missing_from_matcher):,}",
            f"- Complete combos extra in matcher: {len(extra_in_matcher):,}",
            "",
            "### Complete Combos Missing From Matcher",
            "",
        ])
        if missing_from_matcher:
            for index, names in enumerate(missing_from_matcher, start=1):
                lines.append(f"{index}. {sorted_combo_names(names)}")
        else:
            lines.append("None.")

        lines.extend(["", "### Complete Combos Extra In Matcher", ""])
        if extra_in_matcher:
            for index, names in enumerate(extra_in_matcher, start=1):
                lines.append(f"{index}. {sorted_combo_names(names)}")
        else:
            lines.append("None.")
        lines.append("")

    lines.extend([
        "## Parsed Deck Cards",
        "",
        "Use this section to confirm whether the matcher missed a decklist line.",
        "",
    ])
    counts = Counter(deck.all_card_names)
    for name in sorted(counts, key=lambda x: x.casefold()):
        count = counts[name]
        if count == 1:
            lines.append(f"- {name}")
        else:
            lines.append(f"- {count}x {name}")

    lines.extend(["", "## Full Complete Combos Found", ""])
    if summary.complete_combos:
        for index, result in enumerate(summary.complete_combos, start=1):
            lines.append(f"### Complete Combo {index}")
            lines.append("")
            lines.extend(format_combo_result(result))
            lines.append("")
    else:
        lines.append("No complete combos found.")
        lines.append("")

    lines.extend(["## Full Potential Combos Missing One Card", ""])
    if summary.one_card_away_combos:
        for index, result in enumerate(summary.one_card_away_combos, start=1):
            lines.append(f"### Potential Combo {index}")
            lines.append("")
            lines.extend(format_combo_result(result))
            lines.append("")
    else:
        lines.append("No one-card-away potential combos found.")
        lines.append("")

    lines.extend([
        "## Notes",
        "",
        "- If Combo Finder counts differ, compare the missing/extra complete combo lists first.",
        "- If complete combo comparison matches but counts still differ, check filter settings and data version.",
        "- Potential combo comparison needs a full potential-combo export from the outside tool for exact diffing.",
        "- This file is intentionally verbose and should not become a normal user-facing report.",
        "",
    ])
    return "\n".join(lines)



def count_owned_potential(summary, collection_loaded: bool) -> int:
    if not collection_loaded:
        return 0
    owned_count = 0
    for result in summary.one_card_away_combos:
        for sources in result.collection_sources_by_missing_card.values():
            if sources:
                owned_count += 1
                break
    return owned_count


def print_count_block(label: str, summary, *, expected_complete_count=None, expected_potential_count=None, collection_loaded=False) -> None:
    print(f"\n{label}")
    print("-" * len(label))
    print(f"Combos scanned: {summary.scanned_combos:,}")
    print(f"Infinite combos in deck: {len(summary.complete_combos):,}")
    print(f"Potential infinite combos: {len(summary.one_card_away_combos):,}")
    if expected_complete_count is not None:
        delta = len(summary.complete_combos) - expected_complete_count
        print(f"Expected complete combos: {expected_complete_count:,} | Delta: {delta:+,}")
    if expected_potential_count is not None:
        delta = len(summary.one_card_away_combos) - expected_potential_count
        print(f"Expected potential combos: {expected_potential_count:,} | Delta: {delta:+,}")
    owned_count = count_owned_potential(summary, collection_loaded)
    if owned_count:
        print(f"Potential combos completable from loaded collection files: {owned_count:,}")
    print(f"Spoiler-tagged hidden: {summary.skipped_spoiler:,}")
    print(f"Color-identity invalid hidden: {summary.skipped_color_identity:,}")
    print(f"mustBeCommander invalid hidden: {summary.skipped_must_be_commander:,}")


def print_dashboard(
    *,
    strict_summary,
    parity_summary,
    raw_summary,
    strict_index_path: Path,
    parity_index_path: Path,
    parity_metadata: dict,
    collection_loaded: bool,
) -> None:
    """Print the compact v0.8.3.1 dashboard output."""
    print("\nCombo Dashboard")
    print("---------------")
    print(f"Infinite combos in deck: {len(strict_summary.complete_combos):,}")
    print()
    print(f"Dragon's Touch Potential Combos: {len(strict_summary.one_card_away_combos):,}")
    print(f"Combo Finder parity potential combos: {len(parity_summary.one_card_away_combos):,}")
    print(f"All raw potential combos: {len(raw_summary.one_card_away_combos):,}")

    print("\nCollection Completion")
    print("---------------------")
    if collection_loaded:
        print(f"Dragon's Touch collection-completable potentials: {count_owned_potential(strict_summary, collection_loaded):,}")
        print(f"Combo Finder parity collection-completable potentials: {count_owned_potential(parity_summary, collection_loaded):,}")
        print(f"All raw collection-completable potentials: {count_owned_potential(raw_summary, collection_loaded):,}")
    else:
        print("Collection files were not loaded.")

    print("\nFilter Notes")
    print("------------")
    print(f"Spoiler-tagged hidden by Dragon's Touch: {strict_summary.skipped_spoiler:,}")
    print(f"Color-identity invalid hidden by Dragon's Touch: {strict_summary.skipped_color_identity:,}")
    print(f"mustBeCommander invalid hidden by Dragon's Touch: {strict_summary.skipped_must_be_commander:,}")

    print("\nData Sources")
    print("------------")
    print(f"Strict index: {strict_index_path}")
    print(f"Strict index variants scanned: {strict_summary.scanned_combos:,}")
    print()
    print(f"Verification index: {parity_index_path}")
    print(f"Verification index variants scanned: {parity_summary.scanned_combos:,}")
    print(f"Verification index commander_legal_only: {parity_metadata.get('commander_legal_only', 'unknown')}")

    print("\nInterpretation")
    print("--------------")
    print("Dragon's Touch Potential Combos are the deck-relevant combos The Dragon's Touch would normally show.")
    print("Combo Finder parity potential combos are for validation against Combo Finder-style counts.")
    print("All raw potential combos ignore normal relevance filters and are for debugging only.")



NON_DECK_FILE_NAMES = {
    "readme_decklists.txt",
    "readme.txt",
}


def is_probable_non_deck_file(path: Path) -> bool:
    """Skip README/helper text files during stress testing and deck selection."""
    name = path.name.casefold().strip()
    return name in NON_DECK_FILE_NAMES or name.startswith("readme")


def collect_deck_files_for_stress(deck_dir: Path, explicit_deck: str = "") -> list[Path]:
    if explicit_deck:
        return [Path(explicit_deck)]
    if not deck_dir.exists():
        raise FileNotFoundError(f"Deck folder not found: {deck_dir}")
    return sorted(
        [
            path for path in deck_dir.rglob("*.txt")
            if path.is_file() and not is_probable_non_deck_file(path)
        ],
        key=lambda p: str(p).casefold(),
    )


def analyze_stress_warnings(deck, commander_identity) -> list[str]:
    """Return parser/deck-shape warnings for the stress-test markdown."""
    warnings: list[str] = []
    card_count = len(deck.all_card_names)
    commander_count = len(deck.commander_names)
    if commander_count == 0:
        warnings.append("no commander detected")
    elif commander_count > 4:
        warnings.append(f"suspicious commander count: {commander_count}")
    if commander_identity is None:
        warnings.append("commander identity unavailable")
    if card_count < 80:
        warnings.append(f"small deck/card count: {card_count}")
    if card_count > 120:
        warnings.append(f"large deck/card count: {card_count}")
    # If obvious package labels still appear as commanders, flag for manual parser review.
    suspicious_terms = {
        "anthem", "bomb", "burn", "card advantage", "card draw", "copy",
        "draw", "evasion", "finisher", "interaction", "removal", "ramp",
        "complete infinite combos", "damage/win cons", "cost reduction",
    }
    commander_norms = {normalize_card_name(name) for name in deck.commander_names}
    if commander_norms.intersection(suspicious_terms):
        warnings.append("commander field may include category labels")
    return warnings


def build_stress_markdown(
    *,
    deck_results: list[dict],
    strict_index_path: Path,
    parity_index_path: Path,
    parity_metadata: dict,
    include_maybeboard: bool,
    include_tokens: bool,
    collection_loaded: bool,
) -> str:
    lines: list[str] = [
        "# v0.8.7.2.1-dev — Combo Matcher Stress Test Results",
        "",
        "## Scope Guard",
        "",
        "- No API calls were made.",
        "- No app integration was performed.",
        "- `main.py` was not changed.",
        "- UI and normal report generation were not changed.",
        "- This is an isolated local stress-test markdown file.",
        "",
        "## Parser Scope",
        "",
        f"- Maybeboard included: {'Yes' if include_maybeboard else 'No'}",
        f"- Tokens/Extras included: {'Yes' if include_tokens else 'No'}",
        "- Default behavior should analyze actual deck cards only.",
        "",
        "## Data Sources",
        "",
        f"- Strict index: `{strict_index_path}`",
        f"- Verification index: `{parity_index_path}`",
        f"- Verification index commander_legal_only: {parity_metadata.get('commander_legal_only', 'unknown')}",
        f"- Collection files loaded: {'Yes' if collection_loaded else 'No'}",
        "",
        "## Aggregate Summary",
        "",
        f"- Decks processed: {len(deck_results):,}",
        f"- Decks with errors: {sum(1 for row in deck_results if row.get('error')):,}",
        f"- Decks with warnings: {sum(1 for row in deck_results if row.get('warnings')):,}",
        "",
        "| Deck | Commander(s) | Identity | Cards | Unique | Complete | Dragon's Touch Potential | Combo Finder Parity | All Raw Potential | DT Collection | Parity Collection | Raw Collection | Warnings | Error |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in deck_results:
        if row.get("error"):
            lines.append(
                f"| {row['deck']} | - | - | - | - | - | - | - | - | - | - | - | {row.get('warnings', '')} | {row['error']} |"
            )
            continue
        lines.append(
            "| {deck} | {commanders} | {identity} | {cards} | {unique} | {complete} | {dt_potential} | {parity_potential} | {raw_potential} | {dt_owned} | {parity_owned} | {raw_owned} | {warnings} |  |".format(
                **row
            )
        )

    lines.extend(["", "## Per-Deck Details", ""])
    for row in deck_results:
        lines.append(f"### {row['deck']}")
        lines.append("")
        if row.get("error"):
            lines.append(f"- ERROR: {row['error']}")
            lines.append("")
            continue
        lines.extend([
            f"- Commander(s): {row['commanders']}",
            f"- Commander identity: {row['identity']}",
            f"- Cards parsed including commanders: {row['cards']}",
            f"- Unique normalized cards parsed: {row['unique']}",
            f"- Warnings: {row.get('warnings') or 'None'}",
            f"- Infinite combos in deck: {row['complete']}",
            f"- Dragon's Touch Potential Combos: {row['dt_potential']}",
            f"- Combo Finder parity potential combos: {row['parity_potential']}",
            f"- All raw potential combos: {row['raw_potential']}",
            f"- Dragon's Touch collection-completable potentials: {row['dt_owned']}",
            f"- Combo Finder parity collection-completable potentials: {row['parity_owned']}",
            f"- All raw collection-completable potentials: {row['raw_owned']}",
            f"- Spoiler-tagged hidden by Dragon's Touch: {row['skipped_spoiler']}",
            f"- Color-identity invalid hidden by Dragon's Touch: {row['skipped_color']}",
            f"- mustBeCommander invalid hidden by Dragon's Touch: {row['skipped_commander']}",
            "",
        ])
    return "\n".join(lines)


def run_stress_test(args: argparse.Namespace) -> int:
    deck_paths = collect_deck_files_for_stress(Path(args.deck_dir), args.deck)
    if not deck_paths:
        print("No decklists found for stress test.")
        return 2

    index_path = Path(args.index)
    parity_index_path = Path(args.parity_index)
    scryfall_path = Path(args.scryfall)
    collection_dir = None if args.no_collection else Path(args.collection_dir)
    stress_output_path = Path(args.stress_output)

    print("v0.8.7.2.1-dev — Combo Matcher Stress Test")
    print("==========================================")
    print("Loading local files only. No API calls will be made...")
    print(f"Decks to process: {len(deck_paths):,}")
    print(f"Strict index: {index_path}")
    print(f"Parity index: {parity_index_path}")

    combo_index = load_combo_index(index_path)
    parity_index = load_combo_index(parity_index_path) if parity_index_path.exists() else combo_index
    parity_source = parity_index_path if parity_index_path.exists() else index_path
    parity_metadata = parity_index.get("metadata", {}) if isinstance(parity_index, dict) else {}
    scryfall_identity_by_name = load_scryfall_name_identity_map(scryfall_path)

    collection = None
    collection_loaded = False
    if collection_dir is not None:
        print(f"Collection folder: {collection_dir}")
        collection = load_collection_index(collection_dir)
        collection_loaded = bool(collection.cards_by_normalized_name)

    results: list[dict] = []
    for i, deck_path in enumerate(deck_paths, start=1):
        print(f"[{i:,}/{len(deck_paths):,}] {deck_path}")
        try:
            deck = parse_decklist(
                deck_path,
                explicit_commanders=args.commander,
                include_maybeboard=args.include_maybeboard,
                include_tokens=args.include_tokens,
            )
            explicit_identity = canonical_identity(args.commander_identity) if args.commander_identity else None
            inferred_identity = infer_commander_identity(deck, scryfall_identity_by_name) if explicit_identity is None and not args.no_strict_color else None
            commander_identity = explicit_identity if explicit_identity is not None else inferred_identity
            strict_color = not args.no_strict_color
            strict_summary = match_deck_to_combo_index(
                deck,
                combo_index,
                commander_identity=commander_identity,
                collection=collection,
                include_spoilers=args.include_spoilers,
                strict_color_identity=strict_color,
                hide_invalid_must_be_commander=True,
            )
            parity_summary = match_deck_to_combo_index(
                deck,
                parity_index,
                commander_identity=commander_identity,
                collection=collection,
                include_spoilers=args.include_spoilers,
                strict_color_identity=strict_color,
                hide_invalid_must_be_commander=False,
            )
            raw_summary = match_deck_to_combo_index(
                deck,
                parity_index,
                commander_identity=None,
                collection=collection,
                include_spoilers=True,
                strict_color_identity=False,
                hide_invalid_must_be_commander=False,
            )
            warnings = analyze_stress_warnings(deck, commander_identity)
            results.append({
                "deck": str(deck_path),
                "commanders": ", ".join(deck.commander_names) if deck.commander_names else "Not detected",
                "identity": identity_to_string(commander_identity) if commander_identity is not None else "Unavailable/not applied",
                "cards": f"{len(deck.all_card_names):,}",
                "unique": f"{len(deck.normalized_all_cards):,}",
                "complete": f"{len(strict_summary.complete_combos):,}",
                "dt_potential": f"{len(strict_summary.one_card_away_combos):,}",
                "parity_potential": f"{len(parity_summary.one_card_away_combos):,}",
                "raw_potential": f"{len(raw_summary.one_card_away_combos):,}",
                "dt_owned": f"{count_owned_potential(strict_summary, collection_loaded):,}",
                "parity_owned": f"{count_owned_potential(parity_summary, collection_loaded):,}",
                "raw_owned": f"{count_owned_potential(raw_summary, collection_loaded):,}",
                "skipped_spoiler": f"{strict_summary.skipped_spoiler:,}",
                "skipped_color": f"{strict_summary.skipped_color_identity:,}",
                "skipped_commander": f"{strict_summary.skipped_must_be_commander:,}",
                "warnings": "; ".join(warnings),
                "error": "",
            })
        except Exception as exc:
            results.append({"deck": str(deck_path), "warnings": "", "error": str(exc)})

    stress_output_path.parent.mkdir(parents=True, exist_ok=True)
    stress_output_path.write_text(
        build_stress_markdown(
            deck_results=results,
            strict_index_path=index_path,
            parity_index_path=parity_source,
            parity_metadata=parity_metadata,
            include_maybeboard=args.include_maybeboard,
            include_tokens=args.include_tokens,
            collection_loaded=collection_loaded,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote stress-test markdown: {stress_output_path}")
    print("Done. No app integration was performed.")
    return 0


def main() -> int:
    args = parse_args()

    # v0.8.7.2.1-dev: the compact dashboard is the default output.
    # --combo-finder-check and --verification-counts are kept as harmless aliases
    # for older muscle memory, but they no longer prompt for expected counts.
    if args.stress_test:
        return run_stress_test(args)

    if args.deck:
        deck_path = Path(args.deck)
    else:
        try:
            if args.terminal_picker:
                deck_path = choose_deck_file_terminal(Path(args.deck_dir))
            else:
                deck_path = choose_deck_file_with_tkinter(Path(args.deck_dir))
                if deck_path is None:
                    print("Tkinter file picker unavailable. Falling back to terminal deck selection.")
                    deck_path = choose_deck_file_terminal(Path(args.deck_dir))
        except KeyboardInterrupt as exc:
            print(f"\n{exc}")
            return 0
        except Exception as exc:
            print("\nERROR: Could not select decklist.")
            print(str(exc))
            return 2

    index_path = Path(args.index)
    parity_index_path = Path(args.parity_index)
    scryfall_path = Path(args.scryfall)
    collection_dir = None if args.no_collection else Path(args.collection_dir)
    summary_path = Path(args.summary)
    reconciliation_path = Path(args.reconciliation)
    breakdown_path = Path(args.breakdown)

    print("v0.8.7.2.1-dev — Combo Matcher Dashboard, Breakdown, and Stress Test")
    print("================================================================")
    print("Loading local files only. No API calls will be made...")
    print(f"Deck file: {deck_path}")
    print(f"Combo index: {index_path}")

    try:
        deck = parse_decklist(
            deck_path,
            explicit_commanders=args.commander,
            include_maybeboard=args.include_maybeboard,
            include_tokens=args.include_tokens,
        )
    except Exception as exc:
        print("\nERROR: Could not parse decklist.")
        print(str(exc))
        return 2

    try:
        combo_index = load_combo_index(index_path)
    except Exception as exc:
        print("\nERROR: Could not load combo index.")
        print(str(exc))
        print("Run this first: python tools/build_combo_index.py")
        return 3

    explicit_identity = canonical_identity(args.commander_identity) if args.commander_identity else None
    scryfall_identity_by_name = {}
    inferred_identity = None
    if explicit_identity is None and not args.no_strict_color:
        scryfall_identity_by_name = load_scryfall_name_identity_map(scryfall_path)
        inferred_identity = infer_commander_identity(deck, scryfall_identity_by_name)

    commander_identity = explicit_identity if explicit_identity is not None else inferred_identity
    strict_color = not args.no_strict_color

    collection = None
    collection_loaded = False
    if collection_dir is not None:
        print(f"Collection folder: {collection_dir}")
        collection = load_collection_index(collection_dir)
        collection_loaded = bool(collection.cards_by_normalized_name)

    combo_finder_combos = None
    combo_finder_path = Path(args.combo_finder) if args.combo_finder else None
    if combo_finder_path is not None:
        try:
            combo_finder_combos = parse_combo_finder_file(combo_finder_path)
        except Exception as exc:
            print("\nWARNING: Could not parse Combo Finder comparison file.")
            print(str(exc))
            combo_finder_combos = None

    print("\nDeck Summary")
    print("------------")
    print(f"Commanders detected: {', '.join(deck.commander_names) if deck.commander_names else 'Not detected'}")
    print(f"Cards parsed including commanders: {len(deck.all_card_names):,}")
    print(f"Unique normalized cards parsed: {len(deck.normalized_all_cards):,}")
    print(f"Maybeboard included: {'Yes' if args.include_maybeboard else 'No'}")
    print(f"Tokens/Extras included: {'Yes' if args.include_tokens else 'No'}")
    print(f"Commander identity used: {identity_to_string(commander_identity) if commander_identity is not None else 'Unavailable/not applied'}")
    if strict_color and commander_identity is None:
        print("WARNING: Strict color filtering requested, but commander identity could not be determined.")
        print("         Color filtering will not be applied unless you provide --commander-identity or local Scryfall data can resolve it.")

    print("\nMatching against combo index...")
    summary = match_deck_to_combo_index(
        deck,
        combo_index,
        commander_identity=commander_identity,
        collection=collection,
        include_spoilers=args.include_spoilers,
        strict_color_identity=strict_color,
        hide_invalid_must_be_commander=True,
    )

    # Dashboard output is now the default mode. It runs three count profiles:
    # 1. Dragon's Touch strict mode (future user-facing baseline)
    # 2. Combo Finder parity mode (parity index, color ON, mustBeCommander ignored)
    # 3. All raw potential mode (parity index, no filters)
    parity_index = combo_index
    parity_source = parity_index_path
    if parity_index_path.exists():
        try:
            parity_index = load_combo_index(parity_index_path)
            parity_source = parity_index_path
        except Exception as exc:
            print(f"\nWARNING: Could not load parity index `{parity_index_path}`. Using normal index instead.")
            print(str(exc))
            parity_source = index_path
    else:
        print(f"\nWARNING: Parity index not found: {parity_index_path}")
        print("Using the normal index for parity/all-raw counts. If this misses Combo Finder results,")
        print("build a parity index first with:")
        print("  python tools/build_combo_index.py --include-non-commander-legal --output data/commander_spellbook/combo_index_parity.json --summary docs/combo_index_parity_summary_v0.8.7.2.1-dev.md")
        parity_source = index_path

    parity_summary = match_deck_to_combo_index(
        deck,
        parity_index,
        commander_identity=commander_identity,
        collection=collection,
        include_spoilers=args.include_spoilers,
        strict_color_identity=strict_color,
        hide_invalid_must_be_commander=False,
    )

    raw_summary = match_deck_to_combo_index(
        deck,
        parity_index,
        commander_identity=None,
        collection=collection,
        include_spoilers=True,
        strict_color_identity=False,
        hide_invalid_must_be_commander=False,
    )

    parity_metadata = parity_index.get("metadata", {}) if isinstance(parity_index, dict) else {}
    print_dashboard(
        strict_summary=summary,
        parity_summary=parity_summary,
        raw_summary=raw_summary,
        strict_index_path=index_path,
        parity_index_path=parity_source,
        parity_metadata=parity_metadata,
        collection_loaded=collection_loaded,
    )

    if args.write_breakdown:
        breakdown_path.parent.mkdir(parents=True, exist_ok=True)
        breakdown_potential_limit = 0 if args.show_all_potentials else args.breakdown_potential_limit
        breakdown_markdown = build_combo_breakdown_markdown(
            deck=deck,
            strict_summary=summary,
            commander_identity=commander_identity,
            index_metadata=combo_index.get("metadata", {}),
            collection_loaded=collection_loaded,
            parity_summary=parity_summary,
            raw_summary=raw_summary,
            parity_index_metadata=parity_metadata,
            max_complete=args.breakdown_complete_limit,
            max_potential=breakdown_potential_limit,
        )
        breakdown_path.write_text(breakdown_markdown, encoding="utf-8")
        print(f"\nWrote combo awareness breakdown: {breakdown_path}")

    if args.write_report_section:
        report_section_path = Path(args.report_section)
        report_section_path.parent.mkdir(parents=True, exist_ok=True)
        report_section_markdown = build_combo_report_section_markdown(
            deck=deck,
            strict_summary=summary,
            commander_identity=commander_identity,
            collection_loaded=collection_loaded,
            max_complete=args.report_section_complete_limit,
            max_collection_potential=args.report_section_potential_limit,
        )
        report_section_path.write_text(report_section_markdown, encoding="utf-8")
        print(f"\nWrote combo awareness report section: {report_section_path}")

    if args.write_reconciliation:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = build_markdown_summary(
            deck=deck,
            summary=summary,
            commander_identity=commander_identity,
            index_metadata=combo_index.get("metadata", {}),
            max_complete=args.show_complete,
            max_potential=args.show_potential,
            include_spoilers=args.include_spoilers,
            collection_loaded=collection_loaded,
        )
        summary_path.write_text(markdown, encoding="utf-8")

        reconciliation_path.parent.mkdir(parents=True, exist_ok=True)
        reconciliation_markdown = build_reconciliation_markdown(
            deck=deck,
            summary=summary,
            commander_identity=commander_identity,
            index_metadata=combo_index.get("metadata", {}),
            include_spoilers=args.include_spoilers,
            collection_loaded=collection_loaded,
            expected_complete_count=args.expected_complete_count,
            expected_potential_count=args.expected_potential_count,
            combo_finder_path=combo_finder_path,
            combo_finder_combos=combo_finder_combos,
        )
        reconciliation_path.write_text(reconciliation_markdown, encoding="utf-8")
        print(f"\nWrote reconciliation/debug file: {reconciliation_path}")
        print(f"Wrote isolated matcher summary: {summary_path}")
    else:
        print("\nNo full markdown report was written. Use --write-reconciliation for full debug files.")

    print("Done. No app integration was performed.")
    return 0



if __name__ == "__main__":
    sys.exit(main())
