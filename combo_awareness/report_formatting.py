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

def _combo_size(result: MatchResult) -> int:
    return len(combo_card_names(result.combo))

def _append_result_block(lines: list[str], heading: str, result: MatchResult) -> None:
    lines.append(heading)
    lines.append("")
    lines.extend(format_combo_result(result))
    lines.append("")

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
