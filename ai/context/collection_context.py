"""Collection ownership view.

Consumes: collection_summary (CollectionLoadSummary).

Ownership is a FACT the model must never guess. We surface totals + load status
here; the strategy-relevant owned cards arrive already filtered via
collection_candidates (see replacement_context). The full owned-card list is NOT
inlined (it can be thousands of cards); a specific "do I own X?" goes through a
verified lookup in the tools layer, not the model's memory.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_int, as_list, attr

_OWNED_SAMPLE_LIMIT = 0  # do not inline owned names; tools verify ownership on demand


def build_collection_view(collection_summary: Any) -> dict:
    loaded = bool(attr(collection_summary, "loaded", False))
    return {
        "loaded": loaded,
        "active": bool(attr(collection_summary, "active", loaded)),
        "ready_for_matching": bool(attr(collection_summary, "ready_for_matching", False)),
        "total_cards": as_int(attr(collection_summary, "total_cards")),
        "unique_cards": as_int(attr(collection_summary, "unique_cards")),
        "found_cards": as_int(attr(collection_summary, "found_cards")),
        "not_found_count": len(as_list(attr(collection_summary, "not_found_cards"))),
        "ownership_note": (
            "Card ownership is verified by the engine's collection data. Do not assume "
            "the user owns a card unless it appears in collection_candidates or a lookup "
            "confirms it."
        ),
    }
