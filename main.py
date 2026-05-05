"""Modular cleanup entry point for MTG Deck Helper v0.6.2-clean.6.

Round 8 cleanup goal:
- Keep the modular orchestration from Round 7.
- Add QA, parity, smoke-test, and buddy-handoff material around it.

Important: the legacy v0.6.2.6 monolith remains the behavior reference until
full parity testing is complete. This cleanup version is now runnable as a
modular checkpoint, but it should not be treated as a feature-upgraded release.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deck_helper.analysis.bracket_analysis import build_bracket_analysis
from deck_helper.analysis.plan_fit import build_plan_fit_summary
from deck_helper.analysis.role_tag_cleanup import apply_role_tag_cleanup
from deck_helper.analysis.role_tags import build_role_analysis
from deck_helper.analysis.strategy_scoring import build_strategy_summary
from deck_helper.config import OUTPUT_FOLDER, SCRYFALL_FILE, RuntimeConfig, get_runtime_config, print_runtime_config_summary
from deck_helper.cuts.cut_pressure import build_cut_pressure_summary
from deck_helper.cuts.possible_cut_review import build_possible_cut_review
from deck_helper.cuts.protected_cards import build_protected_cards
from deck_helper.cuts.replaceability import build_replaceability_review
from deck_helper.cuts.replacement_categories import build_replacement_need_summary
from deck_helper.data.scryfall_loader import ScryfallDataError, load_scryfall_lookup
from deck_helper.io.batch_runner import run_batch
from deck_helper.io.deck_file_picker import resolve_deck_files
from deck_helper.io.output_writer import create_deck_output_folder, merge_debug_reports, write_text_file, get_unique_output_path
from deck_helper.legality.commander_detection import build_command_zone_summary
from deck_helper.legality.commander_legality import build_commander_legality_summary
from deck_helper.parsing.deck_parser import ParsedDeck, parse_deck_file
from deck_helper.replacements.collection_candidates import build_collection_candidate_summary
from deck_helper.replacements.deck_completion import build_deck_completion_summary
from deck_helper.reports.debug_sections import DebugSectionPaths, write_debug_sections
from deck_helper.reports.prompt_builder import write_user_guided_prompt
from deck_helper.reports.report_builder import write_normal_report


VERSION_LABEL = "v0.6.2-clean.7 — QA / Parity Handoff"


def build_analysis_context(
    parsed_deck: ParsedDeck,
    runtime_config: RuntimeConfig,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    command_zone = build_command_zone_summary(parsed_deck, scryfall_lookup)
    legality = build_commander_legality_summary(parsed_deck, command_zone, scryfall_lookup)
    raw_roles = build_role_analysis(parsed_deck, scryfall_lookup, command_zone)
    role_summary = apply_role_tag_cleanup(raw_roles)
    strategy_summary = build_strategy_summary(
        role_summary.role_counts,
        role_summary.type_counts,
        command_zone.commander_cards_scryfall,
    )
    plan_fit_summary = build_plan_fit_summary(role_summary.card_roles, strategy_summary)
    bracket_summary = build_bracket_analysis(role_summary)
    protected_cards = build_protected_cards(role_summary.card_roles, plan_fit_summary, command_zone)
    replaceability = build_replaceability_review(role_summary.card_roles, plan_fit_summary, protected_cards)
    cut_pressure = build_cut_pressure_summary(parsed_deck.deck_card_count, runtime_config, replaceability)
    possible_cuts = build_possible_cut_review(cut_pressure, replaceability)
    replacement_needs = build_replacement_need_summary(
        role_summary.role_counts,
        strategy_summary,
        parsed_deck.deck_card_count,
    )
    deck_completion = build_deck_completion_summary(
        parsed_deck,
        runtime_config,
        strategy_summary,
        replacement_needs,
    )
    collection_candidates = build_collection_candidate_summary()

    return {
        "version_label": VERSION_LABEL,
        "runtime_config": runtime_config,
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
    deck_folder = create_deck_output_folder(parsed_deck.safe_commander_name, OUTPUT_FOLDER)
    written_paths: list[Path] = []

    if not scryfall_lookup:
        written_paths.append(write_parser_only_checkpoint(deck_folder, parsed_deck))
        return written_paths

    context = build_analysis_context(parsed_deck, runtime_config, scryfall_lookup)
    output_mode = runtime_config.output_mode

    if output_mode in {"normal", "both"}:
        written_paths.append(write_normal_report(deck_folder, parsed_deck.safe_commander_name, context))
        written_paths.append(write_user_guided_prompt(deck_folder, parsed_deck.safe_commander_name, context))

    if output_mode in {"debug", "both"}:
        debug_paths: DebugSectionPaths = write_debug_sections(deck_folder, parsed_deck.safe_commander_name, context)
        section_paths = [
            debug_paths.legality,
            debug_paths.strategy,
            debug_paths.bracket,
            debug_paths.cut_pressure,
            debug_paths.replacement_prompt,
            debug_paths.diagnostics,
        ]
        written_paths.extend(section_paths)
        written_paths.append(merge_debug_reports(deck_folder, parsed_deck.safe_commander_name, section_paths))

    return written_paths


def main() -> None:
    print(f"RUNNING MTG DECK HELPER {VERSION_LABEL}")
    deck_files = resolve_deck_files()
    runtime_config = get_runtime_config()

    if len(deck_files) > 1:
        run_batch(deck_files, runtime_config, Path(__file__))
        return

    print()
    print(f"Selected deck file: {deck_files[0]}")
    print_runtime_config_summary(runtime_config)

    scryfall_lookup: dict[str, dict[str, Any]] = {}
    scryfall_error: Exception | None = None
    try:
        scryfall_cards, scryfall_lookup = load_scryfall_lookup(SCRYFALL_FILE)
        print(f"Scryfall data loaded: {len(scryfall_cards)} cards")
    except ScryfallDataError as exc:
        scryfall_error = exc
        print(f"Scryfall data not loaded: {exc}")
        print("A parser-only checkpoint will be written.")

    if scryfall_error:
        parsed_deck = parse_deck_file(deck_files[0], scryfall_lookup={})
        deck_folder = create_deck_output_folder(parsed_deck.safe_commander_name, OUTPUT_FOLDER)
        written_paths = [write_parser_only_checkpoint(deck_folder, parsed_deck, scryfall_error)]
    else:
        written_paths = process_single_deck(deck_files[0], runtime_config, scryfall_lookup)

    print()
    print("Round 8 modular output complete.")
    print("Files written:")
    for path in written_paths:
        print(f"- {path}")
    print()
    print("Cleanup note: compare these outputs against deck_helper_v0.6.2.6.py before replacing the stable monolith.")


if __name__ == "__main__":
    main()
