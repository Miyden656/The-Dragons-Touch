"""Strategy-to-role bucket mapping preview for Build From Collection v1.3.6.

This module maps broad Commander strategy labels to planning-only role bucket
emphasis. It does not classify owned cards, select exact cards, generate role-count
targets, build a mana base, insert lands, generate a 100-card shell, generate a
deck, score cards, recommend cuts, or change normal deck review behavior.

Marker: Strategy-to-Role Bucket Mapping Preview.
Marker: No owned card classification.
Marker: No exact card selection.
Marker: No deck generation.
Marker: No 100-card shell generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy
from .role_buckets import CollectionFirstRoleBucketPlan, create_collection_first_role_bucket_plan


CORE_SUPPORT_ROLE_BUCKETS: tuple[str, ...] = (
    "Ramp / Mana Development",
    "Card Draw / Card Advantage",
    "Targeted Removal",
    "Protection",
)


STRATEGY_TO_ROLE_BUCKET_MAPPING: dict[str, tuple[str, ...]] = {
    "aristocrats": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Recursion",
        "Finishers / Win Conditions",
    ),
    "tokens": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Finishers / Win Conditions",
        "Protection",
    ),
    "lifegain": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Card Draw / Card Advantage",
        "Finishers / Win Conditions",
    ),
    "voltron": (
        "Strategy Enablers",
        "Protection",
        "Targeted Removal",
        "Finishers / Win Conditions",
    ),
    "spellslinger": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Card Draw / Card Advantage",
        "Finishers / Win Conditions",
    ),
    "graveyard_recursion": (
        "Strategy Enablers",
        "Recursion",
        "Strategy Payoffs",
        "Finishers / Win Conditions",
    ),
    "reanimator": (
        "Strategy Enablers",
        "Recursion",
        "Finishers / Win Conditions",
        "Protection",
    ),
    "go_wide_combat": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Protection",
        "Finishers / Win Conditions",
    ),
    "plus_one_plus_one_counters": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Protection",
        "Finishers / Win Conditions",
    ),
    "artifacts": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Recursion",
        "Mana Base Support",
    ),
    "enchantress": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Card Draw / Card Advantage",
        "Protection",
    ),
    "landfall": (
        "Ramp / Mana Development",
        "Strategy Enablers",
        "Strategy Payoffs",
        "Mana Base Support",
    ),
    "sacrifice": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Recursion",
        "Finishers / Win Conditions",
    ),
    "blink_flicker": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Protection",
        "Card Draw / Card Advantage",
    ),
    "ramp_into_big_threats": (
        "Ramp / Mana Development",
        "Card Draw / Card Advantage",
        "Finishers / Win Conditions",
        "Protection",
    ),
    "control": (
        "Targeted Removal",
        "Board Wipes",
        "Card Draw / Card Advantage",
        "Finishers / Win Conditions",
    ),
    "combo_adjacent_value": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Card Draw / Card Advantage",
        "Protection",
    ),
    "tribal": (
        "Strategy Enablers",
        "Strategy Payoffs",
        "Protection",
        "Finishers / Win Conditions",
    ),
}


STRATEGY_ALIASES: dict[str, str] = {
    "aristocrat": "aristocrats",
    "aristocrats": "aristocrats",
    "token": "tokens",
    "tokens": "tokens",
    "lifegain": "lifegain",
    "life gain": "lifegain",
    "voltron": "voltron",
    "spellslinger": "spellslinger",
    "spells": "spellslinger",
    "graveyard": "graveyard_recursion",
    "graveyard recursion": "graveyard_recursion",
    "graveyard_recursion": "graveyard_recursion",
    "reanimator": "reanimator",
    "go wide": "go_wide_combat",
    "go-wide": "go_wide_combat",
    "go wide combat": "go_wide_combat",
    "go_wide_combat": "go_wide_combat",
    "+1/+1 counters": "plus_one_plus_one_counters",
    "plus one plus one counters": "plus_one_plus_one_counters",
    "plus_one_plus_one_counters": "plus_one_plus_one_counters",
    "artifacts": "artifacts",
    "artifact": "artifacts",
    "enchantress": "enchantress",
    "enchantments": "enchantress",
    "landfall": "landfall",
    "sacrifice": "sacrifice",
    "sac": "sacrifice",
    "blink": "blink_flicker",
    "flicker": "blink_flicker",
    "blink/flicker": "blink_flicker",
    "blink_flicker": "blink_flicker",
    "ramp": "ramp_into_big_threats",
    "ramp into big threats": "ramp_into_big_threats",
    "ramp_into_big_threats": "ramp_into_big_threats",
    "control": "control",
    "combo adjacent value": "combo_adjacent_value",
    "combo-adjacent value": "combo_adjacent_value",
    "combo_adjacent_value": "combo_adjacent_value",
    "tribal": "tribal",
    "typal": "tribal",
}


@dataclass(frozen=True, slots=True)
class StrategyRoleBucketMapping:
    """Planning-only mapping from one strategy to emphasized role buckets."""

    strategy_key: str
    strategy_label: str
    emphasized_role_buckets: tuple[str, ...]
    support_role_buckets: tuple[str, ...] = CORE_SUPPORT_ROLE_BUCKETS
    planning_note: str = (
        "Planning-only role emphasis. No owned card classification, exact card selection, "
        "role-count target generation, 100-card shell generation, or deck generation."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_key": self.strategy_key,
            "strategy_label": self.strategy_label,
            "emphasized_role_buckets": list(self.emphasized_role_buckets),
            "support_role_buckets": list(self.support_role_buckets),
            "planning_note": self.planning_note,
        }


@dataclass(slots=True)
class StrategyRoleBucketMappingPreview:
    """Display-ready strategy-to-role bucket mapping preview for future shell planning."""

    primary_strategy: StrategyRoleBucketMapping
    secondary_strategy: StrategyRoleBucketMapping | None = None
    role_bucket_plan: CollectionFirstRoleBucketPlan = field(default_factory=create_collection_first_role_bucket_plan)
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    preview_version: str = "v1.3.6"
    preview_name: str = "Strategy-to-Role Bucket Mapping Preview"
    planning_only: bool = True
    deferred_behavior: list[str] = field(default_factory=lambda: [
        "No owned card classification",
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No deck generation",
        "No 100-card shell generation",
        "No scoring changes",
        "No cut or replacement changes",
        "No normal deck review changes",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_version": self.preview_version,
            "preview_name": self.preview_name,
            "planning_only": self.planning_only,
            "primary_strategy": self.primary_strategy.to_dict(),
            "secondary_strategy": self.secondary_strategy.to_dict() if self.secondary_strategy else None,
            "role_bucket_plan": self.role_bucket_plan.to_dict(),
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_6_boundary": (
                "Strategy-to-role bucket mapping is planning-only. v1.3.6 does not classify "
                "owned cards, select exact cards, create role-count targets, generate a deck, "
                "create a 100-card shell, build a mana base, insert lands, score cards, recommend "
                "cuts, or change normal deck review behavior. Basic lands are assumed available; "
                "nonbasic lands remain collection-first."
            ),
        }


def normalize_strategy_key(strategy: str | None) -> str:
    """Normalize user-facing strategy text into a baseline strategy key."""
    if not strategy:
        return "custom_or_unknown"
    cleaned = " ".join(str(strategy).strip().lower().replace("_", " ").split())
    return STRATEGY_ALIASES.get(cleaned, cleaned.replace(" ", "_"))


def display_label_for_strategy_key(strategy_key: str) -> str:
    """Return a readable display label for a normalized strategy key."""
    labels = {
        "aristocrats": "Aristocrats",
        "tokens": "Tokens",
        "lifegain": "Lifegain",
        "voltron": "Voltron",
        "spellslinger": "Spellslinger",
        "graveyard_recursion": "Graveyard Recursion",
        "reanimator": "Reanimator",
        "go_wide_combat": "Go-Wide Combat",
        "plus_one_plus_one_counters": "+1/+1 Counters",
        "artifacts": "Artifacts",
        "enchantress": "Enchantress",
        "landfall": "Landfall",
        "sacrifice": "Sacrifice",
        "blink_flicker": "Blink / Flicker",
        "ramp_into_big_threats": "Ramp Into Big Threats",
        "control": "Control",
        "combo_adjacent_value": "Combo-Adjacent Value",
        "tribal": "Tribal / Typal",
        "custom_or_unknown": "Custom / Unknown Strategy",
    }
    return labels.get(strategy_key, strategy_key.replace("_", " ").title())


def create_strategy_role_bucket_mapping(strategy: str | None) -> StrategyRoleBucketMapping:
    """Create a planning-only role bucket mapping for one strategy."""
    strategy_key = normalize_strategy_key(strategy)
    emphasized = STRATEGY_TO_ROLE_BUCKET_MAPPING.get(
        strategy_key,
        (
            "Strategy Enablers",
            "Strategy Payoffs",
            "Card Draw / Card Advantage",
            "Flex / Theme Slots",
        ),
    )
    return StrategyRoleBucketMapping(
        strategy_key=strategy_key,
        strategy_label=display_label_for_strategy_key(strategy_key),
        emphasized_role_buckets=emphasized,
    )


def create_strategy_role_bucket_mapping_preview(
    primary_strategy: str | None,
    secondary_strategy: str | None = None,
) -> StrategyRoleBucketMappingPreview:
    """Create a display-ready, planning-only strategy-to-role bucket preview."""
    secondary = None
    if secondary_strategy and str(secondary_strategy).strip().lower() not in {"", "n/a", "none", "na"}:
        secondary = create_strategy_role_bucket_mapping(secondary_strategy)
    return StrategyRoleBucketMappingPreview(
        primary_strategy=create_strategy_role_bucket_mapping(primary_strategy),
        secondary_strategy=secondary,
        role_bucket_plan=create_collection_first_role_bucket_plan(),
        basic_land_policy=create_basic_land_access_policy(),
    )
