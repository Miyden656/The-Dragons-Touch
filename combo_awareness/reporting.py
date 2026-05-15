#!/usr/bin/env python3
"""v0.8.7.2.1-dev — markdown/report formatting for combo awareness.

Scope guard: reporting split only; no wording/behavior changes, no app integration.
"""

from __future__ import annotations

from typing import Any, Iterable

from .matcher import combo_card_names
from .models import DeckData, MatchResult, MatchSummary
from .normalization import identity_to_string, normalize_card_name

def format_combo_result(result: MatchResult) -> list[str]:
    combo = result.combo
    lines: list[str] = []
    lines.append(f"- Combo ID: {combo.get('id')}")
    lines.append(f"  Cards: {', '.join(combo_card_names(combo))}")
    if result.missing_card_names:
        lines.append(f"  Missing: {', '.join(result.missing_card_names)}")
        for missing in result.missing_card_names:
            sources = result.collection_sources_by_missing_card.get(missing, [])
            if sources:
                lines.append(f"  Collection: {missing} found in {', '.join(sources)}")
            else:
                lines.append(f"  Collection: {missing} not found in loaded collection files")
    produces = combo.get("produce_names") or []
    if produces:
        lines.append(f"  Produces: {', '.join(produces[:8])}")
    if combo.get("bracket_tag"):
        lines.append(f"  Bracket tag: {combo.get('bracket_tag')}")
    if combo.get("has_template_requirements"):
        lines.append("  Note: This combo has additional template/state requirements to verify manually.")
    if combo.get("notable_prerequisites"):
        lines.append(f"  Notable prerequisites: {combo.get('notable_prerequisites')}")
    elif combo.get("easy_prerequisites"):
        lines.append(f"  Prerequisites: {combo.get('easy_prerequisites')}")
    return lines

def build_markdown_summary(
    *,
    deck: DeckData,
    summary: MatchSummary,
    commander_identity: set[str] | None,
    index_metadata: dict[str, Any],
    max_complete: int,
    max_potential: int,
    include_spoilers: bool,
    collection_loaded: bool,
) -> str:
    lines: list[str] = [
        "# v0.8.7.2.1-dev — Isolated Combo Matcher Summary",
        "",
        "## Scope Guard",
        "",
        "- No API calls were made.",
        "- No app integration was performed.",
        "- `main.py` was not changed.",
        "- UI and normal report generation were not changed.",
        "- This is an isolated local combo matching test only.",
        "",
        "## Deck",
        "",
        f"- Deck file: `{deck.path}`",
        f"- Commanders detected: {', '.join(deck.commander_names) if deck.commander_names else 'Not detected'}",
        f"- Commander identity used: {identity_to_string(commander_identity) if commander_identity is not None else 'Unavailable/not applied'}",
        f"- Cards parsed including commanders: {len(deck.all_card_names):,}",
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
        "## Filtered / Skipped During Matching",
        "",
        f"- Spoiler-tagged hidden: {summary.skipped_spoiler:,}",
        f"- Color-identity invalid hidden: {summary.skipped_color_identity:,}",
        f"- mustBeCommander invalid hidden: {summary.skipped_must_be_commander:,}",
        f"- Unusable combo shape skipped: {summary.skipped_unusable_shape:,}",
        "",
        "## Complete Combos — Sample",
        "",
    ]

    if summary.complete_combos:
        for result in summary.complete_combos[:max_complete]:
            lines.extend(format_combo_result(result))
            lines.append("")
    else:
        lines.append("No complete known infinite combos were detected.")
        lines.append("")

    if len(summary.complete_combos) > max_complete:
        lines.append(f"Additional complete combos not shown: {len(summary.complete_combos) - max_complete:,}")
        lines.append("")

    lines.extend(["## Potential Combos Missing One Card — Sample", ""])

    if summary.one_card_away_combos:
        for result in summary.one_card_away_combos[:max_potential]:
            lines.extend(format_combo_result(result))
            lines.append("")
    else:
        lines.append("No one-card-away potential infinite combos were detected.")
        lines.append("")

    if len(summary.one_card_away_combos) > max_potential:
        lines.append(f"Additional potential combos not shown: {len(summary.one_card_away_combos) - max_potential:,}")
        lines.append("")

    lines.extend([
        "## Notes",
        "",
        "- These are combo-awareness findings, not automatic recommendations.",
        "- Missing combo cards should not become replacement suggestions unless the user later selects combo optimization.",
        "- Template/state requirements still need manual review before a combo is treated as reliable.",
        "- This isolated matcher is a stepping stone toward a later Breakdown Report.",
        "",
    ])
    return "\n".join(lines)

