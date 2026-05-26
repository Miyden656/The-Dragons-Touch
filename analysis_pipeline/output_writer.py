"""The Dragon's Touch — modular cleanup entry point.

Patch Batch 8 rebuild goals:
- Use only top-level packages; no nested deck_helper package imports.
- Route normal and debug outputs through one enforced output-folder API.
- Auto batch mode uses deck size and never prompts per deck.
- Batch mode uses deck-file-aware output folders to avoid duplicate commander collisions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.bracket_analysis import build_bracket_analysis
from analysis.deck_building_philosophies import build_philosophy_context
from analysis.plan_fit import build_plan_fit_summary
from analysis.role_tag_cleanup import apply_role_tag_cleanup
from analysis.role_tags import build_role_analysis
from analysis.strategy_scoring import build_strategy_summary
from app_io.deck_file_picker import resolve_deck_files
from app_io.output_writer import (
    assert_output_routing,
    create_unique_run_output_folders,
    get_unique_output_path,
    make_run_output_deck_name,
    merge_debug_reports,
    write_text_file,
)
from config import (
    BATCH_AGGREGATE_OUTPUT_FOLDER,
    OUTPUT_FOLDER,
    SCRYFALL_FILE,
    RuntimeConfig,
    get_runtime_config,
    print_runtime_config_summary,
    resolve_runtime_config_for_deck_size,
)
from cuts.cut_pressure import build_cut_pressure_summary
from cuts.possible_cut_review import build_possible_cut_review
from cuts.protected_cards import build_protected_cards
from cuts.replaceability import build_replaceability_review
from cuts.replacement_categories import build_replacement_need_summary
from data.collection_loader import CollectionLoadSummary, load_collection_sources
from data.scryfall_loader import ScryfallDataError, load_scryfall_lookup
from legality.commander_detection import build_command_zone_summary
from legality.commander_legality import build_commander_legality_summary
from parsing.deck_parser import ParsedDeck, parse_deck_file
from replacements.collection_candidates import build_collection_candidate_summary
from replacements.replacement_candidates import apply_collection_first_confidence_ceiling, apply_dragon_gate_visible_field_rewrite, apply_dragon_need_semantic_gate, build_replacement_candidate_summary
from replacements.deck_completion import build_deck_completion_summary
from reports.batch_aggregate import BatchAggregateWriter
from reports.debug_sections import DebugSectionPaths, write_debug_sections
from reports.prompt_builder import write_user_guided_prompt
from reports.report_builder import write_normal_report
from reports.strategy_bridge.strategy_live_bridge import write_strategy_knowledge_live_bridge_artifacts  # v1.4.21 Strategy Knowledge opt-in live bridge
from combo_awareness.main_hook import write_optional_combo_awareness_artifacts
from app_io.project_paths import ensure_runtime_folders, get_runtime_paths, runtime_data_status


VERSION_LABEL = "The Dragon's Touch v1.4 Expanded Strategy Scoring — Report schema v1.4"

# v0.11.3-dev: central runtime paths for source mode and PyInstaller EXE mode.
_RUNTIME_PATHS = ensure_runtime_folders()
RUNTIME_SCRYFALL_FILE = _RUNTIME_PATHS.scryfall_cards_json
RUNTIME_OUTPUT_FOLDER = _RUNTIME_PATHS.outputs_dir
RUNTIME_BATCH_AGGREGATE_OUTPUT_FOLDER = _RUNTIME_PATHS.outputs_dir / "_batch_reports"
VERSION_LABEL = "The Dragon's Touch v1.4 Expanded Strategy Scoring — Report schema v1.4"
_RUNTIME_PATHS = ensure_runtime_folders()
RUNTIME_SCRYFALL_FILE = _RUNTIME_PATHS.scryfall_cards_json
RUNTIME_OUTPUT_FOLDER = _RUNTIME_PATHS.outputs_dir
RUNTIME_BATCH_AGGREGATE_OUTPUT_FOLDER = _RUNTIME_PATHS.outputs_dir / "_batch_reports"

def write_parser_only_checkpoint(deck_folder: Path, parsed_deck: ParsedDeck, error: Exception | None = None) -> Path:
    lines = [
        f"# MTG Deck Helper Parser Checkpoint — {parsed_deck.commander_name}",
        "",
        "Scryfall data was not loaded, so legality, strategy, cuts, replacements, and prompt generation were skipped.",
        "",
        f"- Deck file: `{parsed_deck.deck_file}`",
        f"- Deck cards parsed: {parsed_deck.deck_card_count}",
        f"- Unique deck card names: {len(parsed_deck.unique_cards)}",
        f"- Reference/non-mainboard cards ignored: {parsed_deck.reference_card_count}",
        f"- Ignored/unparsed lines: {len(parsed_deck.ignored_lines)}",
        f"- Commander name(s): {parsed_deck.commander_name}",
        f"- Companion name(s): {', '.join(parsed_deck.companion_names) if parsed_deck.companion_names else 'None'}",
    ]
    if error:
        lines.extend(["", "## Scryfall load error", "", f"```text\n{error}\n```"])
    path = get_unique_output_path(deck_folder, f"{parsed_deck.safe_commander_name}_parser_checkpoint", ".md")
    return write_text_file(path, "\n".join(lines))
