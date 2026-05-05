"""Strategy scoring engine.

Round 5 cleanup goal:
- Separate strategy scoring from role tagging, legality, cuts, and reports.
- Produce a structured strategy summary that later report/cut modules can consume.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from deck_helper.analysis.strategy_gates import gate_strategy_candidate, suppress_broad_if_narrower_exists
from deck_helper.data.card_lookup import get_full_oracle_text, normalize_text

@dataclass(slots=True)
class StrategyCandidate:
    name: str
    score: int
    layer: str
    anchor_count: int = 0
    payoff_count: int = 0
    enabler_count: int = 0
    win_count: int = 0
    commander_support: str = "light"
    gate_passed: bool = False
    primary_eligible: bool = False
    evidence: list[str] = field(default_factory=list)
    gate_reason: str = ""

@dataclass(slots=True)
class StrategySummary:
    primary_strategy: str
    secondary_strategy: str
    primary_candidate: StrategyCandidate | None
    secondary_candidate: StrategyCandidate | None
    candidates: list[StrategyCandidate]
    confidence: str
    warnings: list[str]
    core_synergy_packages: list[str]

ARCHETYPE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "Ramp / Big Mana": {
        "layer": "macro_archetype",
        "anchors": {"ramp", "mana_rock", "mana_dork", "mana_doubler", "extra_land_play"},
        "payoffs": {"big_mana_payoff", "mana_sink", "high_mv_payoff", "win_condition"},
        "enablers": {"mana_source", "card_draw"},
    },
    "Midrange / Value": {
        "layer": "macro_archetype",
        "anchors": {"card_advantage", "card_draw", "targeted_removal", "recursion", "etb_value"},
        "payoffs": {"win_condition", "damage_payoff", "lifedrain_payoff"},
        "enablers": {"ramp", "protection", "card_selection"},
    },
    "Control": {
        "layer": "macro_archetype",
        "anchors": {"targeted_removal", "board_wipe", "counterspell", "pillowfort", "protection"},
        "payoffs": {"win_condition", "card_advantage"},
        "enablers": {"card_draw", "recursion"},
    },
    "Aristocrats / Sacrifice Value": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"sacrifice_outlet", "free_sacrifice_outlet", "death_trigger_payoff", "sacrifice_payoff"},
        "payoffs": {"death_trigger_payoff", "lifedrain_payoff", "damage_payoff", "card_draw"},
        "enablers": {"token_maker", "recursion", "graveyard_enabler"},
    },
    "Tokens / Go-Wide Combat": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"token_maker", "anthem", "go_wide_token_engine"},
        "payoffs": {"anthem", "combat_synergy", "attack_trigger_payoff", "win_condition"},
        "enablers": {"protection", "card_draw", "token_resource_engine"},
    },
    "Voltron / Go-Tall Combat": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"equipment_synergy", "aura_synergy", "go_tall_support", "commander_damage_support"},
        "payoffs": {"combat_synergy", "extra_combat", "win_condition"},
        "enablers": {"protection", "card_draw", "evasion"},
    },
    "Spellslinger / Noncreature Spells": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"spell_payoff", "noncreature_spell_payoff", "cast_trigger", "cast_copy_synergy"},
        "payoffs": {"spell_payoff", "damage_payoff", "token_maker", "win_condition"},
        "enablers": {"card_draw", "card_selection", "cost_reducer", "spell_recursion_possible"},
    },
    "Blink/Flicker / ETB Value": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"blink_flicker", "exile_return", "mass_blink"},
        "payoffs": {"etb_value", "card_draw", "targeted_removal"},
        "enablers": {"recursion", "protection"},
    },
    "Landfall / Lands Matter": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"landfall", "landfall_payoff", "lands_matter"},
        "payoffs": {"landfall_payoff", "token_maker", "damage_payoff", "win_condition"},
        "enablers": {"ramp", "extra_land_play", "land_token", "utility_land"},
    },
    "Commander-Created Landfall / Artifact Token Landfall": {
        "layer": "commander_defined_emergent",
        "anchors": {"land_token", "rock_token_synergy", "artifact_token_synergy", "landfall"},
        "payoffs": {"artifact_payoff", "token_maker", "damage_payoff", "win_condition"},
        "enablers": {"ramp", "extra_land_play", "lands_matter"},
    },
    "Artifacts / Artifact Tokens": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"artifact_payoff", "artifact_token_synergy", "mana_rock", "treasure_synergy", "clue_synergy", "food_synergy"},
        "payoffs": {"artifact_payoff", "win_condition", "card_draw"},
        "enablers": {"ramp", "token_maker", "sacrifice_outlet"},
    },
    "Lifegain / Lifedrain": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"lifegain_payoff", "lifedrain_payoff"},
        "payoffs": {"lifedrain_payoff", "damage_payoff", "win_condition"},
        "enablers": {"card_draw", "protection", "token_maker"},
    },
    "Toughness / Defender Value": {
        "layer": "mechanical_micro_archetype",
        "anchors": {"toughness_payoff", "defender_payoff", "wall_typal", "high_toughness"},
        "payoffs": {"toughness_payoff", "combat_synergy", "win_condition"},
        "enablers": {"protection", "card_draw", "ramp"},
    },
    "Typal Strategy": {
        "layer": "typal_strategy_shape",
        "anchors": {"typal_density_piece", "creature_type_present"},
        "payoffs": {"tribal_payoff", "typal_payoff", "tribal_dependency"},
        "enablers": {"token_maker", "recursion", "cost_reducer"},
    },
    "Mutate / Creature Stack Value": {
        "layer": "niche_theme",
        "anchors": {"mutate", "mutate_payoff", "mutate_enabler"},
        "payoffs": {"mutate_payoff", "creature_combo_value", "counter_synergy"},
        "enablers": {"mutate_enabler", "protection", "recursion"},
    },
    "Cast From Outside Hand Value": {
        "layer": "commander_defined_emergent",
        "anchors": {"cast_from_outside_hand", "nonhand_casting", "foretell", "plot", "suspend_synergy", "adventure_synergy"},
        "payoffs": {"card_advantage", "spell_payoff", "cast_trigger"},
        "enablers": {"card_selection", "cost_reducer", "alternate_cost_interaction"},
    },
    "Combo-Adjacent Value": {
        "layer": "macro_archetype",
        "anchors": {"combo_piece_possible", "copy_clone_value", "cast_copy_synergy"},
        "payoffs": {"win_condition", "damage_payoff"},
        "enablers": {"tutor", "protection", "recursion"},
    },
}


def _commander_text(commander_cards: list[dict[str, Any]] | None) -> str:
    return normalize_text("\n".join(get_full_oracle_text(card) + "\n" + card.get("type_line", "") for card in commander_cards or []))


def _commander_support_for_strategy(name: str, commander_cards: list[dict[str, Any]] | None) -> str:
    text = _commander_text(commander_cards)
    if not text:
        return "none"
    strategy_checks = {
        "Landfall": ["land enters", "landfall", "rock artifact token"],
        "Commander-Created Landfall": ["land enters", "rock artifact token"],
        "Artifacts": ["artifact", "treasure", "clue", "food"],
        "Tokens": ["create", "token"],
        "Aristocrats": ["sacrifice", "dies", "graveyard"],
        "Spellslinger": ["instant", "sorcery", "noncreature spell", "cast or copy"],
        "Blink": ["exile", "return it to the battlefield"],
        "Lifegain": ["gain life", "lose life"],
        "Toughness": ["toughness", "defender"],
        "Mutate": ["mutate"],
        "Cast From Outside": ["exile", "anywhere other than your hand", "foretell", "plot", "suspend"],
        "Typal": ["creature type", "creatures you control", "dragon", "elf", "goblin", "vampire", "zombie"],
    }
    for key, phrases in strategy_checks.items():
        if key in name and any(phrase in text for phrase in phrases):
            return "strong"
    if any(phrase in text for phrase in ["whenever", "create", "draw", "cast", "attack", "sacrifice"]):
        return "moderate"
    return "light"


def _count_tags(role_counts: Counter[str], tags: set[str]) -> int:
    return sum(role_counts.get(tag, 0) for tag in tags)


def score_archetypes(
    role_counts: Counter[str],
    type_counts: Counter[str],
    commander_cards: list[dict[str, Any]] | None = None,
) -> list[StrategyCandidate]:
    candidates: list[StrategyCandidate] = []
    for name, definition in ARCHETYPE_DEFINITIONS.items():
        anchors = set(definition.get("anchors", set()))
        payoffs = set(definition.get("payoffs", set()))
        enablers = set(definition.get("enablers", set()))
        anchor_count = _count_tags(role_counts, anchors)
        payoff_count = _count_tags(role_counts, payoffs)
        enabler_count = _count_tags(role_counts, enablers)
        win_count = role_counts.get("win_condition", 0)
        commander_support = _commander_support_for_strategy(name, commander_cards)

        score = anchor_count * 4 + payoff_count * 3 + enabler_count * 2 + win_count
        if commander_support == "strong":
            score += 12
        elif commander_support == "moderate":
            score += 6
        elif commander_support == "light":
            score += 2

        evidence = []
        if anchor_count:
            evidence.append(f"{anchor_count} anchor/support role hits")
        if payoff_count:
            evidence.append(f"{payoff_count} payoff role hits")
        if enabler_count:
            evidence.append(f"{enabler_count} enabler role hits")
        if commander_support != "none":
            evidence.append(f"commander support: {commander_support}")

        raw = {
            "name": name,
            "score": int(score),
            "layer": definition.get("layer", "macro_archetype"),
            "anchor_count": anchor_count,
            "payoff_count": payoff_count,
            "enabler_count": enabler_count,
            "win_count": win_count,
            "commander_support": commander_support,
            "evidence": evidence,
        }
        gated = gate_strategy_candidate(raw, role_counts)
        candidates.append(StrategyCandidate(**gated))

    return sorted(candidates, key=lambda item: item.score, reverse=True)


def choose_primary_secondary_strategy(candidates: list[StrategyCandidate]) -> tuple[StrategyCandidate | None, StrategyCandidate | None, list[str]]:
    warnings: list[str] = []
    passing = [candidate for candidate in candidates if candidate.primary_eligible]
    if not passing:
        passing = candidates[:]
        warnings.append("No strategy fully passed its primary gate; treat the strategy read as provisional.")

    # If a broad macro is on top but a narrower gated plan is close, prefer the narrower plan.
    if passing:
        top = passing[0]
        narrower = [c for c in passing if c.layer != "macro_archetype" and c.score >= max(1, int(top.score * 0.70))]
        if suppress_broad_if_narrower_exists(top.name, bool(narrower)):
            warnings.append(f"Suppressed broad fallback '{top.name}' because a narrower supported plan was close enough.")
            passing = sorted(narrower + [c for c in passing if c not in narrower], key=lambda item: item.score, reverse=True)

    primary = passing[0] if passing else None
    secondary = None
    for candidate in passing[1:]:
        if primary and candidate.name != primary.name:
            secondary = candidate
            break
    if primary and secondary and secondary.score >= primary.score * 0.90:
        warnings.append("Primary and secondary strategy scores are within 10%; confirm pilot intent before aggressive cuts/additions.")
    return primary, secondary, warnings


def get_strategy_confidence(primary: StrategyCandidate | None, secondary: StrategyCandidate | None) -> str:
    if not primary:
        return "low"
    if not primary.gate_passed:
        return "low"
    if secondary and secondary.score >= primary.score * 0.90:
        return "medium"
    if primary.score >= 35 and primary.commander_support in {"moderate", "strong"}:
        return "high"
    return "medium"


def get_core_synergy_packages(candidates: list[StrategyCandidate], limit: int = 5) -> list[str]:
    packages = []
    for candidate in candidates:
        if candidate.score <= 0:
            continue
        if candidate.gate_passed or candidate.score >= 12:
            packages.append(f"{candidate.name} ({candidate.layer}, score {candidate.score})")
        if len(packages) >= limit:
            break
    return packages


def build_strategy_summary(
    role_counts: Counter[str],
    type_counts: Counter[str],
    commander_cards: list[dict[str, Any]] | None = None,
) -> StrategySummary:
    candidates = score_archetypes(role_counts, type_counts, commander_cards)
    primary, secondary, warnings = choose_primary_secondary_strategy(candidates)
    confidence = get_strategy_confidence(primary, secondary)
    return StrategySummary(
        primary_strategy=primary.name if primary else "Manual Review / Primary Uncertain",
        secondary_strategy=secondary.name if secondary else "None clearly identified",
        primary_candidate=primary,
        secondary_candidate=secondary,
        candidates=candidates,
        confidence=confidence,
        warnings=warnings,
        core_synergy_packages=get_core_synergy_packages(candidates),
    )
