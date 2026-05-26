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

def build_analysis_context(
    parsed_deck: ParsedDeck,
    runtime_config: RuntimeConfig,
    scryfall_lookup: dict[str, dict[str, Any]],
    collection_summary: CollectionLoadSummary | None = None,
) -> dict[str, Any]:
    resolved_config = resolve_runtime_config_for_deck_size(runtime_config, parsed_deck.deck_card_count)
    command_zone = build_command_zone_summary(parsed_deck, scryfall_lookup)
    legality = build_commander_legality_summary(parsed_deck, command_zone, scryfall_lookup)
    raw_roles = build_role_analysis(parsed_deck, scryfall_lookup, command_zone)
    role_summary = apply_role_tag_cleanup(raw_roles)
    strategy_summary = build_strategy_summary(role_summary.role_counts, role_summary.type_counts, command_zone.commander_cards_scryfall)
    plan_fit_summary = build_plan_fit_summary(role_summary.card_roles, strategy_summary, command_zone.commander_names)
    bracket_summary = build_bracket_analysis(role_summary)
    philosophy_context = build_philosophy_context(
        key=resolved_config.philosophy_key,
        guide_preference=resolved_config.guide_preference,
    )
    protected_cards = build_protected_cards(role_summary.card_roles, plan_fit_summary, command_zone)
    replaceability = build_replaceability_review(role_summary.card_roles, plan_fit_summary, protected_cards, philosophy_context)
    cut_pressure = build_cut_pressure_summary(parsed_deck.deck_card_count, resolved_config, replaceability)
    possible_cuts = build_possible_cut_review(cut_pressure, replaceability)
    replacement_needs = build_replacement_need_summary(role_summary.role_counts, strategy_summary, parsed_deck.deck_card_count)
    deck_completion = build_deck_completion_summary(parsed_deck, resolved_config, strategy_summary, replacement_needs)
    collection_candidates = build_collection_candidate_summary(
        collection_summary=collection_summary,
        replacement_needs=replacement_needs,
        parsed_deck=parsed_deck,
        command_zone=command_zone,
        legality=legality,
        scryfall_lookup=scryfall_lookup,
        strategy_summary=strategy_summary,
        runtime_config=resolved_config,
        philosophy_context=philosophy_context,
    )
    replacement_candidates = build_replacement_candidate_summary(
        collection_candidates=collection_candidates,
        replacement_needs=replacement_needs,
        strategy_summary=strategy_summary,
        runtime_config=resolved_config,
        philosophy_context=philosophy_context,
    )
    replacement_candidates = apply_collection_first_confidence_ceiling(replacement_candidates)
    replacement_candidates = apply_dragon_need_semantic_gate(replacement_candidates)
    replacement_candidates = apply_dragon_gate_visible_field_rewrite(replacement_candidates)

    return {
        "version_label": VERSION_LABEL,
        "runtime_config": resolved_config,
        "original_runtime_config": runtime_config,
        "parsed_deck": parsed_deck,
        "command_zone": command_zone,
        "legality": legality,
        "role_summary": role_summary,
        "strategy_summary": strategy_summary,
        "plan_fit_summary": plan_fit_summary,
        "bracket_summary": bracket_summary,
        "protected_cards": protected_cards,
        "replaceability": replaceability,
        "cut_pressure": cut_pressure,
        "possible_cuts": possible_cuts,
        "replacement_needs": replacement_needs,
        "deck_completion": deck_completion,
        "replacement_candidates": replacement_candidates,
        "collection_candidates": collection_candidates,
        "collection_summary": collection_summary or CollectionLoadSummary(),
        "philosophy_context": philosophy_context,
    }

def load_scryfall_or_none() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], Exception | None]:
    try:
        scryfall_cards, scryfall_lookup = load_scryfall_lookup(RUNTIME_SCRYFALL_FILE)
        print(f"Scryfall data loaded: {len(scryfall_cards)} cards")
        return scryfall_cards, scryfall_lookup, None
    except ScryfallDataError as exc:
        print(f"Scryfall data not loaded: {exc}")
        print("A parser-only checkpoint will be written.")
        return [], {}, exc

def load_collection_summary(
    runtime_config: RuntimeConfig,
    scryfall_lookup: dict[str, dict[str, Any]],
    scryfall_cards: list[dict[str, Any]] | None = None,
) -> CollectionLoadSummary:
    summary = load_collection_sources(
        runtime_config.collection_files,
        mode=runtime_config.collection_mode,
        scryfall_lookup=scryfall_lookup,
        scryfall_cards=scryfall_cards,
        source_mode=getattr(runtime_config, "collection_source_mode", "selected_files"),
        collection_folder=getattr(runtime_config, "collection_file", ""),
    )
    if runtime_config.collection_mode == "none":
        print("Collection mode: off")
        return summary

    print(f"Collection mode: {runtime_config.collection_mode}")
    print(f"Collection source mode: {getattr(runtime_config, 'collection_source_mode', 'selected_files')}")
    if getattr(runtime_config, "collection_source_mode", "") == "entire_collection_folder":
        print(f"Collection folder: {runtime_config.collection_file}")
        print(f"Collection text files selected: {len(runtime_config.collection_files)}")
    else:
        print(f"Selected collection files: {len(runtime_config.collection_files)}")
        for path in runtime_config.collection_files[:5]:
            print(f"  - {Path(path).name}")
        if len(runtime_config.collection_files) > 5:
            print(f"  - ...and {len(runtime_config.collection_files) - 5} more")

    if not summary.file_exists:
        print("Collection file(s) not found; collection candidates will be unavailable.")
    elif summary.loaded:
        print(f"Collection loaded: {summary.total_cards} total cards; {summary.unique_cards} unique names")
        if summary.not_found_cards:
            print(f"Collection cards not found in Scryfall: {len(summary.not_found_cards)}")
    return summary
