"""Shared Scryfall card-name resolution helpers (v1.6.1 Phase 4).

WHY THIS FILE EXISTS
--------------------
Before v1.6.1 the collection loader had a smart resolver
(`data/collection_loader.py::_resolve_collection_card`) that walked four
indexes — exact name, normalized name, set+collector, alternate names
(printed / flavor / face) — to canonicalize a user-typed card name. But the
deck builder (`build_from_collection/full_100_card_draft_builder.py`) used
only `scryfall_lookup.get(name.lower(), {})`. That meant once a build was
running, any card whose canonical name wasn't yet in the lookup (split-card
back face, accented name like "Lim-Dûl's Vault", flavor name from a Universes
Beyond Within reprint) silently disappeared from the candidate pool.

This module extracts the resolution-index logic out of collection_loader so
both surfaces — the collection loader AND the deck builder — call into the
same routines. No duplicate implementation; collection_loader is rewired to
import from here.

PUBLIC API
----------
- `build_card_resolution_indexes(scryfall_lookup, scryfall_cards=None)`:
    Return a dict containing three indexes the resolvers walk:
        "exact_name"      — canonical name (lower + normalized)
        "alternate_name"  — printed_name, flavor_name, face name/printed/flavor
        "set_collector"   — (set_code, collector_number) → card record

- `resolve_card_in_indexes(name, set_code, collector_number, scryfall_lookup, indexes)`:
    Full collection-style resolver. Returns
    (resolved_name, found, resolution_method, record). resolution_method is
    one of "exact_name", "normalized_name", "set_collector",
    "printed_or_alternate_name", "not_found". Used by the collection loader.

- `resolve_card_simple(name, scryfall_lookup, indexes=None)`:
    Build-time resolver. Returns the Scryfall record (dict) or None. Builds
    indexes on demand if none are passed. Used by the deck builder.

- `normalize_lookup_key(text)`:
    Public version of the normalization used everywhere (lower + collapse
    whitespace + replace newlines). Exposed so callers that pre-normalize
    don't fall back to incompatible variants.
"""
from __future__ import annotations

from typing import Any, Sequence


def normalize_lookup_key(text: object) -> str:
    """Normalize a name for resolution-index lookup.

    Steps: cast to str → strip → lower → replace internal newlines with
    spaces → collapse all whitespace runs to a single space.
    """
    return " ".join(str(text or "").strip().lower().replace("\n", " ").split())


def collector_key(set_code: str | None, collector_number: str | None) -> tuple[str, str] | None:
    """Build the (set_code, collector_number) lookup key, lower-cased and
    cleaned of cosmetic markers (★, *). Returns None if either part is empty.
    """
    if not set_code or not collector_number:
        return None
    number = str(collector_number).strip().lower()
    number = number.replace("★", "").replace("*", "")
    return (str(set_code).strip().lower(), number)