def _result_has_collection_source(result: MatchResult) -> bool:
    """Return True when at least one missing card was found in loaded collection files."""
    for sources in result.collection_sources_by_missing_card.values():
        if sources:
            return True
    return False

def _combo_size(result: MatchResult) -> int:
    return len(combo_card_names(result.combo))

def _bracket_rank(result: MatchResult) -> int:
    """Lightweight ordering for readability, not a power judgment."""
    order = {
        "E": 0,
        "C": 1,
        "S": 2,
        "R": 3,
        "O": 4,
        "B": 5,
        "P": 6,
    }
    return order.get(str(result.combo.get("bracket_tag") or "").upper(), 99)

def prioritize_potential_results(results: list[MatchResult]) -> list[MatchResult]:
    """Sort potential combos for breakdown readability.

    Priority:
    1. Missing card is already in loaded collection files.
    2. Smaller combo packages first.
    3. Lighter bracket tag ordering for readability.
    4. Stable card-name ordering.

    This does not recommend cards. It only makes the breakdown easier to read.
    """
    return sorted(
        results,
        key=lambda result: (
            not _result_has_collection_source(result),
            _combo_size(result),
            _bracket_rank(result),
            ", ".join(combo_card_names(result.combo)).casefold(),
        ),
    )

def _append_result_block(lines: list[str], heading: str, result: MatchResult) -> None:
    lines.append(heading)
    lines.append("")
    lines.extend(format_combo_result(result))
    lines.append("")

def _missing_card_summary(result: MatchResult) -> str:
    if not result.missing_card_names:
        return "None"
    return ", ".join(result.missing_card_names)

def _append_compact_result_row(lines: list[str], index: int, result: MatchResult) -> None:
    card_names = combo_card_names(result.combo)
    missing = _missing_card_summary(result)
    collection_note = ""
    if result.missing_card_names:
        collection_parts: list[str] = []
        for missing_card in result.missing_card_names:
            sources = result.collection_sources_by_missing_card.get(missing_card, [])
            if sources:
                collection_parts.append(f"{missing_card}: {', '.join(sources)}")
        if collection_parts:
            collection_note = f" — collection: {'; '.join(collection_parts)}"
    template_note = " — verify template/state requirements" if result.combo.get("has_template_requirements") else ""
    lines.append(
        f"{index}. **{', '.join(card_names)}** — missing: {missing}{collection_note}{template_note}"
    )

def _format_concise_combo_line(index: int, result: MatchResult) -> str:
    card_names = " + ".join(combo_card_names(result.combo))
    bracket = result.combo.get("bracket_tag") or result.combo.get("bracket") or "unknown"
    produces = result.combo.get("produces") or []
    if isinstance(produces, list) and produces:
        output = "; ".join(str(item) for item in produces[:3])
        if len(produces) > 3:
            output += "; ..."
    elif produces:
        output = str(produces)
    else:
        output = "Combo output available in full breakdown"
    return f"{index}. **{card_names}** — {output} _(Bracket tag: {bracket})_"

def _unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique

def _collection_sources_for_result(result: MatchResult) -> list[str]:
    sources: list[str] = []
    for missing_card in result.missing_card_names:
        sources.extend(result.collection_sources_by_missing_card.get(missing_card, []))
    return _unique_preserve_order(sources)

def _missing_group_key(result: MatchResult) -> tuple[str, ...]:
    # One-card-away combos normally have one missing card. Keep this tuple-based so
    # future multi-name edge cases still group predictably instead of duplicating rows.
    names = result.missing_card_names or ["Unknown missing card"]
    return tuple(normalize_card_name(name) for name in names)

