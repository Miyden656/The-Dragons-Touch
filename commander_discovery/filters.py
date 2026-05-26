"""Candidate filtering helpers for The Commander's Call.

v1.2.4 intentionally keeps filtering isolated from the live deck review flow.
These helpers narrow already-discovered CommanderCandidate objects for report and
UI preview work. They do not scan collections, score cards, or build decks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

WUBRG_ORDER = ("W", "U", "B", "R", "G")
COLORLESS_KEY = "COLORLESS"
ANY_COLOR_KEY = "ANY"


def normalize_color_identity_key(value: object) -> str:
    """Return a stable uppercase color-identity key for filters and grouping.

    Examples:
    - ["G", "U"] -> "UG" sorted into WUBRG order as "UG"
    - "Temur" is left as "TEMUR" for label-style comparisons
    - empty / None -> "COLORLESS"
    """
    if value is None:
        return COLORLESS_KEY

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return COLORLESS_KEY
        upper = raw.upper().replace(" ", "_").replace("-", "_")
        if set(upper).issubset(set(WUBRG_ORDER)):
            return "".join(color for color in WUBRG_ORDER if color in upper) or COLORLESS_KEY
        return upper

    if isinstance(value, Sequence):
        colors = [str(item).strip().upper() for item in value if str(item).strip()]
        if not colors:
            return COLORLESS_KEY
        if set(colors).issubset(set(WUBRG_ORDER)):
            return "".join(color for color in WUBRG_ORDER if color in colors) or COLORLESS_KEY
        return "_".join(colors)

    return str(value).strip().upper() or COLORLESS_KEY


def _candidate_text(candidate: object) -> str:
    parts = [
        getattr(candidate, "card_name", ""),
        getattr(candidate, "type_line", ""),
        getattr(candidate, "oracle_text_preview", ""),
        getattr(candidate, "commander_eligibility_reason", ""),
        getattr(candidate, "special_commander_rule", ""),
        getattr(candidate, "manual_review_notes", ""),
        getattr(candidate, "color_identity_text", ""),
        getattr(candidate, "color_identity_group", ""),
    ]
    return "\n".join(str(part) for part in parts if part).lower()


def _candidate_color_key(candidate: object) -> str:
    explicit = getattr(candidate, "color_identity_key", None)
    if explicit:
        return normalize_color_identity_key(explicit)
    colors = getattr(candidate, "color_identity", None)
    return normalize_color_identity_key(colors)


def _candidate_color_count(candidate: object) -> int:
    explicit = getattr(candidate, "color_count", None)
    if isinstance(explicit, int):
        return explicit
    key = _candidate_color_key(candidate)
    if key == COLORLESS_KEY:
        return 0
    return sum(1 for color in WUBRG_ORDER if color in key)


@dataclass(frozen=True)
class CommanderCandidateFilterOptions:
    """Safe filter options for already-discovered commander candidates."""

    color_identity_key: Optional[str] = None
    color_identity_group: Optional[str] = None
    min_colors: Optional[int] = None
    max_colors: Optional[int] = None
    min_owned_quantity: Optional[int] = None
    text_search: Optional[str] = None
    include_mvp_eligible: bool = True
    include_manual_review: bool = True

    def has_active_filters(self) -> bool:
        return any(
            [
                bool(self.color_identity_key),
                bool(self.color_identity_group),
                self.min_colors is not None,
                self.max_colors is not None,
                self.min_owned_quantity is not None,
                bool(self.text_search),
                self.include_mvp_eligible is not True,
                self.include_manual_review is not True,
            ]
        )


def candidate_matches_filters(candidate: object, options: CommanderCandidateFilterOptions | None = None) -> bool:
    """Return True if a CommanderCandidate-like object passes the filters."""
    if options is None:
        return True

    is_mvp = bool(getattr(candidate, "is_mvp_eligible", False))
    is_manual = bool(getattr(candidate, "is_special_rule_candidate", False))

    if is_mvp and not options.include_mvp_eligible:
        return False
    if is_manual and not options.include_manual_review:
        return False

    if options.color_identity_key:
        wanted = normalize_color_identity_key(options.color_identity_key)
        if wanted != ANY_COLOR_KEY and _candidate_color_key(candidate) != wanted:
            return False

    if options.color_identity_group:
        wanted_group = str(options.color_identity_group).strip().lower()
        candidate_group = str(getattr(candidate, "color_identity_group", "")).strip().lower()
        if wanted_group and candidate_group != wanted_group:
            return False

    color_count = _candidate_color_count(candidate)
    if options.min_colors is not None and color_count < int(options.min_colors):
        return False
    if options.max_colors is not None and color_count > int(options.max_colors):
        return False

    if options.min_owned_quantity is not None:
        owned_quantity = getattr(candidate, "owned_quantity", 0) or 0
        if int(owned_quantity) < int(options.min_owned_quantity):
            return False

    if options.text_search:
        needle = options.text_search.strip().lower()
        if needle and needle not in _candidate_text(candidate):
            return False

    return True


def filter_commander_candidates(
    candidates: Iterable[object],
    options: CommanderCandidateFilterOptions | None = None,
) -> List[object]:
    """Return candidates that pass the supplied filter options."""
    return [candidate for candidate in candidates if candidate_matches_filters(candidate, options)]


def summarize_candidate_filters(options: CommanderCandidateFilterOptions | None = None) -> str:
    """Return a short human-readable summary for reports/UI previews."""
    if options is None or not options.has_active_filters():
        return "No filters applied."

    parts: List[str] = []
    if options.color_identity_key:
        parts.append(f"Color identity: {normalize_color_identity_key(options.color_identity_key)}")
    if options.color_identity_group:
        parts.append(f"Color group: {options.color_identity_group}")
    if options.min_colors is not None:
        parts.append(f"Minimum colors: {options.min_colors}")
    if options.max_colors is not None:
        parts.append(f"Maximum colors: {options.max_colors}")
    if options.min_owned_quantity is not None:
        parts.append(f"Minimum owned quantity: {options.min_owned_quantity}")
    if options.text_search:
        parts.append(f"Text search: {options.text_search}")
    if not options.include_mvp_eligible:
        parts.append("MVP Legendary Creature candidates hidden")
    if not options.include_manual_review:
        parts.append("Manual-review candidates hidden")
    return "; ".join(parts) if parts else "No filters applied."


def split_candidates_for_filter_preview(
    candidates: Iterable[object],
    options: CommanderCandidateFilterOptions | None = None,
) -> tuple[List[object], List[object]]:
    """Return (included, excluded) for future UI/report preview counters."""
    included: List[object] = []
    excluded: List[object] = []
    for candidate in candidates:
        if candidate_matches_filters(candidate, options):
            included.append(candidate)
        else:
            excluded.append(candidate)
    return included, excluded
