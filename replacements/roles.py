"""Replacement candidate data model and collection-first ranking for The Dragon's Touch.

v0.9.4.1-dev hotfix goal:
- Ensure the v0.9 replacement-candidate preview/data-model layer actually consumes
  the already-working Collection Pull Candidates.
- Keep collection-first ranking active without adding full-card-pool fallback.
- Preserve review-candidate language and no automatic swaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

def _candidate_replacement_role(candidate: Any) -> str:
    strong_fit_needs = _as_list(getattr(candidate, "strong_fit_needs", None))
    matched_needs = _as_list(getattr(candidate, "matched_needs", None))
    if strong_fit_needs:
        return str(strong_fit_needs[0])
    if matched_needs:
        return str(matched_needs[0])
    return "manual_review"

def _v09462_has_dragon_need(candidate: object) -> bool:
    blob = _v09462_need_blob(candidate)
    return ('more dragon density' in blob or 'more dragon payoff' in blob or 'dragon density' in blob or 'dragon payoff' in blob or 'dragon typal' in blob or 'dragon_typal' in blob)

def _v09463_clean_dragon_need_list(value: object) -> list[str]:
    cleaned: list[str] = []
    for item in _v09463_list_strings(value):
        low = item.lower()
        if 'dragon density' in low or 'dragon payoff' in low or low.strip() in {'more dragon density', 'more dragon payoff'}:
            continue
        cleaned.append(item)
    return cleaned
