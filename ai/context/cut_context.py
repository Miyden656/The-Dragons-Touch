"""Cut view.

Consumes: possible_cuts (PossibleCutReviewSummary), protected_cards
(list[ProtectedCardEntry]).

Preserves the engine's careful separation of cut tiers (required / optional /
manual-review / playtest-first / protected) so the model never flattens them
into "this card is bad". Each entry carries the engine's confidence and reasons.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import as_list, as_str, attr, card_name_of, truncate

_TIER_LIMIT = 15


def build_cut_view(possible_cuts: Any, protected_cards: Any) -> tuple[dict, dict]:
    drops: dict[str, int] = {}

    def tier(name: str, attr_name: str) -> list[dict]:
        raw = as_list(attr(possible_cuts, attr_name))
        capped, dropped = truncate(raw, _TIER_LIMIT)
        if dropped:
            drops[f"cuts.{name}"] = dropped
        return [_cut_entry(e) for e in capped if card_name_of(e)]

    view = {
        "required_cuts": tier("required_cuts", "required_cut_candidates"),
        "optional_cuts": tier("optional_cuts", "optional_cut_candidates"),
        "manual_review": tier("manual_review", "manual_review_candidates"),
        "playtest_first": tier("playtest_first", "playtest_first_candidates"),
        "protected_from_cut": _protected_tier(possible_cuts, "protected_from_cut", drops),
        "protected_cards": _protected(protected_cards, drops),
        "notes": [as_str(n) for n in as_list(attr(possible_cuts, "notes"))],
    }
    return view, drops


def _cut_entry(e: Any) -> dict:
    return {
        "card": card_name_of(e),
        "confidence": as_str(attr(e, "cut_confidence")),
        "cut_type": as_str(attr(e, "cut_type")),
        "reasons": [as_str(r) for r in as_list(attr(e, "reasons"))][:3],
    }


def _protected_tier(possible_cuts: Any, attr_name: str, drops: dict) -> list[dict]:
    """Protected cards only need a name + short label: the model must NOT cut them,
    which the cut allow-list already enforces. The engine's verbose internal reasons
    (~1.7k tokens of prompt) are low-value to the model, so we omit them here — the
    real cut tiers (required/optional/...) still carry their reasons."""
    raw = as_list(attr(possible_cuts, attr_name))
    capped, dropped = truncate(raw, _TIER_LIMIT)
    if dropped:
        drops[f"cuts.{attr_name}"] = dropped
    return [
        {"card": card_name_of(e), "cut_type": as_str(attr(e, "cut_type"))}
        for e in capped
        if card_name_of(e)
    ]


def _protected(protected_cards: Any, drops: dict) -> list[dict]:
    raw = as_list(protected_cards)
    capped, dropped = truncate(raw, _TIER_LIMIT)
    if dropped:
        drops["cuts.protected_cards"] = dropped
    # Name + protection level only — same rationale as _protected_tier (reasons omitted).
    return [
        {"card": card_name_of(e), "protection_level": as_str(attr(e, "protection_level"))}
        for e in capped
        if card_name_of(e)
    ]
