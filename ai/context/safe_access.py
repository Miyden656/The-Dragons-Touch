"""Tiny, dependency-free helpers for defensive context building.

Every read of an engine object goes through here so that a renamed, missing, or
None field degrades to a safe default instead of raising. This is the mechanism
that keeps the AI layer resilient to engine/Commander's Call churn.
"""

from __future__ import annotations

from typing import Any, Iterable


def attr(obj: Any, name: str, default: Any = None) -> Any:
    """getattr that also tolerates dict-like objects and None."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def first_attr(obj: Any, names: Iterable[str], default: Any = None) -> Any:
    """Return the first present, non-None attribute among `names`.

    Useful when an engine list-of-dicts uses an uncertain key (e.g. a banned
    card entry keyed by 'card_name' OR 'name' OR 'card').
    """
    for name in names:
        value = attr(obj, name, None)
        if value is not None:
            return value
    return default


def as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def as_dict(value: Any) -> dict:
    """Coerce a Counter/dict-like to a plain dict; everything else -> {}."""
    if isinstance(value, dict):
        return dict(value)
    try:
        return dict(value)  # Counter and mapping-likes
    except (TypeError, ValueError):
        return {}


def truncate(items: list, limit: int) -> tuple[list, int]:
    """Return (capped_items, dropped_count). dropped_count == 0 if not truncated."""
    items = as_list(items)
    if limit < 0 or len(items) <= limit:
        return items, 0
    return items[:limit], len(items) - limit


def card_name_of(entry: Any, default: str = "") -> str:
    """Extract a card name from an engine entry, tolerating several key names."""
    if isinstance(entry, str):
        return entry.strip()
    return as_str(first_attr(entry, ("card_name", "name", "card"), default), default)
