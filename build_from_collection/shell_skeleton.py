"""Commander Shell Skeleton Preview for Build From Collection v1.3.9.

This module creates a preview-only skeleton for the eventual Build From Collection
Commander shell. It describes the sections a future shell will need without filling
those sections with exact cards or role-count targets.

Marker: Commander Shell Skeleton Preview.
Marker: shell skeleton is preview-only.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No mana-base generation.
Marker: No land insertion.
Marker: No shell completion.
Marker: No deck generation.
Marker: No 100-card shell generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first.
Marker: v1.3.9.2 explicit nonbasic land policy runtime payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy
from .role_buckets import CollectionFirstRoleBucketPlan, create_collection_first_role_bucket_plan


SHELL_SKELETON_SECTIONS: tuple[str, ...] = (
    "Commander",
    "Strategy Plan",
    "Core Role Buckets",
    "Collection Candidate Pool",
    "Owned Card Role Classification Preview",
    "Basic Land Access Policy",
    "Nonbasic Land Collection Check",
    "Future Mana Base Plan",
    "Future Final Deck Shell",
)


@dataclass(frozen=True, slots=True)
class CommanderShellSkeletonSection:
    """Preview-only section in a future Build From Collection shell."""

    section_name: str
    purpose: str
    current_status: str = "Preview only"
    filled_now: bool = False
    exact_cards_selected: bool = False
    role_count_target_generated: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_name": self.section_name,
            "purpose": self.purpose,
            "current_status": self.current_status,
            "filled_now": self.filled_now,
            "exact_cards_selected": self.exact_cards_selected,
            "role_count_target_generated": self.role_count_target_generated,
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class CommanderShellSkeletonPreview:
    """Preview-only shell skeleton for a future commander deck build."""

    selected_commander: Any = None
    primary_strategy: str = ""
    secondary_strategy: str = ""
    sections: tuple[CommanderShellSkeletonSection, ...] = field(default_factory=tuple)
    role_bucket_plan: CollectionFirstRoleBucketPlan = field(default_factory=create_collection_first_role_bucket_plan)
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    nonbasic_land_policy: str = "Nonbasic lands remain collection-first."
    preview_name: str = "Commander Shell Skeleton Preview"
    preview_version: str = "v1.3.9"
    preview_only: bool = True
    collection_first: bool = True
    shell_completed: bool = False
    exact_card_selection: bool = False
    role_count_target_generated: bool = False
    mana_base_generated: bool = False
    land_inserted: bool = False
    deck_generated: bool = False
    deferred_behavior: tuple[str, ...] = (
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell completion",
        "No shell generation",
        "No deck generation",
        "No 100-card shell generation",
        "No scoring changes",
        "No cut or replacement changes",
        "No normal deck review changes",
    )

    def to_dict(self) -> dict[str, Any]:
        commander_payload: Any
        if hasattr(self.selected_commander, "to_dict"):
            commander_payload = self.selected_commander.to_dict()
        else:
            commander_payload = self.selected_commander
        return {
            "preview_name": self.preview_name,
            "preview_version": self.preview_version,
            "preview_only": self.preview_only,
            "collection_first": self.collection_first,
            "selected_commander": commander_payload,
            "primary_strategy": self.primary_strategy,
            "secondary_strategy": self.secondary_strategy,
            "sections": [section.to_dict() for section in self.sections],
            "role_bucket_plan": self.role_bucket_plan.to_dict(),
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "shell_completed": self.shell_completed,
            "exact_card_selection": self.exact_card_selection,
            "role_count_target_generated": self.role_count_target_generated,
            "mana_base_generated": self.mana_base_generated,
            "land_inserted": self.land_inserted,
            "deck_generated": self.deck_generated,
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_9_boundary": (
                "Commander Shell Skeleton Preview is a non-card, non-count shell outline only. "
                "It does not select exact cards, create role-count targets, generate a mana base, insert lands, "
                "complete a shell, generate a deck, score cards, recommend cuts, or change normal deck review behavior. "
                "Basic lands are assumed available; nonbasic lands remain collection-first."
            ),
            "v1_3_9_2_boundary": (
                "Nonbasic lands remain collection-first is explicit runtime payload text. "
                "This patch does not assume access to Command Tower, shock lands, fetch lands, triomes, utility lands, MDFCs, or other nonbasic lands."
            ),
        }


def _default_section_purpose(section_name: str) -> str:
    purposes = {
        "Commander": "Carry the selected commander from The Commander's Call into future build planning.",
        "Strategy Plan": "Carry primary and secondary strategy intent into future role and card evaluation.",
        "Core Role Buckets": "Show the planning categories the future shell will need to consider.",
        "Collection Candidate Pool": "Reserve space for owned collection candidates before exact card selection exists.",
        "Owned Card Role Classification Preview": "Reserve space for preview-only owned-card role labels.",
        "Basic Land Access Policy": "Document that ordinary basic lands are assumed available.",
        "Nonbasic Land Collection Check": "Keep nonbasic lands collection-first for future mana-base work.",
        "Future Mana Base Plan": "Reserve space for later mana-base planning without generating lands now.",
        "Future Final Deck Shell": "Reserve space for the eventual deck shell without building it now.",
    }
    return purposes.get(section_name, "Preview-only future shell section.")


def create_commander_shell_skeleton_section(section_name: str, notes: Iterable[str] | None = None) -> CommanderShellSkeletonSection:
    """Create one preview-only shell skeleton section with no cards selected."""
    return CommanderShellSkeletonSection(
        section_name=section_name,
        purpose=_default_section_purpose(section_name),
        notes=tuple(notes or ()),
    )


def create_commander_shell_skeleton_preview(
    selected_commander: Any = None,
    primary_strategy: str = "",
    secondary_strategy: str = "",
    section_names: Iterable[str] | None = None,
) -> CommanderShellSkeletonPreview:
    """Create a preview-only Commander shell skeleton without filling the shell."""
    names = tuple(section_names or SHELL_SKELETON_SECTIONS)
    sections = tuple(create_commander_shell_skeleton_section(name) for name in names)
    return CommanderShellSkeletonPreview(
        selected_commander=selected_commander,
        primary_strategy=primary_strategy or "",
        secondary_strategy=secondary_strategy or "",
        sections=sections,
    )


def shell_skeleton_section_names() -> tuple[str, ...]:
    """Return canonical shell skeleton section names for v1.3.9."""
    return SHELL_SKELETON_SECTIONS
