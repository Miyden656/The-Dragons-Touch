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
from analysis.multiplayer_signal import build_multiplayer_summary
from analysis.political_archetypes import classify_political_archetypes
from analysis.political_signals import build_political_signal_profile
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
    # Additive 4-player pod-value signal. Reads existing outputs only; does NOT
    # feed back into the v1.6 scoring chain above (role/strategy/bracket unchanged).
    # Shared political signal profile — computed ONCE, consumed by both the
    # multiplayer pod-value signal (goad/pillowfort/instant-speed) and the
    # Section-3 political-archetype classifier. Single source of political truth.
    political_profile = build_political_signal_profile(role_summary, command_zone, scryfall_lookup)
    multiplayer_summary = build_multiplayer_summary(
        role_summary, command_zone, bracket_summary, scryfall_lookup,
        political_profile=political_profile,
    )
    # Additive Section-3 political-archetype classification. Parallel to the v1.6
    # strategy read (does not modify it); reads existing outputs + the profile.
    political_summary = classify_political_archetypes(political_profile)
    philosophy_context = build_philosophy_context(
        key=resolved_config.philosophy_key,
        guide_preference=resolved_config.guide_preference,
    )
    protected_cards = build_protected_cards(role_summary.card_roles, plan_fit_summary, command_zone)
    replaceability = build_replaceability_review(role_summary.card_roles, plan_fit_summary, protected_cards, philosophy_context)
    cut_pressure = build_cut_pressure_summary(parsed_deck.deck_card_count, resolved_config, replaceability)
    possible_cuts = build_possible_cut_review(cut_pressure, replaceability)
    # Presentation/intent-honoring: respect the pilot's never-cut declaration (pet +
    # rescue cards from the intake windows) by moving any such card out of the cut
    # candidates into protected. Does NOT change any cut/replaceability score. Fixes
    # both the report and the AI guide at once (both read this possible_cuts).
    from analysis.pilot_intent import (
        apply_pilot_protection_to_cuts,
        pilot_intent_from_runtime_config,
    )
    _pilot_protected = pilot_intent_from_runtime_config(runtime_config).protected_cards
    if _pilot_protected:
        possible_cuts = apply_pilot_protection_to_cuts(possible_cuts, _pilot_protected)
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
        "multiplayer_summary": multiplayer_summary,
        "political_summary": political_summary,
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


def process_single_deck(
    deck_file: Path,
    runtime_config: RuntimeConfig,
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    collection_summary: CollectionLoadSummary | None = None,
    *,
    batch_output_folder: bool = False,
) -> list[Path]:
    scryfall_lookup = scryfall_lookup or {}
    parsed_deck = parse_deck_file(deck_file, scryfall_lookup=scryfall_lookup)
    # v0.6.8.2.1 regression hotfix:
    # Always create a unique per-run output folder. This restores the locked
    # v0.6.7.9.17 behavior that preserves commander identity, source deck-file
    # distinction, and a run timestamp instead of merging repeated runs into a
    # plain commander-name folder.
    output_deck_name = make_run_output_deck_name(parsed_deck.safe_commander_name, deck_file)
    folders = create_unique_run_output_folders(output_deck_name, RUNTIME_OUTPUT_FOLDER)
    written_paths: list[Path] = []

    if not scryfall_lookup:
        written_paths.append(write_parser_only_checkpoint(folders.normal, parsed_deck))
        # v1.4.21 Strategy Knowledge Main Pipeline Opt-In Live Bridge.
        # This is opt-in via TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE and writes bridge artifacts only.
        # It does not export a final deck, lock final inclusions, generate a finished mana base, or write lands into a deck.
        written_paths.extend(
        write_strategy_knowledge_live_bridge_artifacts(
        normal_folder=folders.normal,
        safe_commander_name=parsed_deck.safe_commander_name,
        context=context,
        )
        )

        assert_output_routing(written_paths, folders.normal, folders.debug)

        return written_paths

    context = build_analysis_context(parsed_deck, runtime_config, scryfall_lookup, collection_summary)
    resolved_config: RuntimeConfig = context["runtime_config"]
    output_mode = resolved_config.output_mode

    normal_report_path: Path | None = None
    user_prompt_path: Path | None = None
    if output_mode in {"normal", "both"}:
        normal_report_path = write_normal_report(folders.normal, parsed_deck.safe_commander_name, context)
        written_paths.append(normal_report_path)
        user_prompt_path = write_user_guided_prompt(folders.normal, parsed_deck.safe_commander_name, context)
        written_paths.append(user_prompt_path)

    if output_mode in {"debug", "both"}:
        debug_paths: DebugSectionPaths = write_debug_sections(folders.debug, parsed_deck.safe_commander_name, context)
        section_paths = [
            debug_paths.legality,
            debug_paths.strategy,
            debug_paths.bracket,
            debug_paths.cut_pressure,
            debug_paths.replacement_prompt,
            debug_paths.diagnostics,
        ]
        written_paths.extend(section_paths)
        written_paths.append(merge_debug_reports(folders.debug, parsed_deck.safe_commander_name, section_paths))

    # v1.4-expanded-strategy-scoring: combo awareness remains optional and off by default.
    # When the user explicitly selects a report-section mode, write the separate
    # combo artifact and append the same concise, user-facing section to the
    # normal deck report when one exists. Breakdown-only mode stays dev-facing.
    written_paths.extend(
        write_optional_combo_awareness_artifacts(
            deck_file=deck_file,
            runtime_config=resolved_config,
            normal_folder=folders.normal,
            debug_folder=folders.debug,
            scryfall_lookup=scryfall_lookup,
            normal_report_path=normal_report_path,
            user_prompt_path=user_prompt_path,
        )
    )

    assert_output_routing(written_paths, folders.normal, folders.debug)
    return written_paths


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


