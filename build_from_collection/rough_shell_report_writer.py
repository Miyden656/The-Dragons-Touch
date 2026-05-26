"""Rough Shell UI / Report Write Hook.

v1.3.23 writes depth-D Rough Shell output files.

This module writes a rough-shell model report and AI handoff prompt only.
It does not generate a completed shell or a deck.

No exact card selection in this patch.
No final deck inclusion decisions in this patch.
No role-count target generation in this patch.
No mana-base generation in this patch.
No land insertion in this patch.
No completed shell generation in this patch.
No shell generation in this patch.
No deck generation in this patch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .rough_shell_output import (
    RoughShellOutputModel,
    rough_shell_handoff_prompt,
    rough_shell_output_model_lines,
)


@dataclass(frozen=True)
class RoughShellWriteResult:
    """Result for writing depth-D rough-shell output files."""

    output_dir: str
    human_report_path: str
    ai_handoff_prompt_path: str
    manifest_path: str
    exact_card_selection: bool = False
    final_deck_inclusion_decisions: bool = False
    role_count_target_generation: bool = False
    mana_base_generation: bool = False
    land_insertion: bool = False
    completed_shell_generation: bool = False
    shell_generation: bool = False
    deck_generation: bool = False

    @property
    def selects_exact_cards(self) -> bool:
        return self.exact_card_selection

    @property
    def makes_final_deck_inclusion_decisions(self) -> bool:
        return self.final_deck_inclusion_decisions

    @property
    def generates_role_count_targets(self) -> bool:
        return self.role_count_target_generation

    @property
    def generates_mana_base(self) -> bool:
        return self.mana_base_generation

    @property
    def inserts_lands(self) -> bool:
        return self.land_insertion

    @property
    def generates_completed_shell(self) -> bool:
        return self.completed_shell_generation

    @property
    def generates_shell(self) -> bool:
        return self.shell_generation

    @property
    def generates_deck(self) -> bool:
        return self.deck_generation

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_dir": self.output_dir,
            "human_report_path": self.human_report_path,
            "ai_handoff_prompt_path": self.ai_handoff_prompt_path,
            "manifest_path": self.manifest_path,
            "exact_card_selection": self.exact_card_selection,
            "final_deck_inclusion_decisions": self.final_deck_inclusion_decisions,
            "role_count_target_generation": self.role_count_target_generation,
            "mana_base_generation": self.mana_base_generation,
            "land_insertion": self.land_insertion,
            "completed_shell_generation": self.completed_shell_generation,
            "shell_generation": self.shell_generation,
            "deck_generation": self.deck_generation,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_shell": self.generates_shell,
            "generates_deck": self.generates_deck,
        }


def _safe_slug(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(value).strip())
    return "_".join(part for part in safe.split("_") if part)[:80] or "selected_commander"


def _build_depth_label(model: RoughShellOutputModel) -> str:
    return str(getattr(model, "depth_label", None) or getattr(model, "build_depth_label", "D - Rough Shell"))


def write_rough_shell_output(
    model: RoughShellOutputModel,
    selected_commander: str = "Selected commander",
    output_root: str | Path = "Outputs",
) -> RoughShellWriteResult:
    """Write rough-shell report/prompt files only. No shell or deck generation."""

    commander_name = str(selected_commander or "Selected commander")
    out_dir = (
        Path(output_root)
        / "build_from_collection"
        / "rough_shell"
        / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_safe_slug(commander_name)}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    human_report_path = out_dir / "rough_shell.md"
    ai_handoff_prompt_path = out_dir / "ai_handoff_prompt.md"
    manifest_path = out_dir / "rough_shell_manifest.json"

    human_lines = [
        "# Rough Shell Output",
        "",
        f"Selected commander: {commander_name}",
        "",
    ]
    human_lines.extend(rough_shell_output_model_lines(model))
    human_lines.extend([
        "",
        "This is a rough shell model/report only, not a completed shell and not a final decklist.",
        "No deck generation occurred.",
    ])
    human_report = "\n".join(human_lines).rstrip() + "\n"

    ai_prompt = rough_shell_handoff_prompt(model)
    if "handoff" not in ai_prompt.lower():
        ai_prompt = "# AI Handoff Prompt - Rough Shell\n\n" + ai_prompt
    if "not a final decklist" not in ai_prompt.lower():
        ai_prompt += "\n\nPreserve this boundary: this is not a final decklist and not a completed shell."
    if not ai_prompt.endswith("\n"):
        ai_prompt += "\n"

    manifest = {
        "output_type": "Rough Shell Output",
        "selected_commander": commander_name,
        "build_depth": getattr(model, "depth_key", "D"),
        "build_depth_key": getattr(model, "build_depth_key", "D"),
        "depth_key": getattr(model, "depth_key", "D"),
        "build_depth_label": _build_depth_label(model),
        "depth_label": _build_depth_label(model),
        "human_report_path": str(human_report_path),
        "ai_handoff_prompt_path": str(ai_handoff_prompt_path),
        "manifest_path": str(manifest_path),
        "exact_card_selection": False,
        "final_deck_inclusion_decisions": False,
        "role_count_target_generation": False,
        "mana_base_generation": False,
        "land_insertion": False,
        "completed_shell_generation": False,
        "shell_generation": False,
        "deck_generation": False,
        "selects_exact_cards": False,
        "makes_final_deck_inclusion_decisions": False,
        "generates_role_count_targets": False,
        "generates_mana_base": False,
        "inserts_lands": False,
        "generates_completed_shell": False,
        "generates_shell": False,
        "generates_deck": False,
    }

    human_report_path.write_text(human_report, encoding="utf-8")
    ai_handoff_prompt_path.write_text(ai_prompt, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return RoughShellWriteResult(
        output_dir=str(out_dir),
        human_report_path=str(human_report_path),
        ai_handoff_prompt_path=str(ai_handoff_prompt_path),
        manifest_path=str(manifest_path),
    )


def rough_shell_write_result_lines(result: RoughShellWriteResult) -> list[str]:
    data = result.to_dict()
    return [
        "Rough Shell output written.",
        "This is depth-D output: rough shell report only, not a completed shell and not a final decklist.",
        "",
        "Files written:",
        f"- Human-readable report: {data['human_report_path']}",
        f"- AI handoff prompt: {data['ai_handoff_prompt_path']}",
        f"- Manifest: {data['manifest_path']}",
        "",
        "Boundary checks:",
        "- No exact card selection.",
        "- No final deck inclusion decisions.",
        "- No role-count target generation.",
        "- No mana-base generation.",
        "- No land insertion.",
        "- No completed shell generation.",
        "- No shell generation.",
        "- No deck generation.",
    ]


__all__ = [
    "RoughShellWriteResult",
    "write_rough_shell_output",
    "rough_shell_write_result_lines",
]
