"""Full 100-Card Draft UI / Report Write Hook.

Writes the depth-E Full 100-Card Draft output to disk: a human-readable
markdown report, an AI handoff prompt, and a manifest.

The UI overwrites the human-readable report file with the real decklist
markdown produced by render_full_100_card_draft_markdown() in
full_100_card_draft_builder. This module supplies the surrounding folder,
handoff prompt, and manifest scaffolding.

The dataclass boundary flags (full_100_card_draft_generation, deck_generation,
etc.) remain False because this writer itself does not generate cards — the
builder does. Do not flip them without auditing dev-mode contract callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .full_100_card_draft_output import (
    Full100CardDraftOutputModel,
    full_100_card_draft_handoff_prompt,
    full_100_card_draft_output_model_lines,
)


@dataclass(frozen=True)
class Full100CardDraftWriteResult:
    """Result for writing depth-E full 100-card draft model output files."""

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
    full_100_card_draft_generation: bool = False
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
    def generates_100_card_draft(self) -> bool:
        return self.full_100_card_draft_generation

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
            "full_100_card_draft_generation": self.full_100_card_draft_generation,
            "deck_generation": self.deck_generation,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_shell": self.generates_shell,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_deck": self.generates_deck,
        }


def _safe_slug(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(value).strip())
    return "_".join(part for part in safe.split("_") if part)[:80] or "selected_commander"


def _build_depth_label(model: Full100CardDraftOutputModel) -> str:
    return str(getattr(model, "depth_label", None) or getattr(model, "build_depth_label", "E - Full 100-Card Draft"))


def write_full_100_card_draft_output(
    model: Full100CardDraftOutputModel,
    selected_commander: str = "Selected commander",
    output_root: str | Path = "Outputs",
) -> Full100CardDraftWriteResult:
    """Write full-draft model report/prompt files only. No deck generation."""

    commander_name = str(selected_commander or "Selected commander")
    out_dir = (
        Path(output_root)
        / "build_from_collection"
        / "full_100_card_draft"
        / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_safe_slug(commander_name)}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    human_report_path = out_dir / "full_100_card_draft.md"
    ai_handoff_prompt_path = out_dir / "ai_handoff_prompt.md"
    manifest_path = out_dir / "full_100_card_draft_manifest.json"

    human_lines = ["# Full 100-Card Draft", "", f"Selected commander: {commander_name}", ""]
    human_lines.extend(full_100_card_draft_output_model_lines(model))
    human_lines.extend([
        "",
        "The UI overwrites this file with the real generated decklist markdown.",
        "If you are reading this scaffold text, the overwrite step did not run.",
    ])
    human_report = "\n".join(human_lines).rstrip() + "\n"

    ai_prompt = full_100_card_draft_handoff_prompt(model)
    if "handoff" not in ai_prompt.lower():
        ai_prompt = "# AI Handoff Prompt - Full 100-Card Draft\n\n" + ai_prompt
    if "starting point" not in ai_prompt.lower() and "starting draft" not in ai_prompt.lower():
        ai_prompt += "\n\nPreserve this boundary: the draft is a starting point, not the user's final committed decklist."
    if not ai_prompt.endswith("\n"):
        ai_prompt += "\n"

    manifest = {
        "output_type": "Full 100-Card Draft",
        "selected_commander": commander_name,
        "build_depth": getattr(model, "depth_key", "E"),
        "build_depth_key": getattr(model, "build_depth_key", "E"),
        "depth_key": getattr(model, "depth_key", "E"),
        "build_depth_label": _build_depth_label(model),
        "depth_label": _build_depth_label(model),
        "human_report_path": str(human_report_path),
        "ai_handoff_prompt_path": str(ai_handoff_prompt_path),
        "manifest_path": str(manifest_path),
        "is_starting_draft": True,
        "is_final_decklist": False,
        "exact_card_selection": True,
        "final_deck_inclusion_decisions": True,
        "role_count_target_generation": True,
        "mana_base_generation": True,
        "land_insertion": True,
        "completed_shell_generation": True,
        "shell_generation": True,
        "full_100_card_draft_generation": True,
        "deck_generation": True,
        "selects_exact_cards": True,
        "makes_final_deck_inclusion_decisions": True,
        "generates_role_count_targets": True,
        "generates_mana_base": True,
        "inserts_lands": True,
        "generates_completed_shell": True,
        "generates_shell": True,
        "generates_100_card_draft": True,
        "generates_deck": True,
    }

    human_report_path.write_text(human_report, encoding="utf-8")
    ai_handoff_prompt_path.write_text(ai_prompt, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return Full100CardDraftWriteResult(str(out_dir), str(human_report_path), str(ai_handoff_prompt_path), str(manifest_path))


def full_100_card_draft_write_result_lines(result: Full100CardDraftWriteResult) -> list[str]:
    data = result.to_dict()
    return [
        "Full 100-Card Draft written.",
        "This is depth-E output: a heuristically generated 100-card draft from the user's collection.",
        "Treat as a starting point, not a final committed decklist.",
        "",
        "Files written:",
        f"- Human-readable report (real decklist): {data['human_report_path']}",
        f"- AI handoff prompt: {data['ai_handoff_prompt_path']}",
        f"- Manifest: {data['manifest_path']}",
    ]


__all__ = ["Full100CardDraftWriteResult", "write_full_100_card_draft_output", "full_100_card_draft_write_result_lines"]
