"""Strategy gate and suppression helpers.

Round 5 cleanup goal:
- Keep strategy gating separate from raw strategy scoring.
- Prevent broad fallback labels from stealing primary strategy when a narrower
  commander-defined or mechanical plan is better supported.
"""

from __future__ import annotations

BROAD_MACRO_LABELS = {
    "Aggro",
    "Midrange / Value",
    "Control",
    "Ramp / Big Mana",
    "Ramp-Control / Big Mana Value",
    "Engine / Synergy Value",
    "Combo-Adjacent Value",
    "Generic Tokens",
    "Generic Artifacts",
    "Generic Goodstuff",
    "Generic Treasure",
    "Generic Lifegain",
    "Generic Topdeck Value",
}


def density_category(count: int) -> str:
    if count >= 9:
        return "high"
    if count >= 4:
        return "medium"
    if count >= 1:
        return "low"
    return "none"


def can_be_primary_micro_archetype(
    commander_support: str,
    deck_density: str,
    payoff_present: bool,
    enabler_present: bool,
    win_path_present: bool,
) -> bool:
    return (
        commander_support in {"moderate", "strong"}
        and deck_density in {"medium", "high"}
        and payoff_present
        and enabler_present
        and win_path_present
    )


def can_be_primary_typal(creature_type_count: int, typal_payoff_count: int, commander_typal_support: bool) -> bool:
    return (
        creature_type_count >= 18 and typal_payoff_count >= 4
    ) or (
        commander_typal_support and creature_type_count >= 12 and typal_payoff_count >= 3
    )


def can_be_primary_commander_created_landfall(
    land_drop_support_count: int,
    land_recursion_count: int,
    commander_landfall_engine: bool,
    payoff_count: int,
) -> bool:
    return commander_landfall_engine and (land_drop_support_count + land_recursion_count) >= 6 and payoff_count >= 1


def can_be_true_turbo_combo(
    fast_mana_count: int,
    efficient_tutor_count: int,
    compact_combo_count: int,
    protection_count: int,
) -> bool:
    return fast_mana_count >= 3 and efficient_tutor_count >= 3 and compact_combo_count >= 1 and protection_count >= 2


def suppress_broad_if_narrower_exists(primary_name: str, has_passing_narrower: bool) -> bool:
    return primary_name in BROAD_MACRO_LABELS and has_passing_narrower


def gate_strategy_candidate(candidate: dict, role_counts: dict[str, int]) -> dict:
    """Apply generic gate fields to a scored candidate dict."""
    name = candidate.get("name", "Unknown")
    anchor_count = candidate.get("anchor_count", 0)
    payoff_count = candidate.get("payoff_count", 0)
    enabler_count = candidate.get("enabler_count", 0)
    win_count = candidate.get("win_count", 0)
    commander_support = candidate.get("commander_support", "light")
    layer = candidate.get("layer", "macro_archetype")

    gate_passed = False
    reason = ""
    if layer == "macro_archetype":
        gate_passed = candidate.get("score", 0) >= 8
        reason = "Macro fallback score met threshold." if gate_passed else "Macro fallback score below threshold."
    elif layer == "typal_strategy_shape":
        gate_passed = can_be_primary_typal(
            role_counts.get("typal_density_piece", 0) + role_counts.get("creature_type_present", 0),
            role_counts.get("typal_payoff", 0) + role_counts.get("tribal_payoff", 0),
            commander_support in {"moderate", "strong"},
        )
        reason = "Typal density/payoff gate passed." if gate_passed else "Typal density/payoff gate not fully met."
    else:
        gate_passed = can_be_primary_micro_archetype(
            commander_support=commander_support,
            deck_density=density_category(anchor_count + enabler_count + payoff_count),
            payoff_present=payoff_count > 0,
            enabler_present=enabler_count > 0 or anchor_count >= 4,
            win_path_present=win_count > 0 or payoff_count >= 2,
        )
        reason = "Micro/emergent gate passed." if gate_passed else "Micro/emergent gate not fully met."

    candidate["gate_passed"] = gate_passed
    candidate["primary_eligible"] = gate_passed
    candidate["gate_reason"] = reason
    return candidate