def _iter_scryfall_records(
    scryfall_lookup: dict[str, dict[str, Any]],
    scryfall_cards: Sequence[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if scryfall_cards:
        return [card for card in scryfall_cards if isinstance(card, dict)]
    # Fallback is less complete because name lookup collapses printings, but
    # it preserves compatibility when full Scryfall cards are not passed in.
    return [card for card in scryfall_lookup.values() if isinstance(card, dict)]


def build_card_resolution_indexes(
    scryfall_lookup: dict[str, dict[str, Any]],
    scryfall_cards: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the four indexes used by name resolution.

    Pass `scryfall_cards` (the full list-of-cards JSON) when available so
    set+collector and per-printing alternate names are populated. Falling
    back to scryfall_lookup.values() works but covers fewer alternates
    because the name-keyed lookup collapses printings.
    """
    records = _iter_scryfall_records(scryfall_lookup, scryfall_cards)

    exact_name_index: dict[str, dict[str, Any]] = {}
    alternate_name_index: dict[str, dict[str, Any]] = {}
    set_collector_index: dict[tuple[str, str], dict[str, Any]] = {}

    for card in records:
        name = card.get("name")
        if name:
            exact_name_index.setdefault(str(name).lower(), card)
            exact_name_index.setdefault(normalize_lookup_key(name), card)

        # Printed-name (e.g., non-English printings) and flavor-name (Universes
        # Within reprint flavor) at the whole-card level.
        for alt_key in ("printed_name", "flavor_name"):
            alt_name = card.get(alt_key)
            if alt_name:
                alternate_name_index.setdefault(str(alt_name).lower(), card)
                alternate_name_index.setdefault(normalize_lookup_key(alt_name), card)

        # Per-face name / printed / flavor — handles split cards, MDFCs,
        # adventures, flip cards, rooms, sieges, etc.
        for face in card.get("card_faces", []) or []:
            if not isinstance(face, dict):
                continue
            for alt_key in ("name", "printed_name", "flavor_name"):
                alt_name = face.get(alt_key)
                if alt_name:
                    alternate_name_index.setdefault(str(alt_name).lower(), card)
                    alternate_name_index.setdefault(normalize_lookup_key(alt_name), card)

        key = collector_key(card.get("set"), card.get("collector_number"))
        if key:
            set_collector_index.setdefault(key, card)

    return {
        "exact_name": exact_name_index,
        "alternate_name": alternate_name_index,
        "set_collector": set_collector_index,
    }


def resolve_card_in_indexes(
    card_name: str,
    set_code: str | None,
    collector_number: str | None,
    scryfall_lookup: dict[str, dict[str, Any]],
    indexes: dict[str, Any],
) -> tuple[str, bool, str, dict[str, Any] | None]:
    """Full collection-style resolver.

    Resolution order:
      1. Exact Scryfall name match.
      2. Normalized name match.
      3. Set code + collector number match.
      4. Printed / flavor / card-face alternate name match.
      5. Not found.

    Returns (resolved_name, found, resolution_method, record) where
    resolution_method is one of:
        "exact_name", "normalized_name", "set_collector",
        "printed_or_alternate_name", "not_found"
    """
    clean = (card_name or "").strip()
    if not clean:
        return clean, False, "not_found", None

    # 1. Exact match. Prefer the original scryfall_lookup first to preserve
    # legacy behavior for callers that built their lookup outside this module.
    record = scryfall_lookup.get(clean.lower()) or indexes["exact_name"].get(clean.lower())
    if record:
        return str(record.get("name") or clean), True, "exact_name", record

    # 2. Normalized.
    normalized_key = normalize_lookup_key(clean)
    record = indexes["exact_name"].get(normalized_key)
    if record:
        return str(record.get("name") or clean), True, "normalized_name", record

    # 3. Set + collector.
    key = collector_key(set_code, collector_number)
    if key:
        record = indexes["set_collector"].get(key)
        if record:
            return str(record.get("name") or clean), True, "set_collector", record

    # 4. Alternate names (printed / flavor / face).
    record = (
        indexes["alternate_name"].get(clean.lower())
        or indexes["alternate_name"].get(normalized_key)
    )
    if record:
        return str(record.get("name") or clean), True, "printed_or_alternate_name", record

    return clean, False, "not_found", None


def resolve_card_simple(
    card_name: str,
    scryfall_lookup: dict[str, dict[str, Any]],
    indexes: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build-time resolver. Returns the Scryfall record or None.

    Order: exact lowercase → normalized → printed/face/flavor alt.
    (Set+collector skipped because the build path does not know set codes
    — that info is consumed during collection load, not during deck build.)

    Builds resolution indexes on demand from scryfall_lookup if none are
    passed. For per-card calls inside a loop, build indexes once at the
    top of the loop and pass them in to avoid the O(N) per-call cost.
    """
    clean = (card_name or "").strip()
    if not clean:
        return None

    # Fast path: exact lowercase against the existing lookup. This is the
    # common case — the loader already canonicalised the name.
    record = scryfall_lookup.get(clean.lower())
    if record:
        return record

    if indexes is None:
        indexes = build_card_resolution_indexes(scryfall_lookup)

    # Exact (lowercase + normalized) against the full index.
    normalized_key = normalize_lookup_key(clean)
    record = indexes["exact_name"].get(clean.lower()) or indexes["exact_name"].get(normalized_key)
    if record:
        return record

    # Alternate-name index (printed, flavor, face name/printed/flavor).
    record = (
        indexes["alternate_name"].get(clean.lower())
        or indexes["alternate_name"].get(normalized_key)
    )
    return record
