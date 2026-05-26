"""Owned Card Role Classification Preview for Build From Collection v1.3.8.

This module provides preview-only role-bucket classification for owned card candidate
pool entries. It helps answer what roles an owned card might support.

Marker: Owned Card Role Classification Preview.
Marker: preview-only role classification.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No mana-base generation.
Marker: No land insertion.
Marker: No shell generation.
Marker: No deck generation.
Marker: No 100-card shell generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy, is_assumed_available_basic_land
from .candidate_pool import CollectionCandidatePoolEntry, CollectionCandidatePoolShape
from .role_buckets import create_collection_first_role_bucket_plan
from .strategy_role_mapping import create_strategy_role_bucket_mapping_preview


ROLE_BUCKET_ALIASES: dict[str, str] = {
    "ramp": "Ramp / Mana Development",
    "mana": "Ramp / Mana Development",
    "draw": "Card Draw / Card Advantage",
    "card advantage": "Card Draw / Card Advantage",
    "removal": "Targeted Removal",
    "wipe": "Board Wipes",
    "protection": "Protection",
    "recursion": "Recursion",
    "enabler": "Strategy Enablers",
    "payoff": "Strategy Payoffs",
    "finisher": "Finishers / Win Conditions",
    "mana base": "Mana Base Support",
    "land": "Mana Base Support",
    "flex": "Flex / Theme Slots",
}


ROLE_BUCKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Ramp / Mana Development": (
        "add one mana",
        "add two mana",
        "add three mana",
        "add mana",
        "add {",
        "search your library for a basic land",
        "search your library for a land",
        "put a land card",
        "treasure token",
        "treasure tokens",
    ),
    "Card Draw / Card Advantage": (
        "draw a card",
        "draw cards",
        "draw two cards",
        "draw three cards",
        "look at the top",
        "reveal the top",
        "return target card",
        "from your graveyard to your hand",
    ),
    "Targeted Removal": (
        "destroy target",
        "exile target",
        "counter target",
        "deals damage to target",
        "fight target",
        "target creature gets -",
    ),
    "Board Wipes": (
        "destroy all",
        "exile all",
        "each creature",
        "all creatures",
        "each nonland permanent",
        "all nonland permanents",
        "damage to each creature",
    ),
    "Protection": (
        "hexproof",
        "indestructible",
        "phase out",
        "protection from",
        "prevent all damage",
        "can't be countered",
        "ward",
    ),
    "Recursion": (
        "return target creature card from your graveyard",
        "return target card from your graveyard",
        "from your graveyard to the battlefield",
        "cast from your graveyard",
        "escape",
        "flashback",
        "unearth",
    ),
    "Strategy Enablers": (
        "create a token",
        "whenever you cast",
        "whenever a creature enters",
        "sacrifice a creature",
        "sacrifice another",
        "mill",
        "discard a card",
        "landfall",
        "copy target",
        "blink",
        "exile another target creature you control",
    ),
    "Strategy Payoffs": (
        "whenever",
        "for each",
        "equal to the number",
        "you gain life",
        "each opponent loses",
        "+1/+1 counter",
        "tokens you control",
        "creatures you control get",
        "artifacts you control",
        "enchantments you control",
    ),
    "Finishers / Win Conditions": (
        "you win the game",
        "each opponent loses",
        "damage to each opponent",
        "creatures you control get +",
        "double the power",
        "extra combat",
        "extra turn",
        "can't block this turn",
    ),
    "Mana Base Support": (
        "land",
        "basic land",
        "nonbasic land",
        "mana of any color",
        "colorless mana",
    ),
}


@dataclass(frozen=True, slots=True)
class OwnedCardRoleClassification:
    """Preview-only possible role-bucket fit for a single owned card candidate."""

    card_name: str
    normalized_name: str
    owned_quantity: int
    possible_role_buckets: tuple[str, ...] = field(default_factory=tuple)
    strategy_emphasis_buckets: tuple[str, ...] = field(default_factory=tuple)
    classification_reasons: tuple[str, ...] = field(default_factory=tuple)
    confidence: str = "Low"
    preview_only: bool = True
    exact_card_selection: bool = False
    role_count_target_generated: bool = False
    selected_for_deck: bool = False
    classification_complete: bool = False
    boundary_note: str = (
        "Preview-only role classification. No exact card selection, role-count target generation, "
        "mana-base generation, land insertion, shell generation, deck generation, or 100-card shell generation."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_name": self.card_name,
            "normalized_name": self.normalized_name,
            "owned_quantity": self.owned_quantity,
            "possible_role_buckets": list(self.possible_role_buckets),
            "strategy_emphasis_buckets": list(self.strategy_emphasis_buckets),
            "classification_reasons": list(self.classification_reasons),
            "confidence": self.confidence,
            "preview_only": self.preview_only,
            "exact_card_selection": self.exact_card_selection,
            "role_count_target_generated": self.role_count_target_generated,
            "selected_for_deck": self.selected_for_deck,
            "classification_complete": self.classification_complete,
            "boundary_note": self.boundary_note,
        }


@dataclass(slots=True)
class OwnedCardRoleClassificationPreview:
    """Preview container for possible role-bucket fits across owned candidates."""

    classifications: tuple[OwnedCardRoleClassification, ...] = field(default_factory=tuple)
    primary_strategy: str = ""
    secondary_strategy: str = ""
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    role_bucket_plan: Any = field(default_factory=create_collection_first_role_bucket_plan)
    preview_name: str = "Owned Card Role Classification Preview"
    preview_version: str = "v1.3.8"
    preview_only: bool = True
    collection_first: bool = True
    deferred_behavior: tuple[str, ...] = (
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell generation",
        "No deck generation",
        "No 100-card shell generation",
        "No scoring changes",
        "No cut or replacement changes",
        "No normal deck review changes",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_name": self.preview_name,
            "preview_version": self.preview_version,
            "preview_only": self.preview_only,
            "collection_first": self.collection_first,
            "primary_strategy": self.primary_strategy,
            "secondary_strategy": self.secondary_strategy,
            "classifications": [classification.to_dict() for classification in self.classifications],
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "role_bucket_plan": self.role_bucket_plan.to_dict(),
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_8_boundary": (
                "Owned card role classification is a preview only. It may identify possible role-bucket fits, "
                "but it does not select exact cards, create role-count targets, generate a mana base, insert lands, "
                "build a shell, generate a deck, score cards, recommend cuts, or change normal deck review behavior. "
                "Basic lands are assumed available; nonbasic lands remain collection-first."
            ),
        }


def normalize_role_bucket_name(bucket_name: str | None) -> str:
    """Normalize a role bucket label to the canonical v1.3.5 bucket name when possible."""
    if not bucket_name:
        return ""
    raw = " ".join(str(bucket_name).strip().split())
    key = raw.casefold()
    return ROLE_BUCKET_ALIASES.get(key, raw)


def _add_role(roles: list[str], reasons: list[str], role: str, reason: str) -> None:
    if role not in roles:
        roles.append(role)
    if reason not in reasons:
        reasons.append(reason)


def _strategy_emphasis(primary_strategy: str = "", secondary_strategy: str = "") -> tuple[str, ...]:
    preview = create_strategy_role_bucket_mapping_preview(primary_strategy=primary_strategy, secondary_strategy=secondary_strategy)
    payload = preview.to_dict()
    buckets: list[str] = []
    for key in ("primary_mapping", "secondary_mapping"):
        mapping = payload.get(key) or {}
        for bucket in mapping.get("emphasized_role_buckets", []):
            if bucket not in buckets:
                buckets.append(bucket)
    return tuple(buckets)


def classify_owned_card_role_preview(
    entry: CollectionCandidatePoolEntry,
    primary_strategy: str = "",
    secondary_strategy: str = "",
) -> OwnedCardRoleClassification:
    """Classify possible role-bucket fits for one owned candidate without selecting it for a deck."""
    text_blob = " ".join([
        entry.card_name or "",
        entry.type_line or "",
        entry.oracle_text or "",
        " ".join(entry.role_tags or ()),
    ]).casefold()
    roles: list[str] = []
    reasons: list[str] = []

    if is_assumed_available_basic_land(entry.card_name):
        _add_role(roles, reasons, "Mana Base Support", "Basic land is assumed available for future mana-base work.")
    elif "land" in (entry.type_line or "").casefold():
        _add_role(roles, reasons, "Mana Base Support", "Land or nonbasic land candidate remains collection-first.")

    for role_name, keywords in ROLE_BUCKET_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_blob:
                _add_role(roles, reasons, role_name, f"Matched role signal: {keyword}")
                break

    for tag in entry.role_tags or ():
        canonical = normalize_role_bucket_name(tag)
        if canonical and canonical in ROLE_BUCKET_KEYWORDS:
            _add_role(roles, reasons, canonical, f"Existing role tag suggests {canonical}.")

    strategy_buckets = _strategy_emphasis(primary_strategy, secondary_strategy)
    overlap = tuple(bucket for bucket in roles if bucket in strategy_buckets)
    if overlap:
        reasons.append("Possible role overlaps selected strategy emphasis.")

    if not roles:
        roles.append("Flex / Theme Slots")
        reasons.append("No strong preview signal found; keep as manual-review flex/theme candidate.")

    confidence = "Low"
    if len(roles) >= 2 or overlap:
        confidence = "Medium"
    if len(overlap) >= 2:
        confidence = "High"

    return OwnedCardRoleClassification(
        card_name=entry.card_name,
        normalized_name=entry.normalized_name,
        owned_quantity=entry.owned_quantity,
        possible_role_buckets=tuple(roles),
        strategy_emphasis_buckets=strategy_buckets,
        classification_reasons=tuple(reasons),
        confidence=confidence,
    )


def create_owned_card_role_classification_preview(
    candidate_pool: CollectionCandidatePoolShape | Iterable[CollectionCandidatePoolEntry] | None = None,
    primary_strategy: str = "",
    secondary_strategy: str = "",
) -> OwnedCardRoleClassificationPreview:
    """Create a preview-only role classification payload for owned candidate pool entries."""
    if isinstance(candidate_pool, CollectionCandidatePoolShape):
        entries = candidate_pool.entries
    else:
        entries = tuple(candidate_pool or ())
    classifications = tuple(
        classify_owned_card_role_preview(entry, primary_strategy=primary_strategy, secondary_strategy=secondary_strategy)
        for entry in entries
    )
    return OwnedCardRoleClassificationPreview(
        classifications=classifications,
        primary_strategy=primary_strategy,
        secondary_strategy=secondary_strategy,
    )
