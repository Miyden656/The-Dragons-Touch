"""Collection-first role bucket planning baseline for Build From Collection v1.3.5.

This module defines planning-only role buckets for future collection-built Commander
shells. It does not classify owned cards, select cards, generate a deck, create a
100-card shell, build a mana base, insert lands, score cards, or change normal deck
review behavior.
Marker: Basic lands are assumed available; nonbasic lands remain collection-first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy


@dataclass(frozen=True, slots=True)
class CollectionFirstRoleBucketDefinition:
    """A planning-only role bucket for a future collection-first Commander shell."""

    key: str
    display_name: str
    purpose: str
    collection_first_rule: str
    examples: tuple[str, ...] = ()
    deferred_behavior: tuple[str, ...] = (
        "No owned card classification",
        "No exact card selection",
        "No deck generation",
        "No 100-card shell generation",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "purpose": self.purpose,
            "collection_first_rule": self.collection_first_rule,
            "examples": list(self.examples),
            "deferred_behavior": list(self.deferred_behavior),
        }


COLLECTION_FIRST_ROLE_BUCKETS: tuple[CollectionFirstRoleBucketDefinition, ...] = (
    CollectionFirstRoleBucketDefinition(
        key="ramp_mana_development",
        display_name="Ramp / Mana Development",
        purpose="Help the deck cast its commander and execute its plan on time.",
        collection_first_rule="Future selection should prefer owned ramp and mana-development cards first.",
        examples=("mana rocks", "land ramp", "cost reducers", "treasure makers"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="card_draw_card_advantage",
        display_name="Card Draw / Card Advantage",
        purpose="Keep resources flowing so the deck does not run out of action.",
        collection_first_rule="Future selection should prefer owned draw engines, impulse draw, recursion-as-advantage, or repeatable value first.",
        examples=("draw spells", "repeatable draw engines", "impulse draw", "value creatures"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="targeted_removal",
        display_name="Targeted Removal",
        purpose="Answer specific opposing threats that would stop the deck's plan.",
        collection_first_rule="Future selection should prefer owned efficient interaction that fits the commander's color identity first.",
        examples=("creature removal", "artifact removal", "enchantment removal", "flexible removal"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="board_wipes",
        display_name="Board Wipes",
        purpose="Reset problem boards when targeted answers are not enough.",
        collection_first_rule="Future selection should prefer owned sweepers that fit the deck's strategy and bracket preference first.",
        examples=("creature sweepers", "artifact wipes", "asymmetric wipes", "damage-based wipes"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="protection",
        display_name="Protection",
        purpose="Protect the commander, key engines, or final push from disruption.",
        collection_first_rule="Future selection should prefer owned protection pieces that match the deck's actual risk profile first.",
        examples=("hexproof effects", "indestructible effects", "countermagic", "recursion protection"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="recursion",
        display_name="Recursion",
        purpose="Reuse important cards and recover after removal or wipes.",
        collection_first_rule="Future selection should prefer owned recursion that supports the primary strategy first.",
        examples=("graveyard recursion", "artifact recursion", "creature reanimation", "spell rebuy"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="strategy_enablers",
        display_name="Strategy Enablers",
        purpose="Make the commander's primary and secondary strategies function.",
        collection_first_rule="Future selection should prefer owned cards that turn the deck's main engine on first.",
        examples=("token makers", "sacrifice outlets", "graveyard setup", "landfall triggers"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="strategy_payoffs",
        display_name="Strategy Payoffs",
        purpose="Reward the deck for doing the thing it is built to do.",
        collection_first_rule="Future selection should prefer owned payoffs that directly reward the chosen strategy first.",
        examples=("aristocrats payoffs", "anthem effects", "spell payoffs", "+1/+1 counter payoffs"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="finishers_win_conditions",
        display_name="Finishers / Win Conditions",
        purpose="Turn the deck's engine or board position into a way to win the game.",
        collection_first_rule="Future selection should prefer owned finishers that fit the commander's strategy and bracket first.",
        examples=("combat closers", "big X spells", "combo-adjacent finishers", "overrun effects"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="mana_base_support",
        display_name="Mana Base Support",
        purpose="Support the deck's color needs and utility land plan.",
        collection_first_rule="Nonbasic lands remain collection-first. Basic lands are assumed available.",
        examples=("dual lands", "tri lands", "utility lands", "color fixing"),
    ),
    CollectionFirstRoleBucketDefinition(
        key="flex_theme_slots",
        display_name="Flex / Theme Slots",
        purpose="Leave room for pet cards, flavor cards, meta calls, and player-expression choices.",
        collection_first_rule="Future selection should prefer owned cards that match the user's philosophy, theme, or local meta needs first.",
        examples=("pet cards", "theme cards", "meta tech", "bracket-safe upgrades"),
    ),
)


@dataclass(slots=True)
class CollectionFirstRoleBucketPlan:
    """Planning-only role bucket baseline for future Build From Collection work."""

    role_buckets: tuple[CollectionFirstRoleBucketDefinition, ...] = COLLECTION_FIRST_ROLE_BUCKETS
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    plan_version: str = "v1.3.5"
    plan_name: str = "Collection-First Role Bucket Planning Baseline"
    planning_only: bool = True
    future_selection_rule: str = "Prefer owned cards first for nonbasic, non-assumed cards."
    deferred_behavior: list[str] = field(default_factory=lambda: [
        "No owned card classification",
        "No exact card selection",
        "No deck generation",
        "No 100-card shell generation",
        "No role-count targets yet",
        "No mana-base generation",
        "No land insertion",
        "No scoring changes",
        "No cut or replacement changes",
        "No normal deck review changes",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_version": self.plan_version,
            "plan_name": self.plan_name,
            "planning_only": self.planning_only,
            "future_selection_rule": self.future_selection_rule,
            "role_buckets": [bucket.to_dict() for bucket in self.role_buckets],
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_5_boundary": (
                "Collection-first role buckets are planning categories only. v1.3.5 does not "
                "classify owned cards, select exact cards, create role-count targets, generate a "
                "deck, create a 100-card shell, build a mana base, insert lands, score cards, or "
                "change normal deck review behavior. Basic lands are assumed available; nonbasic "
                "lands remain collection-first."
            ),
        }


def create_collection_first_role_bucket_plan() -> CollectionFirstRoleBucketPlan:
    """Create the v1.3.5 planning-only role bucket baseline."""
    return CollectionFirstRoleBucketPlan(
        role_buckets=COLLECTION_FIRST_ROLE_BUCKETS,
        basic_land_policy=create_basic_land_access_policy(),
    )


def role_bucket_names() -> list[str]:
    """Return display names for the baseline planning role buckets."""
    return [bucket.display_name for bucket in COLLECTION_FIRST_ROLE_BUCKETS]
