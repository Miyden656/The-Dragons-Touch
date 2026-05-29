"""Owned Cards By Role UI / Report Write Hook.

Writes the depth-C Owned Cards By Role output to disk: a human-readable
markdown report grouping the user's owned cards into 11 role buckets,
an AI handoff prompt, and a manifest.

This is a role-bucketing summary — it tells the user which owned cards
could fill which roles. It is not a generated deck. The deck-generation
feature lives at depth E (Full 100-Card Draft).

The dataclass boundary flags (deck_generation, shell_generation, etc.) remain
False because role bucketing is intentionally not deck selection. Do not
flip them without auditing dev-mode contract callers.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any
from .owned_cards_by_role_output import OwnedCardsByRoleOutput, owned_cards_by_role_handoff_prompt, owned_cards_by_role_output_lines

@dataclass(frozen=True)
class OwnedCardsByRoleWriteResult:
    """Result for writing depth-C owned-cards-by-role output files."""
    output_dir: str
    human_report_path: str
    ai_handoff_prompt_path: str
    manifest_path: str
    exact_card_selection: bool = False
    final_deck_inclusion_decisions: bool = False
    role_count_target_generation: bool = False
    mana_base_generation: bool = False
    land_insertion: bool = False
    shell_generation: bool = False
    deck_generation: bool = False
    @property
    def generates_deck(self) -> bool: return self.deck_generation
    @property
    def generates_shell(self) -> bool: return self.shell_generation
    @property
    def generates_mana_base(self) -> bool: return self.mana_base_generation
    @property
    def inserts_lands(self) -> bool: return self.land_insertion
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
            "shell_generation": self.shell_generation,
            "deck_generation": self.deck_generation,
            "generates_deck": self.generates_deck,
            "generates_shell": self.generates_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
        }

def _safe_slug(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(value).strip())
    return "_".join(part for part in safe.split("_") if part)[:80] or "selected_commander"

def write_owned_cards_by_role_output(output: OwnedCardsByRoleOutput, output_root: str | Path = "Outputs") -> OwnedCardsByRoleWriteResult:
    """Write report/prompt files only. No deck generation."""
    out_dir = Path(output_root) / "build_from_collection" / "owned_cards_by_role" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_safe_slug(output.selected_commander)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    human_report_path = out_dir / "owned_cards_by_role.md"
    ai_handoff_prompt_path = out_dir / "ai_handoff_prompt.md"
    manifest_path = out_dir / "owned_cards_by_role_manifest.json"
    human_report = "\n".join(owned_cards_by_role_output_lines(output)) + "\n"
    ai_prompt = owned_cards_by_role_handoff_prompt(output)
    if "handoff" not in ai_prompt.lower():
        ai_prompt = "# AI Handoff Prompt - Owned Cards By Role\n\n" + ai_prompt
    if not ai_prompt.endswith("\n"):
        ai_prompt += "\n"
    manifest = {
        "output_type": "Owned Cards By Role",
        "is_role_bucketing_summary": True,
        "is_generated_decklist": False,
        "build_depth": getattr(output, "depth_key", getattr(output, "build_depth_key", "C")),
        # v1.3.21.7 writer depth label compatibility guard
        "build_depth_label": getattr(output, "depth_label", getattr(output, "build_depth_label", "C - Owned Cards By Role")),
        "selected_commander": output.selected_commander,
        "human_report_path": str(human_report_path),
        "ai_handoff_prompt_path": str(ai_handoff_prompt_path),
        "manifest_path": str(manifest_path),
        "exact_card_selection": False,
        "final_deck_inclusion_decisions": False,
        "role_count_target_generation": False,
        "mana_base_generation": False,
        "land_insertion": False,
        "shell_generation": False,
        "deck_generation": False,
        "generates_deck": False,
        "generates_shell": False,
        "generates_mana_base": False,
        "inserts_lands": False,
    }
    human_report_path.write_text(human_report, encoding="utf-8")
    ai_handoff_prompt_path.write_text(ai_prompt, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return OwnedCardsByRoleWriteResult(str(out_dir), str(human_report_path), str(ai_handoff_prompt_path), str(manifest_path))

def owned_cards_by_role_write_result_lines(result: OwnedCardsByRoleWriteResult) -> list[str]:
    data = result.to_dict()
    return [
        "Owned Cards By Role report written.",
        "This is depth-C output: the user's owned cards grouped into 11 possible role buckets.",
        "Use the Full 100-Card Draft button to generate an actual decklist.",
        "",
        "Files written:",
        f"- Human-readable report: {data['human_report_path']}",
        f"- AI handoff prompt: {data['ai_handoff_prompt_path']}",
        f"- Manifest: {data['manifest_path']}",
    ]
