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

def _bracket_rank(result: MatchResult) -> int:
    """Lightweight ordering for readability, not a power judgment."""
    order = {
        "E": 0,
        "C": 1,
        "S": 2,
        "R": 3,
        "O": 4,
        "B": 5,
        "P": 6,
    }
    return order.get(str(result.combo.get("bracket_tag") or "").upper(), 99)
