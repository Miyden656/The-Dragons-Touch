"""Rough Shell Output Model.

v1.3.22.1 syntax recovery hotfix.

This module supports depth D - Rough Shell by defining a rough shell
output model. It is intentionally model-only for now.

Rough shell, not final deck.

No exact card selection in this patch.
No final deck inclusion decisions in this patch.
No role-count target generation in this patch.
No mana-base generation in this patch.
No land insertion in this patch.
No completed shell generation in this patch.
No shell generation in this patch.
No deck generation in this patch.

Basic lands are assumed available.
Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


DEFAULT_ROUGH_SHELL_SECTIONS: tuple[str, ...] = (
    "Commander Context",
    "Strategy Plan",
    "Core Role Buckets",
    "Owned Cards By Role",
    "Possible Rough Shell Sections",
    "Basic Land Access Policy",
    "Nonbasic Land Collection-First Policy",
    "Future Mana Base Plan",
    "Future Final Deck Draft",
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
        "Rough shell, not final deck. This output model does not select exact cards, "
        "make final deck inclusion decisions, generate role-count targets, generate a mana base, "
        "insert lands, complete a shell, generate a shell, or generate a deck."
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
    """Return human-readable rough-shell output model lines."""
    actual = model or create_rough_shell_output_model()
    lines = [
        actual.name,
        f"Build depth: {actual.build_depth_label}",
        "Rough shell, not final deck.",
        actual.basic_land_policy,
        actual.nonbasic_land_policy,
        "",
        "Rough shell sections:",
    ]
    for section in actual.sections:
        lines.append(f"- {section.name}")
    lines.extend([
        "",
        "Boundary:",
        "- No exact card selection in this patch.",
        "- No final deck inclusion decisions in this patch.",
        "- No role-count target generation in this patch.",
        "- No mana-base generation in this patch.",
        "- No land insertion in this patch.",
        "- No completed shell generation in this patch.",
        "- No shell generation in this patch.",
        "- No deck generation in this patch.",
    ])
    return lines


def rough_shell_handoff_prompt(model: RoughShellOutputModel | None = None) -> str:
    """Return AI handoff prompt text for the rough-shell output model."""
    actual = model or create_rough_shell_output_model()
    lines = [
        "AI Handoff Prompt - Rough Shell Output Model",
        "",
        "Use this as depth D setup context only.",
        "This is a rough shell model, not a final decklist and not a completed shell.",
        "Preserve the not-final boundary.",
        "Do not select exact cards yet unless a later patch explicitly allows it.",
        "Do not make final deck inclusion decisions.",
        "Do not generate role-count targets.",
        "Do not generate a mana base.",
        "Do not insert lands.",
        "Do not generate a completed shell.",
        "Do not generate a deck.",
        "",
        f"Build depth: {actual.build_depth_label}",
        actual.basic_land_policy,
        actual.nonbasic_land_policy,
        "",
        "Sections to preserve:",
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
