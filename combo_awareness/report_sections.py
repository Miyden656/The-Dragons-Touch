#!/usr/bin/env python3
"""v1.4 expanded strategy scoring — markdown/report formatting for combo awareness.

v0.10.7.1.1 actual combo reporting source wording hotfix:
- Combo report text no longer describes combo analysis as optional or enabled only for a run.

Scope guard: reporting split only; no wording/behavior changes, no app integration.
"""

from __future__ import annotations

from typing import Any, Iterable

from .matcher import combo_card_names
from .models import DeckData, MatchResult, MatchSummary
from .normalization import identity_to_string, normalize_card_name

def _result_has_collection_source(result: MatchResult) -> bool:
    """Return True when at least one missing card was found in loaded collection files."""
    for sources in result.collection_sources_by_missing_card.values():
        if sources:
            return True
    return False

def _missing_card_summary(result: MatchResult) -> str:
    if not result.missing_card_names:
        return "None"
    return ", ".join(result.missing_card_names)

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
