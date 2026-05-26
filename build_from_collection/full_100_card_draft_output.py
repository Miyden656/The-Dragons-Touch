"""Full 100-Card Draft Output Model.

v1.3.24 Full 100-Card Draft Output Model.

This module defines the model-only depth-E output contract for the future
Full 100-Card Draft path in Commander's Call.

It intentionally represents a future output shape only.

No exact card selection in this patch.
No final deck inclusion decisions in this patch.
No role-count target generation in this patch.
No mana-base generation in this patch.
No land insertion in this patch.
No completed shell generation in this patch.
No shell generation in this patch.
No deck generation in this patch.
No 100-card draft generation in this patch.

Basic lands are assumed available.
Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


DEFAULT_FULL_DRAFT_SECTION_NAMES: tuple[str, ...] = (
    "Selected Commander",
    "Build Depth and User Preferences",
    "Strategy and Philosophy Context",
    "Collection-First Candidate Pool",
    "Nonland Spell Draft Area",
    "Mana Base Draft Area",
    "Assumed Basic Land Policy",
    "Nonbasic Land Collection Check",
    "Outside-Collection Upgrade Queue",
    "Unresolved Slots and Missing Roles",
    "Validation and Safety Notes",
    "Future Final 100-Card Draft",
)


@dataclass(frozen=True)
class Full100CardDraftSection:
    """A named section in the future full 100-card draft output model."""

    name: str
    purpose: str
    is_future_generation_area: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "is_future_generation_area": self.is_future_generation_area,
        }


@dataclass(frozen=True)
class Full100CardDraftOutputModel:
    """Model-only depth E - Full 100-Card Draft output contract."""

    selected_commander: str = "Selected Commander"
    build_depth_key: str = "E"
    depth_key: str = "E"
    selected_build_depth_key: str = "E"
    build_depth_label: str = "E - Full 100-Card Draft"
    depth_label: str = "E - Full 100-Card Draft"
    output_name: str = "Full 100-Card Draft Output Model"
    sections: tuple[Full100CardDraftSection, ...] = field(default_factory=tuple)

    future_full_100_card_draft_intent: bool = True
    model_only: bool = True
    generates_deck: bool = False
    generates_100_card_draft: bool = False
    generates_shell: bool = False
    generates_completed_shell: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False

    basic_land_policy: str = "Basic lands are assumed available."
    nonbasic_land_policy: str = (
        "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
    )
    boundary_note: str = (
        "Depth E is represented as a future full-draft output contract only; "
        "this patch does not generate a 100-card deck."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_commander": self.selected_commander,
            "build_depth_key": self.build_depth_key,
            "depth_key": self.depth_key,
            "selected_build_depth_key": self.selected_build_depth_key,
            "build_depth_label": self.build_depth_label,
            "depth_label": self.depth_label,
            "output_name": self.output_name,
            "sections": [section.to_dict() for section in self.sections],
            "future_full_100_card_draft_intent": self.future_full_100_card_draft_intent,
            "model_only": self.model_only,
            "generates_deck": self.generates_deck,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_shell": self.generates_shell,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "basic_land_policy": self.basic_land_policy,
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "boundary_note": self.boundary_note,
        }


def create_full_100_card_draft_section(
    name: str,
    purpose: str = "",
    *,
    is_future_generation_area: bool = True,
) -> Full100CardDraftSection:
    """Create a section entry for the model-only full draft contract."""

    return Full100CardDraftSection(
        name=str(name).strip() or "Unnamed Full Draft Section",
        purpose=str(purpose).strip() or "Future full draft output section.",
        is_future_generation_area=bool(is_future_generation_area),
    )


def _default_sections() -> tuple[Full100CardDraftSection, ...]:
    purposes = {
        "Selected Commander": "Carries the selected commander into the future full-draft output.",
        "Build Depth and User Preferences": "Records build depth, strategy, philosophy, bracket, and collection settings.",
        "Strategy and Philosophy Context": "Explains how strategy and player preference should guide future selection.",
        "Collection-First Candidate Pool": "Groups owned cards before any final inclusion decisions are made.",
        "Nonland Spell Draft Area": "Future space for nonland spell candidates and unresolved spell slots.",
        "Mana Base Draft Area": "Future space for mana-base candidates without generating a mana base now.",
        "Assumed Basic Land Policy": "Records that ordinary basic lands are assumed available.",
        "Nonbasic Land Collection Check": "Records that nonbasic lands remain collection-first unless upgrades are allowed.",
        "Outside-Collection Upgrade Queue": "Future space for user-approved outside-collection suggestions.",
        "Unresolved Slots and Missing Roles": "Future space for open needs without inventing final counts now.",
        "Validation and Safety Notes": "Future space for legality and sanity checks.",
        "Future Final 100-Card Draft": "Placeholder for a later generated full draft, not created in this patch.",
    }
    return tuple(
        create_full_100_card_draft_section(name, purposes.get(name, "Future section."))
        for name in DEFAULT_FULL_DRAFT_SECTION_NAMES
    )


def create_full_100_card_draft_output_model(
    selected_commander: str = "Selected Commander",
    sections: Iterable[Full100CardDraftSection | str] | None = None,
) -> Full100CardDraftOutputModel:
    """Create the model-only depth-E output contract."""

    normalized_sections: list[Full100CardDraftSection] = []
    if sections is None:
        normalized_sections.extend(_default_sections())
    else:
        for section in sections:
            if isinstance(section, Full100CardDraftSection):
                normalized_sections.append(section)
            else:
                normalized_sections.append(create_full_100_card_draft_section(str(section)))

    return Full100CardDraftOutputModel(
        selected_commander=str(selected_commander).strip() or "Selected Commander",
        sections=tuple(normalized_sections),
    )


def full_100_card_draft_section_names() -> list[str]:
    """Return default section names for the future depth-E output contract."""

    return list(DEFAULT_FULL_DRAFT_SECTION_NAMES)


def full_100_card_draft_output_model_lines(model: Full100CardDraftOutputModel) -> list[str]:
    """Return human-readable model-only summary lines."""

    lines = [
        "Full 100-Card Draft Output Model",
        f"Selected commander: {model.selected_commander}",
        f"Build depth: {model.build_depth_label}",
        "Status: model-only future output contract.",
        model.basic_land_policy,
        model.nonbasic_land_policy,
        "Boundary: this patch does not generate a 100-card deck.",
        "Boundary: this patch does not select exact cards or make final deck inclusion decisions.",
        "Future sections:",
    ]
    for section in model.sections:
        lines.append(f"- {section.name}: {section.purpose}")
    return lines


def full_100_card_draft_handoff_prompt(model: Full100CardDraftOutputModel) -> str:
    """Return an AI handoff prompt for the model-only future full draft output."""

    lines = [
        "AI handoff prompt: Full 100-Card Draft Output Model.",
        f"Selected commander: {model.selected_commander}",
        f"Build depth: {model.build_depth_label}",
        "This is not a final decklist.",
        "This is not a generated 100-card deck.",
        "Preserve the no-deck-generation boundary for v1.3.24.",
        "Use this as a future output contract only.",
        model.basic_land_policy,
        model.nonbasic_land_policy,
    ]
    return "\n".join(lines)
