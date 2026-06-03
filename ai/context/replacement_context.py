"""Replacement view.

Consumes: replacement_needs (ReplacementNeedSummary), replacement_candidates
(ReplacementCandidateSummary), collection_candidates (CollectionCandidateSummary).

Leads with NEED CATEGORIES (more ramp / draw / removal / ...) and only lists
specific cards that the engine has already verified and ranked. The model must
not promote category advice into named cards on its own.
"""

from __future__ import annotations

import re
from typing import Any

from ai.context.safe_access import as_list, as_str, attr, card_name_of, truncate

_CANDIDATE_LIMIT = 12
_COLLECTION_LIMIT = 12
_NEED_DETAIL_LIMIT = 12

# The engine bakes internal detection-source tags into free-text reasons
# (e.g. "More X was detected from role_count_gap."). Translate them to plain
# language so the local model can't parrot internal field names back to the user.
# Presentation-only: this never changes what is recommended, only how it reads.
_INTERNAL_SOURCE_PLAIN = {
    "primary_or_secondary_strategy": "your deck's main strategy",
    "strategy_specific_need": "your deck's specific strategy",
    "role_count_gap": "a gap in this deck's role coverage",
    "generic_role_gap": "a general role gap",
    "heuristic": "the deck's overall profile",
}
# Safety net for any other snake_case tag that slips through after "from <tag>".
_SNAKE_SOURCE = re.compile(r"\bfrom\s+([a-z]+_[a-z0-9_]+)\b")


def _clean_reason(text: str) -> str:
    """Strip internal detection-source tags from a user-facing reason string."""
    if not text:
        return text
    for tag, plain in _INTERNAL_SOURCE_PLAIN.items():
        text = text.replace(tag, plain)
    text = _SNAKE_SOURCE.sub("from the deck's overall profile", text)
    return text


def build_replacement_view(
    replacement_needs: Any,
    replacement_candidates: Any,
    collection_candidates: Any,
) -> tuple[dict, dict]:
    drops: dict[str, int] = {}

    need_details_raw = as_list(attr(replacement_needs, "need_details"))
    need_details, dropped = truncate(need_details_raw, _NEED_DETAIL_LIMIT)
    if dropped:
        drops["replacements.need_details"] = dropped

    cand_raw = as_list(attr(replacement_candidates, "top_ranked_candidates")) or as_list(
        attr(replacement_candidates, "candidates")
    )
    cands, dropped = truncate(cand_raw, _CANDIDATE_LIMIT)
    if dropped:
        drops["replacements.candidates"] = dropped

    coll_raw = as_list(attr(collection_candidates, "strong_candidates")) + as_list(
        attr(collection_candidates, "possible_candidates")
    )
    coll, dropped = truncate(coll_raw, _COLLECTION_LIMIT)
    if dropped:
        drops["replacements.collection_candidates"] = dropped

    view = {
        "priority_categories": [as_str(c) for c in as_list(attr(replacement_needs, "priority_categories"))],
        "need_details": [_need(n) for n in need_details],
        "candidates": [_candidate(c) for c in cands if card_name_of(c)],
        "collection_candidates": [_collection(c) for c in coll if card_name_of(c)],
        "collection_matching_active": bool(attr(collection_candidates, "candidate_matching_active", False)),
    }
    return view, drops


def _need(n: Any) -> dict:
    return {
        "category": as_str(attr(n, "category")),
        "priority": as_str(attr(n, "priority")),
        "reason": _clean_reason(as_str(attr(n, "reason"))),
    }


def _candidate(c: Any) -> dict:
    return {
        "card": card_name_of(c),
        "replacement_category": as_str(attr(c, "replacement_category")),
        "matched_needs": [as_str(m) for m in as_list(attr(c, "matched_needs"))],
        "owned_status": as_str(attr(c, "owned_status")),
        "confidence": as_str(attr(c, "confidence")),
        "why_it_fits": _clean_reason(as_str(attr(c, "why_it_fits"))),
        "why_to_be_careful": _clean_reason(as_str(attr(c, "why_to_be_careful"))),
    }


def _collection(c: Any) -> dict:
    return {
        "card": card_name_of(c),
        "quantity_owned": attr(c, "quantity_owned"),
        "confidence": as_str(attr(c, "confidence")),
        "matched_needs": [as_str(m) for m in as_list(attr(c, "matched_needs"))],
        "reason": _clean_reason(as_str(attr(c, "reason"))),
    }
