"""The Dragon's Touch — modular cleanup entry point.

Clean.8.5 rebuild goals:
- Use only top-level packages; no nested deck_helper package imports.
- Route normal and debug outputs through one enforced output-folder API.
- Auto batch mode uses deck size and never prompts per deck.
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
    create_deck_output_folder,
    create_deck_output_folders,
    get_unique_output_path,
    merge_debug_reports,
    write_text_file,
)
from config import (
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
from data.scryfall_loader import ScryfallDataError, load_scryfall_lookup
from legality.commander_detection import build_command_zone_summary
from legality.commander_legality import build_commander_legality_summary
from parsing.deck_parser import ParsedDeck, parse_deck_file
from replacements.collection_candidates import build_collection_candidate_summary
from replacements.deck_completion import build_deck_completion_summary
from reports.debug_sections import DebugSectionPaths, write_debug_sections
from reports.prompt_builder import write_user_guided_prompt
from reports.report_builder import write_normal_report


VERSION_LABEL = "v0.6.2-clean.8.6 — philosophy layer MVP"


def build_analysis_context(parsed_deck: ParsedDeck, runtime_config: RuntimeConfig, scryfall_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    resolved_config = resolve_runtime_config_for_deck_size(runtime_config, parsed_deck.deck_card_count)
    command_zone = build_command_zone_summary(parsed_deck, scryfall_lookup)
    legality = build_commander_legality_summary(parsed_deck, command_zone, scryfall_lookup)
    raw_roles = build_role_analysis(parsed_deck, scryfall_lookup, command_zone)
    role_summary = apply_role_tag_cleanup(raw_roles)
    strategy_summary = build_strategy_summary(role_summary.role_counts, role_summary.type_counts, command_zone.commander_cards_scryfall)
    plan_fit_summary = build_plan_fit_summary(role_summary.card_roles, strategy_summary, command_zone.commander_names)
    bracket_summary = build_bracket_analysis(role_summary)
    protected_cards = build_protected_cards(role_summary.card_roles, plan_fit_summary, command_zone)
    replaceability = build_replaceability_review(role_summary.card_roles, plan_fit_summary, protected_cards)
    cut_pressure = build_cut_pressure_summary(parsed_deck.deck_card_count, resolved_config, replaceability)
    possible_cuts = build_possible_cut_review(cut_pressure, replaceability)
    replacement_needs = build_replacement_need_summary(role_summary.role_counts, strategy_summary, parsed_deck.deck_card_count)
    deck_completion = build_deck_completion_summary(parsed_deck, resolved_config, strategy_summary, replacement_needs)
    collection_candidates = build_collection_candidate_summary()
    philosophy_context = build_philosophy_context(
        key=resolved_config.philosophy_key,
        guide_preference=resolved_config.guide_preference,
    )

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
        "collection_candidates": collection_candidates,
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


def process_single_deck(deck_file: Path, runtime_config: RuntimeConfig, scryfall_lookup: dict[str, dict[str, Any]] | None = None) -> list[Path]:
    scryfall_lookup = scryfall_lookup or {}
    parsed_deck = parse_deck_file(deck_file, scryfall_lookup=scryfall_lookup)
    folders = create_deck_output_folders(parsed_deck.safe_commander_name, OUTPUT_FOLDER)
    written_paths: list[Path] = []

    if not scryfall_lookup:
        written_paths.append(write_parser_only_checkpoint(folders.normal, parsed_deck))
        assert_output_routing(written_paths, folders.normal, folders.debug)
        return written_paths

    context = build_analysis_context(parsed_deck, runtime_config, scryfall_lookup)
    resolved_config: RuntimeConfig = context["runtime_config"]
    output_mode = resolved_config.output_mode

    if output_mode in {"normal", "both"}:
        written_paths.append(write_normal_report(folders.normal, parsed_deck.safe_commander_name, context))
        written_paths.append(write_user_guided_prompt(folders.normal, parsed_deck.safe_commander_name, context))

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

    assert_output_routing(written_paths, folders.normal, folders.debug)
    return written_paths


def load_scryfall_or_none() -> tuple[dict[str, dict[str, Any]], Exception | None]:
    try:
        scryfall_cards, scryfall_lookup = load_scryfall_lookup(SCRYFALL_FILE)
        print(f"Scryfall data loaded: {len(scryfall_cards)} cards")
        return scryfall_lookup, None
    except ScryfallDataError as exc:
        print(f"Scryfall data not loaded: {exc}")
        print("A parser-only checkpoint will be written.")
        return {}, exc


def run_many_decks(deck_files: list[Path], runtime_config: RuntimeConfig, scryfall_lookup: dict[str, dict[str, Any]]) -> None:
    print()
    print(f"Batch mode: {len(deck_files)} deck files selected.")
    print_runtime_config_summary(runtime_config)
    print()
    successes = 0
    failures: list[tuple[Path, str]] = []
    for deck_file in deck_files:
        print(f"Running deck helper for: {deck_file}")
        try:
            written = process_single_deck(deck_file, runtime_config, scryfall_lookup)
            successes += 1
            print(f"  Success. Files written: {len(written)}")
        except Exception as exc:  # noqa: BLE001 - stress-test mode should continue.
            failures.append((deck_file, str(exc)))
            print(f"  FAILED: {exc}")
        print()
    print("Batch run complete.")
    print("Final Summary:")
    print(f"- Decks processed: {len(deck_files)}")
    print(f"- Successes: {successes}")
    print(f"- Failures: {len(failures)}")
    for path, error in failures:
        print(f"  - {path.name}: {error}")


def main() -> None:
    print(f"RUNNING THE DRAGON'S TOUCH {VERSION_LABEL}")
    deck_files = resolve_deck_files()
    runtime_config = get_runtime_config()
    scryfall_lookup, scryfall_error = load_scryfall_or_none()

    if len(deck_files) > 1:
        run_many_decks(deck_files, runtime_config, scryfall_lookup)
        return

    print()
    print(f"Selected deck file: {deck_files[0]}")
    print_runtime_config_summary(runtime_config)

    if scryfall_error:
        parsed_deck = parse_deck_file(deck_files[0], scryfall_lookup={})
        folders = create_deck_output_folders(parsed_deck.safe_commander_name, OUTPUT_FOLDER)
        written_paths = [write_parser_only_checkpoint(folders.normal, parsed_deck, scryfall_error)]
    else:
        written_paths = process_single_deck(deck_files[0], runtime_config, scryfall_lookup)

    print()
    print("The Dragon's Touch output complete.")
    print("Files written:")
    for path in written_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
