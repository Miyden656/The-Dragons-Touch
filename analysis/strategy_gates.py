"""Strategy gate and suppression helpers.

Cleanup focus:
- Keep strategy gating separate from raw strategy scoring.
- Prevent broad fallback labels from stealing primary strategy when a narrower
  commander-defined or mechanical plan is better supported.
- Prevent broad tags such as artifact, creature, combat, or lands_matter from
  making unrelated packages pass as meaningful strategies.
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


def _count(role_counts: dict[str, int], *tags: str) -> int:
    return sum(int(role_counts.get(tag, 0) or 0) for tag in tags)


def _gate_dragon_token_copy(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    dragon_count = _count(role_counts, "dragon_typal")
    copy_count = _count(role_counts, "copy_clone_value", "dragon_copy_value")
    token_count = _count(role_counts, "token_maker")
    typal_payoff = _count(role_counts, "tribal_payoff", "typal_payoff", "tribal_dependency")
    commander_support = candidate.get("commander_support", "light")

    if dragon_count >= 8 and (copy_count >= 2 or token_count >= 4 or commander_support == "strong"):
        return True, "Dragon density plus token/copy value gate passed."
    if commander_support == "strong" and dragon_count >= 5 and (copy_count + token_count + typal_payoff) >= 4:
        return True, "Commander-supported Dragon token/copy gate passed."
    return False, "Dragon token/copy gate failed; not enough Dragon density plus copy/token evidence."


def _gate_equipment_artifact_combat(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    # Artifact count alone must not make this strategy pass. This gate needs actual
    # Equipment/attachment/artifact-combat evidence.
    equipment_core = _count(
        role_counts,
        "equipment_synergy",
        "equipment_payoff",
        "equip_cost_reduction",
        "artifact_combat",
        "commander_damage_support",
        "attachment_synergy",
    )
    combat_core = _count(role_counts, "combat_synergy", "attack_trigger_payoff", "go_tall_support")
    protection = _count(role_counts, "protection", "evasion")
    commander_support = candidate.get("commander_support", "light")

    if equipment_core >= 5 and combat_core >= 3:
        return True, "Equipment/artifact-combat gate passed from real attachment/combat density."
    if commander_support == "strong" and equipment_core >= 3 and combat_core >= 2:
        return True, "Commander-supported Equipment/artifact-combat gate passed."
    if equipment_core >= 4 and protection >= 3 and combat_core >= 2:
        return True, "Equipment/artifact-combat gate passed with protection/evasion support."
    return False, "Equipment/artifact-combat gate failed; artifact or combat tags alone are not enough."


def _gate_token_go_wide_go_tall(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    token_count = _count(role_counts, "token_maker", "go_wide_token_engine", "token_resource_engine")
    combat_count = _count(role_counts, "combat_synergy", "attack_trigger_payoff", "anthem")
    tall_count = _count(role_counts, "go_tall_support", "counter_synergy", "high_toughness")
    commander_support = candidate.get("commander_support", "light")

    if commander_support in {"moderate", "strong"} and token_count >= 5 and (combat_count + tall_count) >= 8:
        return True, "Commander-supported token combat / go-wide-go-tall gate passed."
    if token_count >= 8 and combat_count >= 4 and tall_count >= 4:
        return True, "Token combat / go-wide-go-tall gate passed from token, combat, and scaling density."
    return False, "Token combat gate failed; needs token production plus combat/scaling payoff."


def _gate_mutate(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    mutate_count = _count(role_counts, "mutate")
    mutate_enabler = _count(role_counts, "mutate_enabler")
    mutate_payoff = _count(role_counts, "mutate_payoff", "creature_combo_value")
    if mutate_count >= 5 and mutate_enabler >= 3 and mutate_payoff >= 3:
        return True, "Mutate/creature-stack gate passed from mutate density, enablers, and payoffs."
    return False, "Mutate/creature-stack gate failed; needs real mutate density, enablers, and payoffs."


def _gate_graveyard_commander(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    setup = _count(role_counts, "graveyard_enabler", "self_mill", "discard_outlet")
    payoff = _count(role_counts, "reanimation", "graveyard_payoff", "recursion", "copy_clone_value")
    commander_support = candidate.get("commander_support", "light")
    if commander_support in {"moderate", "strong"} and setup >= 8 and payoff >= 2:
        return True, "Graveyard commander-engine gate passed from setup density and payoff."
    if setup >= 14 and payoff >= 4:
        return True, "Graveyard setup gate passed from high self-mill/discard/graveyard density."
    return False, "Graveyard commander-engine gate failed; insufficient commander/setup/payoff evidence."


def _gate_draw_punisher(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    punisher = _count(role_counts, "draw_punisher", "forced_draw", "wheel", "group_slug", "table_damage", "punisher")
    payoff = _count(role_counts, "damage_payoff", "lifedrain_payoff", "draw_punisher")
    commander_support = candidate.get("commander_support", "light")
    if commander_support == "strong" and punisher >= 3 and payoff >= 2:
        return True, "Draw-punisher/wheels gate passed from commander support and package density."
    if punisher >= 6 and payoff >= 3:
        return True, "Draw-punisher/wheels gate passed from package density."
    return False, "Draw-punisher/wheels gate failed; incidental draw/damage is not enough."


def _gate_landfall(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str]:
    landfall = _count(role_counts, "landfall", "landfall_payoff")
    land_support = _count(role_counts, "lands_matter", "extra_land_play", "land_recursion", "land_ramp")
    landfall_payoff = _count(role_counts, "landfall_payoff")
    land_engine_support = _count(role_counts, "extra_land_play", "land_recursion", "land_ramp")
    payoff = _count(role_counts, "landfall_payoff", "damage_payoff", "win_condition")
    commander_support = candidate.get("commander_support", "light")
    name = candidate.get("name", "")

    if name.startswith("Commander-Created Landfall"):
        if commander_support == "strong" and (landfall + land_engine_support) >= 6 and (payoff >= 1 or landfall_payoff >= 1):
            return True, "Commander-created landfall gate passed from commander support and land engine density."
        return False, "Commander-created landfall gate failed; commander must be the land engine."

    if commander_support == "strong" and (landfall + land_support) >= 6 and (payoff >= 1 or landfall_payoff >= 1):
        return True, "Commander-supported landfall/lands-matter gate passed."
    if landfall >= 5 and land_support >= 4 and (landfall_payoff >= 2 or land_engine_support >= 3):
        return True, "Landfall/lands-matter gate passed from printed landfall plus land-engine support."
    return False, "Landfall/lands-matter gate failed; broad lands_matter/token tags alone are not enough."


def _strategy_specific_gate(candidate: dict, role_counts: dict[str, int]) -> tuple[bool, str] | None:
    name = candidate.get("name", "")
    if name == "Dragon Typal / Token-Copy Value":
        return _gate_dragon_token_copy(candidate, role_counts)
    if name == "Equipment / Artifact Combat":
        return _gate_equipment_artifact_combat(candidate, role_counts)
    if name in {"Token Combat / Go-Wide-Go-Tall", "Tokens / Go-Wide Combat"}:
        return _gate_token_go_wide_go_tall(candidate, role_counts)
    if name == "Mutate / Creature Stack Value":
        return _gate_mutate(candidate, role_counts)
    if name == "Graveyard Setup / Commander Engine":
        return _gate_graveyard_commander(candidate, role_counts)
    if name == "Draw-Punisher / Wheels / Group Slug":
        return _gate_draw_punisher(candidate, role_counts)
    if name in {"Landfall / Lands Matter", "Commander-Created Landfall / Artifact Token Landfall"}:
        return _gate_landfall(candidate, role_counts)
    return None


def gate_strategy_candidate(candidate: dict, role_counts: dict[str, int]) -> dict:
    """Apply gate fields to a scored candidate dict."""
    name = candidate.get("name", "Unknown")
    anchor_count = candidate.get("anchor_count", 0)
    payoff_count = candidate.get("payoff_count", 0)
    enabler_count = candidate.get("enabler_count", 0)
    win_count = candidate.get("win_count", 0)
    commander_support = candidate.get("commander_support", "light")
    layer = candidate.get("layer", "macro_archetype")

    specific_gate = _strategy_specific_gate(candidate, role_counts)
    if specific_gate is not None:
        gate_passed, reason = specific_gate
    elif layer == "macro_archetype":
        gate_passed = candidate.get("score", 0) >= 8
        reason = "Macro fallback score met threshold." if gate_passed else "Macro fallback score below threshold."
    elif layer == "typal_strategy_shape":
        gate_passed = can_be_primary_typal(
            role_counts.get("typal_density_piece", 0) + role_counts.get("creature_type_present", 0),
            role_counts.get("typal_payoff", 0) + role_counts.get("tribal_payoff", 0) + role_counts.get("tribal_dependency", 0),
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
