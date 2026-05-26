"""Basic land access policy for Build From Collection v1.3.3.

v1.3.3 records the project rule that Build From Collection should assume the
user can access all needed basic lands. This is a policy/data helper only: it
must not add lands to a deck, generate a 100-card shell, or change normal deck
review behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ASSUMED_AVAILABLE_BASIC_LANDS: tuple[str, ...] = (
    "Plains",
    "Island",
    "Swamp",
    "Mountain",
    "Forest",
    "Wastes",
)

ASSUMED_AVAILABLE_BASIC_LANDS_NORMALIZED: frozenset[str] = frozenset(
    land.casefold() for land in ASSUMED_AVAILABLE_BASIC_LANDS
)

BASIC_LAND_ACCESS_ASSUMPTION = (
    "Build From Collection assumes the user has access to every needed basic "
    "land: Plains, Island, Swamp, Mountain, Forest, and Wastes. Users should "
    "not need to scan or count basic lands for collection-first shell planning."
)


@dataclass(frozen=True, slots=True)
class BasicLandAccessPolicy:
    """Display-safe basic land policy payload for future shell planning."""

    assumed_available_basic_lands: tuple[str, ...] = ASSUMED_AVAILABLE_BASIC_LANDS
    nonbasic_lands_remain_collection_first: bool = True
    policy_name: str = "Basic Land Access Assumption"
    policy_version: str = "v1.3.3"
    boundary: str = (
        "Basic land access policy only. This does not add lands, generate a "
        "mana base, create a 100-card shell, or change deck review behavior."
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["assumption"] = BASIC_LAND_ACCESS_ASSUMPTION
        data["v1_3_3_boundary"] = self.boundary
        return data


def is_assumed_available_basic_land(card_name: str) -> bool:
    """Return True when card_name is one of the assumed-available basics."""
    return str(card_name or "").strip().casefold() in ASSUMED_AVAILABLE_BASIC_LANDS_NORMALIZED


def create_basic_land_access_policy() -> BasicLandAccessPolicy:
    """Return the v1.3.3 basic land access policy payload."""
    return BasicLandAccessPolicy()


def describe_basic_land_access_assumption() -> str:
    """Return a concise player-facing description of the basic-land rule."""
    return (
        f"{BASIC_LAND_ACCESS_ASSUMPTION} Nonbasic lands remain collection-first. "
        "No deck generation or land insertion happens in v1.3.3."
    )
