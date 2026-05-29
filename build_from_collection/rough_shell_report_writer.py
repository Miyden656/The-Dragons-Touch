"""Rough Shell UI / Report Write Hook.

Writes the depth-D Rough Shell guidance output to disk: a human-readable
markdown guidance file, an AI handoff prompt, and a manifest.

The UI overwrites the human-readable file with the real strategy-driven
guidance markdown produced by build_rough_shell_markdown() in
rough_shell_guidance.py. This module supplies the surrounding folder,
handoff prompt, and manifest scaffolding.

Rough Shell is collection-scan guidance — "what to look for in your
collection for this commander + strategy" — not a generated deck. The
deck-generation feature lives at depth E (Full 100-Card Draft).

The dataclass boundary flags (generates_deck, generates_shell, etc.) remain
False because Rough Shell genuinely is guidance-only. Do not flip them
without auditing dev-mode contract callers.
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
        "# Rough Shell",
        "",
        f"Selected commander: {commander_name}",
        "",
    ]
    human_lines.extend(rough_shell_output_model_lines(model))
    human_lines.extend([
        "",
        "The UI overwrites this file with the real strategy-driven guidance markdown.",
        "If you are reading this scaffold text, the overwrite step did not run.",
    ])
    human_report = "\n".join(human_lines).rstrip() + "\n"

    ai_prompt = rough_shell_handoff_prompt(model)
    if "handoff" not in ai_prompt.lower():
        ai_prompt = "# AI Handoff Prompt - Rough Shell\n\n" + ai_prompt
    if "guidance" not in ai_prompt.lower():
        ai_prompt += "\n\nRough Shell is collection-scan guidance, not a generated decklist."
    if not ai_prompt.endswith("\n"):
        ai_prompt += "\n"

    manifest = {
        "output_type": "Rough Shell Guidance",
        "is_guidance_only": True,
        "is_generated_decklist": False,
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
        "Rough Shell guidance written.",
        "This is depth-D output: collection-scan guidance for the commander + strategy.",
        "Use the Full 100-Card Draft button to generate an actual decklist.",
        "",
        "Files written:",
        f"- Human-readable guidance: {data['human_report_path']}",
        f"- AI handoff prompt: {data['ai_handoff_prompt_path']}",
        f"- Manifest: {data['manifest_path']}",
    ]


__all__ = [
    "RoughShellWriteResult",
    "write_rough_shell_output",
    "rough_shell_write_result_lines",
]
