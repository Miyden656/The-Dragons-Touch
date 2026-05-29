"""Rough Shell Output Model.

Defines the depth-D Rough Shell section schema and AI handoff text.

Rough Shell is "what to look for in your collection" guidance for the
commander + strategy combination — it lists relevant role tags with
plain-English descriptions, oracle keywords, and example cards. It
is intentionally not a generated deck.

The actual guidance markdown is built by build_rough_shell_markdown() in
rough_shell_guidance.py. This module supplies the surrounding section
schema and AI handoff prompt used by the report writer.

Land policy:
- Basic lands are assumed available.
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.

The dataclass boundary flags (generates_deck, generates_shell, etc.) remain
False because Rough Shell genuinely is guidance-only — the deck-generation
features live at depth E (Full 100-Card Draft). Do not flip them without
auditing dev-mode contract callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


DEFAULT_ROUGH_SHELL_SECTIONS: tuple[str, ...] = (
    "Commander Context",
    "Strategy Plan",
    "Core Role Buckets",
    "What To Look For In Your Collection",
    "Role-Tag Guidance",
    "Basic Land Access Policy",
    "Nonbasic Land Collection-First Policy",
    "Next Step: Full 100-Card Draft",
)


@dataclass(frozen=True)
class RoughShellSection:
    """A named rough-shell section contract only."""

    name: str
    purpose: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)
    is_model_only: bool = True
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    generates_shell: bool = False
    generates_deck: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "notes": list(self.notes),
            "is_model_only": self.is_model_only,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "generates_shell": self.generates_shell,
            "generates_deck": self.generates_deck,
        }


@dataclass(frozen=True)
class RoughShellOutputModel:
    """Depth-D rough shell output model."""

    name: str = "Rough Shell Output Model"
    build_depth_key: str = "D"
    depth_key: str = "D"
    selected_build_depth_key: str = "D"
    build_depth_label: str = "D - Rough Shell"
    depth_label: str = "D - Rough Shell"
    is_model_only: bool = True
    is_rough_shell: bool = True
    is_completed_shell: bool = False
    is_final_deck: bool = False
    sections: tuple[RoughShellSection, ...] = field(default_factory=tuple)

    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    generates_completed_shell: bool = False
    generates_shell: bool = False
    generates_deck: bool = False

    basic_land_policy: str = "Basic lands are assumed available."
    nonbasic_land_policy: str = (
        "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
    )

    boundary_note: str = (
        "Rough Shell is collection-scan guidance, not a generated deck. "
        "It tells the user what to look for in their collection for the chosen commander + strategy. "
        "Use the Full 100-Card Draft button to generate an actual decklist."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "build_depth_key": self.build_depth_key,
            "depth_key": self.depth_key,
            "selected_build_depth_key": self.selected_build_depth_key,
            "build_depth_label": self.build_depth_label,
            "depth_label": self.depth_label,
            "is_model_only": self.is_model_only,
            "is_rough_shell": self.is_rough_shell,
            "is_completed_shell": self.is_completed_shell,
            "is_final_deck": self.is_final_deck,
            "sections": [section.to_dict() for section in self.sections],
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_shell": self.generates_shell,
            "generates_deck": self.generates_deck,
            "basic_land_policy": self.basic_land_policy,
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "boundary_note": self.boundary_note,
        }


def create_rough_shell_section(name: str, purpose: str = "", notes: Iterable[str] | None = None) -> RoughShellSection:
    """Create a rough-shell section contract only."""
    return RoughShellSection(
        name=str(name).strip() or "Unnamed Rough Shell Section",
        purpose=str(purpose).strip(),
        notes=tuple(str(note).strip() for note in (notes or ()) if str(note).strip()),
    )


def create_rough_shell_output_model(sections: Iterable[RoughShellSection | str] | None = None) -> RoughShellOutputModel:
    """Create a model-only rough shell output. No shell generation occurs here."""
    if sections is None:
        section_objects = tuple(create_rough_shell_section(name) for name in DEFAULT_ROUGH_SHELL_SECTIONS)
    else:
        built: list[RoughShellSection] = []
        for section in sections:
            built.append(section if isinstance(section, RoughShellSection) else create_rough_shell_section(str(section)))
        section_objects = tuple(built)
    return RoughShellOutputModel(sections=section_objects)


def rough_shell_section_names(model: RoughShellOutputModel | None = None) -> list[str]:
    """Return rough-shell section names."""
    actual = model or create_rough_shell_output_model()
    return [section.name for section in actual.sections]


def rough_shell_output_model_lines(model: RoughShellOutputModel | None = None) -> list[str]:
    """Return human-readable rough-shell summary lines."""
    actual = model or create_rough_shell_output_model()
    lines = [
        actual.name,
        f"Build depth: {actual.build_depth_label}",
        "Rough Shell is collection-scan guidance, not a generated deck.",
        actual.basic_land_policy,
        actual.nonbasic_land_policy,
        "",
        "Rough Shell sections:",
    ]
    for section in actual.sections:
        lines.append(f"- {section.name}")
    lines.extend([
        "",
        "To generate an actual decklist from your collection, use the Full 100-Card Draft button.",
    ])
    return lines


def rough_shell_handoff_prompt(model: RoughShellOutputModel | None = None) -> str:
    """Return AI handoff prompt text for the Rough Shell guidance."""
    actual = model or create_rough_shell_output_model()
    lines = [
        "AI Handoff Prompt - Rough Shell",
        "",
        "This file accompanies collection-scan guidance for a Commander build.",
        "It is not a generated decklist — it tells the user what to look for in their collection.",
        "",
        f"Build depth: {actual.build_depth_label}",
        actual.basic_land_policy,
        actual.nonbasic_land_policy,
        "",
        "Useful follow-ups for the user:",
        "- Suggest owned-card candidates that match the role-tag guidance shown.",
        "- Flag missing roles where the user's collection may be thin.",
        "- Recommend affordable outside-collection upgrades for weak roles, if the user is open to them.",
        "",
        "Sections in the guidance file:",
    ]
    lines.extend(f"- {section.name}" for section in actual.sections)
    return "\n".join(lines)


__all__ = [
    "DEFAULT_ROUGH_SHELL_SECTIONS",
    "RoughShellSection",
    "RoughShellOutputModel",
    "create_rough_shell_section",
    "create_rough_shell_output_model",
    "rough_shell_section_names",
    "rough_shell_output_model_lines",
    "rough_shell_handoff_prompt",
]