def run_many_decks(
    deck_files: list[Path],
    runtime_config: RuntimeConfig,
    scryfall_lookup: dict[str, dict[str, Any]],
    collection_summary: CollectionLoadSummary | None = None,
) -> None:
    print()
    print(f"Batch mode: {len(deck_files)} deck files selected.")
    print_runtime_config_summary(runtime_config)
    print()

    aggregate_writer = BatchAggregateWriter.create(
        base_folder=RUNTIME_BATCH_AGGREGATE_OUTPUT_FOLDER,
        version_label=VERSION_LABEL,
        runtime_config=runtime_config,
        deck_count=len(deck_files),
    )
    print(f"Batch aggregate folder: {aggregate_writer.run_folder}")
    print()

    successes = 0
    failures: list[tuple[Path, str]] = []
    for index, deck_file in enumerate(deck_files, start=1):
        print(f"Running deck helper for: {deck_file}")
        try:
            written = process_single_deck(deck_file, runtime_config, scryfall_lookup, collection_summary, batch_output_folder=True)
            successes += 1
            aggregate_writer.add_success(index=index, deck_file=deck_file, written_paths=written)
            print(f"  Success. Files written: {len(written)}")
        except Exception as exc:  # noqa: BLE001 - stress-test mode should continue.
            failures.append((deck_file, str(exc)))
            aggregate_writer.add_failure(index=index, deck_file=deck_file, error=exc)
            print(f"  FAILED: {exc}")
        print()

    aggregate_paths = aggregate_writer.finalize(success_count=successes, failures=failures)

    print("Batch run complete.")
    print("Final Summary:")
    print(f"- Decks processed: {len(deck_files)}")
    print(f"- Successes: {successes}")
    print(f"- Failures: {len(failures)}")
    for path, error in failures:
        print(f"  - {path.name}: {error}")
    print("- Batch aggregate reports:")
    print(f"  - Deck reports: {aggregate_paths.deck_reports}")
    print(f"  - Debug reports: {aggregate_paths.debug_reports}")


def main() -> None:
    print(f"RUNNING THE DRAGON'S TOUCH {VERSION_LABEL}")
    print(f"Runtime root: {_RUNTIME_PATHS.root}")
    print(f"Runtime data folder: {_RUNTIME_PATHS.data_dir}")
    deck_files = resolve_deck_files()
    runtime_config = get_runtime_config()
    scryfall_cards, scryfall_lookup, scryfall_error = load_scryfall_or_none()
    collection_summary = load_collection_summary(runtime_config, scryfall_lookup, scryfall_cards)

    if len(deck_files) > 1:
        run_many_decks(deck_files, runtime_config, scryfall_lookup, collection_summary)
        return

    print()
    print(f"Selected deck file: {deck_files[0]}")
    print_runtime_config_summary(runtime_config)

    if scryfall_error:
        parsed_deck = parse_deck_file(deck_files[0], scryfall_lookup={})
        output_deck_name = make_run_output_deck_name(parsed_deck.safe_commander_name, deck_files[0])
        folders = create_unique_run_output_folders(output_deck_name, RUNTIME_OUTPUT_FOLDER)
        written_paths = [write_parser_only_checkpoint(folders.normal, parsed_deck, scryfall_error)]
    else:
        written_paths = process_single_deck(deck_files[0], runtime_config, scryfall_lookup, collection_summary)

    print()
    print("The Dragon's Touch output complete.")
    print("Files written:")
    for path in written_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
