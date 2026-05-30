"""Collection scanner for Commander Discovery.

v1.2.2 preserves the isolated scan path and enriches candidate output with
eligibility status/rule fields. It still does not load files by itself, make
network calls, touch main.py, modify reports/prompts, or change normal deck
review behavior.
"""

from __future__ import annotations

from typing import Any, Iterable

from .eligibility import (
    RULE_BANNED_COMMANDER,
    classify_commander_eligibility,
)
from .models import CommanderCandidate, CommanderDiscoveryScanResult


Bucket = dict[str, Any]


def scan_collection_for_legendary_creature_candidates(
    collection_summary: Any,
    scryfall_lookup: dict[str, dict[str, Any]] | None,
    *,
    allow_banned_commanders: bool = False,
) -> CommanderDiscoveryScanResult:
    """Compatibility wrapper for the v1.2.1 scanner name.

    v1.2.2 may include manual-review special-rule candidates in the full result.
    v1.6.1 Phase 2 adds the optional allow_banned_commanders flag.
    Use result.legendary_creature_candidates to read only MVP Legendary Creature
    candidates.
    """
    return scan_collection_for_commanders(
        collection_summary,
        scryfall_lookup,
        allow_banned_commanders=allow_banned_commanders,
    )


def scan_collection_for_commanders(
    collection_summary: Any,
    scryfall_lookup: dict[str, dict[str, Any]] | None,
    *,
    allow_banned_commanders: bool = False,
) -> CommanderDiscoveryScanResult:
    """Scan a CollectionLoadSummary-like object for commander candidates.

    Expected input is compatible with the existing data.collection_loader
    CollectionLoadSummary shape. Dict-like test doubles are also supported so
    verifier and future CLI tooling can exercise this in isolation.
    """
    lookup = _normalized_lookup(scryfall_lookup or {})
    warnings = _summary_warnings(collection_summary)
    buckets: dict[str, Bucket] = {}
    total_collection_entries = 0
    unresolved_collection_cards = 0

    entries = list(_iter_collection_entries(collection_summary))
    if entries:
        for entry in entries:
            total_collection_entries += 1
            name = _entry_name(entry)
            if not name:
                unresolved_collection_cards += 1
                continue
            card = _lookup_card(name, lookup)
            if not card:
                unresolved_collection_cards += 1
                continue
            _merge_bucket(
                buckets,
                card,
                quantity=_entry_quantity(entry),
                source_file=_entry_source(entry),
            )
    else:
        for name, quantity in _iter_card_quantities(collection_summary):
            total_collection_entries += 1
            card = _lookup_card(name, lookup)
            if not card:
                unresolved_collection_cards += 1
                continue
            _merge_bucket(
                buckets,
                card,
                quantity=quantity,
                source_files=_card_sources(collection_summary, name),
            )

    candidates: list[CommanderCandidate] = []
    skipped_nonlegendary_cards = 0
    # v1.6.1 Phase 2: count banned-commander exclusions separately so the UI /
    # report can surface "N banned commanders in your collection were excluded"
    # rather than lumping them in with non-legendary cards.
    banned_commanders_skipped = 0
    manual_review_candidate_count = 0
    mvp_candidate_count = 0

    for payload in buckets.values():
        card = payload["card"]
        classification = classify_commander_eligibility(
            card, allow_banned_commanders=allow_banned_commanders,
        )
        if not classification.include_in_discovery:
            if classification.rule == RULE_BANNED_COMMANDER:
                banned_commanders_skipped += 1
            else:
                skipped_nonlegendary_cards += 1
            continue
        if classification.is_mvp_eligible:
            mvp_candidate_count += 1
        if classification.status == "manual_review":
            manual_review_candidate_count += 1
        candidates.append(
            CommanderCandidate.from_card(
                card,
                owned_quantity=payload["quantity"],
                source_files=sorted(payload["sources"]),
                eligibility=classification,
            )
        )

    candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate.color_count,
            candidate.color_identity_key,
            candidate.eligibility_status != "eligible",
            candidate.card_name.lower(),
        ),
    )

    return CommanderDiscoveryScanResult(
        candidates=candidates,
        total_collection_entries=total_collection_entries,
        unique_collection_cards=len(buckets),
        resolved_collection_cards=len(buckets),
        unresolved_collection_cards=unresolved_collection_cards,
        skipped_nonlegendary_cards=skipped_nonlegendary_cards,
        banned_commanders_skipped=banned_commanders_skipped,
        allow_banned_commanders=allow_banned_commanders,
        manual_review_candidate_count=manual_review_candidate_count,
        mvp_candidate_count=mvp_candidate_count,
        warnings=warnings,
    )