def _missing_group_display(result: MatchResult) -> str:
    names = result.missing_card_names or ["Unknown missing card"]
    return " + ".join(names)

def _group_collection_potential_results(results: list[MatchResult]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    order: list[tuple[str, ...]] = []

    for result in results:
        key = _missing_group_key(result)
        if key not in grouped:
            grouped[key] = {
                "missing": _missing_group_display(result),
                "sources": [],
                "results": [],
                "bracket_tags": [],
                "examples": [],
            }
            order.append(key)

        group = grouped[key]
        group["results"].append(result)
        group["sources"].extend(_collection_sources_for_result(result))

        bracket = result.combo.get("bracket_tag") or result.combo.get("bracket")
        if bracket:
            group["bracket_tags"].append(str(bracket))

        example = " + ".join(combo_card_names(result.combo))
        if example:
            group["examples"].append(example)

    grouped_rows: list[dict[str, Any]] = []
    for key in order:
        group = grouped[key]
        group["sources"] = _unique_preserve_order(group["sources"])
        group["bracket_tags"] = _unique_preserve_order(group["bracket_tags"])
        group["examples"] = _unique_preserve_order(group["examples"])
        grouped_rows.append(group)

    # Prioritize missing cards that complete the most variants, then those with more
    # collection source certainty, while preserving readable deterministic ordering.
    grouped_rows.sort(
        key=lambda group: (
            -len(group["results"]),
            -len(group["sources"]),
            str(group["missing"]).casefold(),
        )
    )
    return grouped_rows

def _format_grouped_concise_potential_line(index: int, group: dict[str, Any]) -> list[str]:
    missing = group["missing"]
    sources = group.get("sources") or []
    found_in = "; ".join(sources) if sources else "loaded collection files"
    variant_count = len(group.get("results") or [])
    variant_word = "variant" if variant_count == 1 else "variants"
    bracket_tags = group.get("bracket_tags") or []
    bracket_note = f" _(Bracket tags seen: {', '.join(bracket_tags)})_" if bracket_tags else ""

    lines = [
        f"{index}. **{missing}** — found in: `{found_in}`",
        f"   - Completes {variant_count:,} potential combo {variant_word}.{bracket_note}",
    ]

    examples = group.get("examples") or []
    if examples:
        shown_examples = examples[:3]
        lines.append(f"   - Example variant(s): {'; '.join(shown_examples)}")
        if len(examples) > len(shown_examples):
            lines.append(f"   - Additional variants for this missing card are available in the full breakdown.")

    return lines

def build_combo_report_section_markdown(
    *,
    deck: DeckData,
    strict_summary: MatchSummary,
    commander_identity: set[str] | None,
    collection_loaded: bool,
    max_complete: int = 10,
    max_collection_potential: int = 10,
) -> str:
    """Build a concise v0.8.7.2.1-dev combo awareness section for future reports.

    This is still an isolated artifact. It is not injected into the normal Dragon's
    Touch report yet. It intentionally uses only strict Dragon's Touch findings and
    avoids parity/raw debug counts.
    """
    complete_results = strict_summary.complete_combos
    prioritized_potential_results = prioritize_potential_results(strict_summary.one_card_away_combos)
    collection_potential_results = [
        result for result in prioritized_potential_results if _result_has_collection_source(result)
    ]

    shown_complete = complete_results if max_complete == 0 else complete_results[:max_complete]
    grouped_collection_potentials = _group_collection_potential_results(collection_potential_results)
    shown_collection_groups = (
        grouped_collection_potentials
        if max_collection_potential == 0
        else grouped_collection_potentials[:max_collection_potential]
    )

    lines: list[str] = [
        "# v0.8.7.2.1-dev — Isolated Combo Awareness Report Section",
        "",
        "## Scope Guard",
        "",
        "- This is a standalone report-section draft only.",
        "- It was not inserted into a normal Dragon's Touch report.",
        "- No API calls were made.",
        "- `main.py`, the PySide6 UI, and normal report generation were not changed.",
        "- Findings are informational by default, not automatic recommendations.",
        "",
        "## Combo Awareness",
        "",
        f"Deck checked: `{deck.path}`",
        f"Commander(s): {', '.join(deck.commander_names) if deck.commander_names else 'Not detected'}",
        f"Commander identity: {identity_to_string(commander_identity) if commander_identity is not None else 'Unavailable/not applied'}",
        "",
        "### Combo Summary",
        "",
        f"- Infinite combos found in deck: {len(strict_summary.complete_combos):,}",
        f"- Dragon's Touch Potential Combos: {len(strict_summary.one_card_away_combos):,}",
    ]

    if collection_loaded:
        lines.append(f"- Collection-completable potential combos: {len(collection_potential_results):,}")
    else:
        lines.append("- Collection-completable potential combos: collection files not loaded")

    lines.extend([
        "",
        "These are combo-awareness findings. Missing cards are not automatic add recommendations unless combo optimization is intentionally enabled later.",
        "",
        "### Current Infinite Combos Found",
        "",
    ])

    if not complete_results:
        lines.append("No complete known infinite combos were detected by the strict Dragon's Touch matcher.")
        lines.append("")
    else:
        for index, result in enumerate(shown_complete, start=1):
            lines.append(_format_concise_combo_line(index, result))
        if len(complete_results) > len(shown_complete):
            lines.append(f"Additional current combos not shown in this concise section: {len(complete_results) - len(shown_complete):,}")
        lines.append("")

    lines.extend([
        "### Collection-Completable Potential Combos",
        "",
    ])

    if not collection_loaded:
        lines.append("Collection files were not loaded, so collection-completable potential combos could not be identified.")
        lines.append("")
    elif not collection_potential_results:
        lines.append("No one-card-away potential combos were found where the missing card appeared in the loaded collection files.")
        lines.append("")
    else:
        lines.append("These are grouped by missing card so repeated Combo Spellbook variants do not overwhelm the concise report section.")
        lines.append("Exact combo variants remain available in the full isolated breakdown artifact.")
        lines.append("")
        for index, group in enumerate(shown_collection_groups, start=1):
            lines.extend(_format_grouped_concise_potential_line(index, group))
        if len(grouped_collection_potentials) > len(shown_collection_groups):
            lines.append(
                f"Additional collection-completable missing-card groups not shown in this concise section: {len(grouped_collection_potentials) - len(shown_collection_groups):,}"
            )
        lines.append("")

    lines.extend([
        "### Report Section Notes",
        "",
        "- This section intentionally hides Combo Finder parity and all-raw debug counts.",
        "- Collection-completable potential combos are grouped by missing card for readability.",
        "- Full combo variant details remain available in the isolated combo awareness breakdown artifact.",
        "- Verify template/state requirements before treating a combo as actually executable in-game.",
        "- Check whether the playgroup is comfortable with known infinite combos before adding missing pieces.",
        "- Future integration should keep combo optimization opt-in.",
        "",
    ])

    return "\n".join(lines)

def build_combo_breakdown_markdown(
    *,
    deck: DeckData,
    strict_summary: MatchSummary,
    commander_identity: set[str] | None,
    index_metadata: dict[str, Any],
    collection_loaded: bool,
    parity_summary: MatchSummary | None = None,
    raw_summary: MatchSummary | None = None,
    parity_index_metadata: dict[str, Any] | None = None,
    max_complete: int = 0,
    max_potential: int = 0,
) -> str:
    """Build the v0.8.7.2.1-dev combo awareness breakdown artifact.

    This markdown is still isolated/dev-only. It is not the normal report and it is
    not integrated with main.py or the PySide6 UI.
    """
    parity_index_metadata = parity_index_metadata or {}
    complete_results = strict_summary.complete_combos
    prioritized_potential_results = prioritize_potential_results(strict_summary.one_card_away_combos)

    collection_potential_results = [
        result for result in prioritized_potential_results if _result_has_collection_source(result)
    ]
    non_collection_potential_results = [
        result for result in prioritized_potential_results if not _result_has_collection_source(result)
    ]

    if max_complete and max_complete > 0:
        complete_results = complete_results[:max_complete]

    potential_results = prioritized_potential_results
    if max_potential and max_potential > 0:
        potential_results = potential_results[:max_potential]

    owned_potential_count = len(collection_potential_results)
    parity_potential_count = len(parity_summary.one_card_away_combos) if parity_summary is not None else None
    raw_potential_count = len(raw_summary.one_card_away_combos) if raw_summary is not None else None
    parity_owned = (
        sum(1 for result in parity_summary.one_card_away_combos if _result_has_collection_source(result))
        if parity_summary is not None
        else None
    )
    raw_owned = (
        sum(1 for result in raw_summary.one_card_away_combos if _result_has_collection_source(result))
        if raw_summary is not None
        else None
    )

    lines: list[str] = [
        "# v0.8.7.2.1-dev — Commander Spellbook Combo Awareness Breakdown",
        "",
        "## Scope Guard",
        "",
        "- No API calls were made.",
        "- No app integration was performed.",
        "- `main.py` was not changed.",
        "- UI and normal report generation were not changed.",
        "- This is a local, isolated breakdown artifact built from the strict Dragon's Touch matcher results.",
        "- These are combo-awareness findings, not automatic recommendations.",
        "",
        "## Deck Summary",
        "",
        f"- Deck file: `{deck.path}`",
        f"- Commanders detected: {', '.join(deck.commander_names) if deck.commander_names else 'Not detected'}",
        f"- Commander identity used: {identity_to_string(commander_identity) if commander_identity is not None else 'Unavailable/not applied'}",
        f"- Cards parsed including commanders: {len(deck.all_card_names):,}",
        f"- Unique normalized cards parsed: {len(deck.normalized_all_cards):,}",
        "",
        "## At-a-Glance Combo Dashboard",
        "",
        f"- Infinite combos in deck: {len(strict_summary.complete_combos):,}",
        f"- Dragon's Touch Potential Combos: {len(strict_summary.one_card_away_combos):,}",
    ]

    if parity_potential_count is not None:
        lines.append(f"- Combo Finder parity potential combos: {parity_potential_count:,}")
    if raw_potential_count is not None:
        lines.append(f"- All raw potential combos: {raw_potential_count:,}")

    lines.extend([
        "",
        "## Collection Completion Summary",
        "",
    ])
    if collection_loaded:
        lines.append(f"- Dragon's Touch collection-completable potentials: {owned_potential_count:,}")
        if parity_owned is not None:
            lines.append(f"- Combo Finder parity collection-completable potentials: {parity_owned:,}")
        if raw_owned is not None:
            lines.append(f"- All raw collection-completable potentials: {raw_owned:,}")
    else:
        lines.append("- Collection files were not loaded.")

    lines.extend([
        "",
        "## Data Sources",
        "",
        f"- Source version: {index_metadata.get('source_version', 'unknown')}",
        f"- Source timestamp: {index_metadata.get('source_timestamp', 'unknown')}",
        f"- Index schema version: {index_metadata.get('index_schema_version', 'unknown')}",
        f"- Strict index combos scanned: {strict_summary.scanned_combos:,}",
    ])
    if parity_summary is not None:
        lines.append(f"- Verification/parity index combos scanned: {parity_summary.scanned_combos:,}")
        if parity_index_metadata:
            lines.append(
                f"- Verification index commander_legal_only: {parity_index_metadata.get('commander_legal_only', 'unknown')}"
            )

    lines.extend([
        "",
        "## Dragon's Touch Filter Notes",
        "",
        f"- Spoiler-tagged hidden by Dragon's Touch: {strict_summary.skipped_spoiler:,}",
        f"- Color-identity invalid hidden by Dragon's Touch: {strict_summary.skipped_color_identity:,}",
        f"- mustBeCommander invalid hidden by Dragon's Touch: {strict_summary.skipped_must_be_commander:,}",
        f"- Unusable combo shape skipped: {strict_summary.skipped_unusable_shape:,}",
        "",
        "## How to Read This Breakdown",
        "",
        "- **Dragon's Touch Potential Combos** are strict-mode, deck-relevant, one-card-away combos.",
        "- **Combo Finder parity potential combos** are validation counts, not the default user-facing behavior.",
        "- **All raw potential combos** ignore normal relevance filters and are for debugging only.",
        "- Missing combo cards are not replacement recommendations unless a future user-selected combo-optimization mode asks for that behavior.",
        "- Collection-completable means the missing card appeared in a loaded collection file; it does not mean the card should automatically be added.",
        "- The detailed potential-combo section is capped by default for readability; use `--show-all-potentials` for full dev/audit output.",
        "",
        "## Current Infinite Combos Found",
        "",
    ])

    if not strict_summary.complete_combos:
        lines.append("No complete known infinite combos were detected by the strict matcher.")
        lines.append("")
    else:
        lines.append(f"Showing {len(complete_results):,} of {len(strict_summary.complete_combos):,} complete combos.")
        lines.append("")
        for index, result in enumerate(complete_results, start=1):
            _append_result_block(lines, f"### Complete Combo {index}", result)
        if max_complete and len(strict_summary.complete_combos) > len(complete_results):
            lines.append(f"Additional complete combos not shown: {len(strict_summary.complete_combos) - len(complete_results):,}")
            lines.append("")

    lines.extend([
        "## Collection-Completable Potential Combos",
        "",
    ])

    if not collection_loaded:
        lines.append("Collection files were not loaded, so collection-completable potential combos could not be identified.")
        lines.append("")
    elif not collection_potential_results:
        lines.append("No Dragon's Touch Potential Combos were completable from the loaded collection files.")
        lines.append("")
    else:
        lines.append(
            f"{len(collection_potential_results):,} Dragon's Touch Potential Combos are missing one card found in the loaded collection files."
        )
        lines.append("")
        for index, result in enumerate(collection_potential_results[:25], start=1):
            _append_compact_result_row(lines, index, result)
        if len(collection_potential_results) > 25:
            lines.append(f"Additional collection-completable potential combos not shown in this compact section: {len(collection_potential_results) - 25:,}")
        lines.append("")

    lines.extend([
        "## Potential Infinite Combos — Missing One Card",
        "",
    ])

    if not strict_summary.one_card_away_combos:
        lines.append("No one-card-away potential infinite combos were detected by the strict matcher.")
        lines.append("")
    else:
        lines.append(
            f"Showing {len(potential_results):,} of {len(strict_summary.one_card_away_combos):,} Dragon's Touch Potential Combos."
        )
        if max_potential and len(strict_summary.one_card_away_combos) > len(potential_results):
            lines.append(
                "This section is capped for readability. Use `--show-all-potentials` for full dev/audit output."
            )
        lines.append("Potential combos are sorted with collection-completable missing cards first, then smaller combo packages.")
        lines.append("")
        for index, result in enumerate(potential_results, start=1):
            _append_result_block(lines, f"### Potential Combo {index}", result)
        if max_potential and len(strict_summary.one_card_away_combos) > len(potential_results):
            lines.append(f"Additional potential combos not shown: {len(strict_summary.one_card_away_combos) - len(potential_results):,}")
            lines.append("")

    lines.extend([
        "## Breakdown Readiness Notes",
        "",
        f"- Complete combos listed: {len(complete_results):,} of {len(strict_summary.complete_combos):,}.",
        f"- Potential combos listed: {len(potential_results):,} of {len(strict_summary.one_card_away_combos):,}.",
        f"- Collection-completable potential combos: {owned_potential_count:,}.",
        f"- Non-collection potential combos: {len(non_collection_potential_results):,}.",
        "- Verify template/state requirements before treating a combo as actually executable in-game.",
        "- Check whether your playgroup is comfortable with known infinite combos before adding missing pieces.",
        "- This v0.8.7.2.1-dev breakdown should remain isolated until a later report integration patch intentionally connects it.",
        "",
    ])

    return "\n".join(lines)

