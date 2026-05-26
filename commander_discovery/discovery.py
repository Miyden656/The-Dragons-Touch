"""Commander Discovery helpers.

These helpers are safe to import and test in isolation. v1.2.2 does not wire them
into main.py, UI, live reports, prompt building, scoring, or replacement logic.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .collection_scanner import scan_collection_for_commanders
from .models import CommanderCandidate


def discover_commander_candidates(collection_summary, scryfall_lookup) -> list[CommanderCandidate]:
    """Discover commander candidates from a loaded collection summary."""
    return scan_collection_for_commanders(collection_summary, scryfall_lookup).candidates


def group_candidates_by_color_identity(
    candidates: Iterable[CommanderCandidate],
) -> dict[str, list[CommanderCandidate]]:
    """Group candidates for future report/UI display."""
    grouped: dict[str, list[CommanderCandidate]] = defaultdict(list)
    for candidate in candidates:
        label = candidate.color_identity_group or candidate.color_identity_text or "Colorless"
        grouped[label].append(candidate)

    return {
        color_identity: sorted(group, key=lambda candidate: candidate.card_name.lower())
        for color_identity, group in sorted(grouped.items(), key=lambda item: (len(item[0]), item[0]))
    }
