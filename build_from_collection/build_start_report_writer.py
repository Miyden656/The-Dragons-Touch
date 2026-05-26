"""
Build-Start Summary UI / Report Write Hook — v1.3.19

This module writes the v1.3.18 Build-Start Summary Output to disk from
Commander’s Call.

Outputs:
- human-readable Build From Collection report markdown
- AI handoff prompt markdown
- small manifest payload

Boundaries:
- No exact card selection in this patch
- No role-count target generation in this patch
- No mana-base generation in this patch
- No land insertion in this patch
- No shell generation in this patch
- No deck generation in this patch
- No 100-card shell generation in this patch

Land policy:
- Basic lands are assumed available
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any


BUILD_START_SUMMARY_REPORT_WRITER_NAME = "Build-Start Summary UI / Report Write Hook"
HUMAN_REPORT_FILENAME = "build_start_summary.md"
AI_HANDOFF_FILENAME = "ai_handoff_prompt.md"
MANIFEST_FILENAME = "build_start_summary_manifest.json"


def _payload_from_output(output: Any) -> dict[str, Any]:
    if output is None:
        return {}
    if isinstance(output, dict):
        return dict(output)
    if hasattr(output, "to_dict"):
        try:
            payload = output.to_dict()
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
    return {}


def _slugify(value: str, fallback: str = "build_start_summary") -> str:
    text = str(value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


def _timestamp_label(timestamp: str | None = None) -> str:
    if timestamp:
        return _slugify(timestamp, fallback="manual_timestamp")
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass(frozen=True)
class BuildStartSummaryWriteResult:
    """Result of writing a build-start summary report and AI handoff prompt."""

    name: str = BUILD_START_SUMMARY_REPORT_WRITER_NAME
    patch_version: str = "v1.3.19"
    output_folder: str = ""
    human_report_path: str = ""
    ai_handoff_prompt_path: str = ""
    manifest_path: str = ""
    human_report_written: bool = False
    ai_handoff_prompt_written: bool = False
    manifest_written: bool = False
    exact_card_selection_performed: bool = False
    role_count_targets_generated: bool = False
    mana_base_generated: bool = False
    lands_inserted: bool = False
    shell_generated: bool = False
    deck_generated: bool = False
    # v1.3.19.3 explicit output boundary aliases for verifier/UI clarity.
    generates_mana_base: bool = False
    inserts_lands: bool = False
    generates_shell: bool = False
    generates_deck: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "patch_version": self.patch_version,
            "output_folder": self.output_folder,
            "human_report_path": self.human_report_path,
            "ai_handoff_prompt_path": self.ai_handoff_prompt_path,
            "manifest_path": self.manifest_path,
            "human_report_written": self.human_report_written,
            "ai_handoff_prompt_written": self.ai_handoff_prompt_written,
            "manifest_written": self.manifest_written,
            "exact_card_selection_performed": self.exact_card_selection_performed,
            "role_count_targets_generated": self.role_count_targets_generated,
            "mana_base_generated": self.mana_base_generated,
            "lands_inserted": self.lands_inserted,
            "shell_generated": self.shell_generated,
            "deck_generated": self.deck_generated,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "generates_shell": self.generates_shell,
            "generates_deck": self.generates_deck,
        }


def default_build_start_summary_output_root(output_root: str | Path | None = None) -> Path:
    """Resolve the parent folder for Build From Collection build-start outputs."""

    root = Path(output_root) if output_root else Path("Outputs")
    return root / "build_from_collection" / "build_start_summary"


def write_build_start_summary_output(
    output: Any,
    *,
    output_root: str | Path | None = None,
    run_label: str | None = None,
    timestamp: str | None = None,
) -> BuildStartSummaryWriteResult:
    """Write the depth-B build-start summary output to markdown files.

    This function writes text that was already created by v1.3.18. It does not
    select cards, create role targets, generate a mana base, insert lands,
    generate a shell, or generate a deck.
    """

    payload = _payload_from_output(output)
    commander_name = payload.get("selected_commander_name") or payload.get("commander_name") or "selected_commander"
    folder_label = run_label or f"{_timestamp_label(timestamp)}_{_slugify(str(commander_name), fallback='selected_commander')}"
    output_folder = default_build_start_summary_output_root(output_root) / _slugify(folder_label, fallback="build_start_summary")
    output_folder.mkdir(parents=True, exist_ok=True)

    human_report = payload.get("human_report_markdown") or "# Build From Collection — Build-Start Summary\n\nNo human-readable report text was provided."
    ai_prompt = payload.get("ai_handoff_prompt") or "# AI Handoff Prompt\n\nNo AI handoff prompt text was provided."
    # v1.3.19.3 handoff wording guard: make the written prompt unmistakably an AI handoff.
    if "handoff" not in str(ai_prompt).lower():
        ai_prompt = "# AI Handoff Prompt\n\nThis AI handoff prompt is generated from the Build From Collection build-start summary.\n\n" + str(ai_prompt).lstrip()

    human_path = output_folder / HUMAN_REPORT_FILENAME
    ai_path = output_folder / AI_HANDOFF_FILENAME
    manifest_path = output_folder / MANIFEST_FILENAME

    human_path.write_text(str(human_report).rstrip() + "\n", encoding="utf-8", newline="\n")
    ai_path.write_text(str(ai_prompt).rstrip() + "\n", encoding="utf-8", newline="\n")

    manifest = {
        "patch_version": "v1.3.19",
        "output_type": "Build-Start Summary Output",
        "human_report_path": str(human_path),
        "ai_handoff_prompt_path": str(ai_path),
        "selected_commander_name": payload.get("selected_commander_name"),
        "output_depth_key": payload.get("output_depth_key"),
        "output_depth_label": payload.get("output_depth_label"),
        "basic_land_policy": payload.get("basic_land_policy"),
        "nonbasic_land_policy": payload.get("nonbasic_land_policy"),
        "exact_card_selection_performed": False,
        "role_count_targets_generated": False,
        "mana_base_generated": False,
        "lands_inserted": False,
        "shell_generated": False,
        "deck_generated": False,
        "generates_mana_base": False,
        "inserts_lands": False,
        "generates_shell": False,
        "generates_deck": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8", newline="\n")

    return BuildStartSummaryWriteResult(
        output_folder=str(output_folder),
        human_report_path=str(human_path),
        ai_handoff_prompt_path=str(ai_path),
        manifest_path=str(manifest_path),
        human_report_written=human_path.exists(),
        ai_handoff_prompt_written=ai_path.exists(),
        manifest_written=manifest_path.exists(),
        # v1.3.19.3 boundary aliases: all remain False because this writes depth-B output only.
        generates_mana_base=False,
        inserts_lands=False,
        generates_shell=False,
        generates_deck=False,
    )


def build_start_summary_write_result_lines(result: BuildStartSummaryWriteResult) -> tuple[str, ...]:
    """Return user-facing lines for the UI report write hook."""

    return (
        "Build-Start Summary report files written.",
        f"Output folder: {result.output_folder}",
        f"Human-readable report: {result.human_report_path}",
        f"AI handoff prompt: {result.ai_handoff_prompt_path}",
        f"Manifest: {result.manifest_path}",
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell generation.",
        "No deck generation.",
    )