def _normalized_lookup(scryfall_lookup: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for key, card in scryfall_lookup.items():
        if not isinstance(card, dict):
            continue
        normalized[_normalize_key(key)] = card
        if card.get("name"):
            normalized[_normalize_key(card.get("name"))] = card
    return normalized


def _lookup_card(name: object, lookup: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return lookup.get(_normalize_key(name))


def _normalize_key(value: object) -> str:
    return " ".join(str(value or "").strip().lower().replace("\n", " ").split())


def _merge_bucket(
    buckets: dict[str, Bucket],
    card: dict[str, Any],
    *,
    quantity: object = 1,
    source_file: str = "",
    source_files: Iterable[str] | None = None,
) -> None:
    name = str(card.get("name") or "Unknown").strip()
    key = _normalize_key(name)
    bucket = buckets.setdefault(key, {"card": card, "quantity": 0, "sources": set()})
    bucket["quantity"] += _coerce_quantity(quantity)
    if source_file:
        bucket["sources"].add(str(source_file))
    for source in source_files or []:
        if source:
            bucket["sources"].add(str(source))


def _iter_collection_entries(collection_summary: Any) -> Iterable[Any]:
    entries = getattr(collection_summary, "entries", None)
    if entries is None and isinstance(collection_summary, dict):
        entries = collection_summary.get("entries")
    return entries or []


def _entry_name(entry: Any) -> str:
    for attr in ("scryfall_name", "normalized_name", "card_name"):
        value = getattr(entry, attr, None)
        if value:
            return str(value).strip()
    if isinstance(entry, dict):
        for key in ("scryfall_name", "normalized_name", "card_name", "name"):
            value = entry.get(key)
            if value:
                return str(value).strip()
    return ""


def _entry_quantity(entry: Any) -> int:
    value = getattr(entry, "quantity", None)
    if value is None and isinstance(entry, dict):
        value = entry.get("quantity", 1)
    return _coerce_quantity(value)


def _coerce_quantity(value: object) -> int:
    try:
        return max(int(value or 1), 0)
    except (TypeError, ValueError):
        return 1


def _entry_source(entry: Any) -> str:
    value = getattr(entry, "source_file", None)
    if value is None and isinstance(entry, dict):
        value = entry.get("source_file")
    return str(value).strip() if value else ""


def _iter_card_quantities(collection_summary: Any) -> Iterable[tuple[str, int]]:
    card_quantities = getattr(collection_summary, "card_quantities", None)
    if card_quantities is None and isinstance(collection_summary, dict):
        card_quantities = collection_summary.get("card_quantities")
    if not card_quantities:
        return []
    return list(card_quantities.items())


def _card_sources(collection_summary: Any, name: object) -> list[str]:
    card_sources = getattr(collection_summary, "card_sources", None)
    if card_sources is None and isinstance(collection_summary, dict):
        card_sources = collection_summary.get("card_sources")
    if not card_sources:
        return []
    sources = card_sources.get(str(name), []) or card_sources.get(_normalize_key(name), []) or []
    return [str(source) for source in sources if source]


def _summary_warnings(collection_summary: Any) -> list[str]:
    warnings = getattr(collection_summary, "parse_warnings", None)
    if warnings is None and isinstance(collection_summary, dict):
        warnings = collection_summary.get("parse_warnings")
    return [str(warning) for warning in (warnings or []) if warning]
