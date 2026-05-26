"""Commander candidate rules for The Commander's Call.

v1.2.2 keeps these public helper names stable while routing the actual
classification through commander_discovery.eligibility.
"""

from __future__ import annotations

from typing import Any

from .eligibility import (
    classify_commander_eligibility,
    get_commander_candidate_reason,
    get_special_commander_rule_note,
    is_basic_legendary_creature_candidate,
    is_commander_discovery_candidate,
)


__all__ = [
    "classify_commander_eligibility",
    "get_commander_candidate_reason",
    "get_special_commander_rule_note",
    "is_basic_legendary_creature_candidate",
    "is_commander_discovery_candidate",
]
