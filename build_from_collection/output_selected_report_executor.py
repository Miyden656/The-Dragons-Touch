"""Build From Collection Output Execute Selected Report Button.

v1.3.30.1 selected report executor syntax recovery hotfix.

This module performs guarded report artifact writing for the selected
Build From Collection output depth only. It does not perform deckbuilding.

No exact card selection in this patch.
No final deck inclusion decisions in this patch.
No role-count target generation in this patch.
No mana-base generation in this patch.
No land insertion in this patch.
No completed shell generation in this patch.
No shell generation in this patch.
No full 100-card draft generation in this patch.
No deck generation in this patch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class BuildFromCollectionSelectedReportExecutionResult:
    """Result of a guarded selected report output write."""

    selected_build_depth_key: str = "B"
    depth_key: str = "B"
    build_depth_key: str = "B"
    output_route: str = "build_start_summary"
    route_key: str = "build_start_summary"
    output_key: str = "build_start_summary"
    output_family: str = "build_start_summary"
    writer_key: str = "build_start_summary"
    user_confirmed_execution: bool = False
    requires_explicit_user_confirmation: bool = True
    execution_attempted: bool = False
    writer_executed: bool = False
    executes_writer: bool = False
    blocked_by_guard: bool = True
    success: bool = False
    output_directory: str = ""
    written_files: tuple[str, ...] = field(default_factory=tuple)
    message: str = "Execution blocked until explicit user confirmation."
    errors: tuple[str, ...] = field(default_factory=tuple)
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    generates_completed_shell: bool = False
    generates_shell: bool = False
    generates_100_card_draft: bool = False
    generates_deck: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_build_depth_key": self.selected_build_depth_key,
            "depth_key": self.depth_key,
            "build_depth_key": self.build_depth_key,
            "output_route": self.output_route,
            "route_key": self.route_key,
            "output_key": self.output_key,
            "output_family": self.output_family,
            "writer_key": self.writer_key,
            "user_confirmed_execution": self.user_confirmed_execution,
            "requires_explicit_user_confirmation": self.requires_explicit_user_confirmation,
            "execution_attempted": self.execution_attempted,
            "writer_executed": self.writer_executed,
            "executes_writer": self.executes_writer,
            "blocked_by_guard": self.blocked_by_guard,
            "success": self.success,
            "output_directory": self.output_directory,
            "written_files": list(self.written_files),
            "message": self.message,
            "errors": list(self.errors),
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


_ROUTE_BY_DEPTH = {
    "B": "build_start_summary",
    "C": "owned_cards_by_role",
    "D": "rough_shell",
    "E": "full_100_card_draft",
}


_DEPTH_LABELS = {
    "B": "B - Build-Start Summary",
    "C": "C - Owned Cards By Role",
    "D": "D - Rough Shell",
    "E": "E - Full 100-Card Draft",
}


def _normalize_depth_key(selected_build_depth_key: Any) -> str:
    key = str(selected_build_depth_key or "B").strip().upper()[:1]
    return key if key in _ROUTE_BY_DEPTH else "B"


def _route_for_depth(selected_build_depth_key: Any) -> str:
    return _ROUTE_BY_DEPTH[_normalize_depth_key(selected_build_depth_key)]


def _call_writer(writer: Callable[..., Any], output: Any, output_root: Path | None) -> Any:
    if output_root is None:
        return writer(output)
    try:
        return writer(output, output_root=output_root)
    except TypeError:
        try:
            return writer(output, output_dir=output_root)
        except TypeError:
            return writer(output, output_root)


def _written_files_from_result(result: Any) -> tuple[str, ...]:
    files = getattr(result, "written_files", None)
    if files is None:
        files = getattr(result, "files_written", None)
    if files is None:
        candidate_paths = [
            getattr(result, "human_report_path", None),
            getattr(result, "ai_handoff_prompt_path", None),
            getattr(result, "manifest_path", None),
        ]
        files = [str(path) for path in candidate_paths if path]
    return tuple(str(item) for item in (files or ()))


def _output_dir_from_result(result: Any) -> str:
    for attr in ("output_directory", "output_dir", "output_path"):
        value = getattr(result, attr, None)
        if value:
            return str(value)
    return ""


def execute_build_from_collection_selected_report(
    selected_build_depth_key: str = "B",
    output: Any | None = None,
    *,
    user_confirmed_execution: bool = False,
    output_root: str | Path | None = None,
) -> BuildFromCollectionSelectedReportExecutionResult:
    """Execute the selected report writer only after explicit confirmation."""

    depth_key = _normalize_depth_key(selected_build_depth_key)
    route = _route_for_depth(depth_key)

    if not user_confirmed_execution:
        return BuildFromCollectionSelectedReportExecutionResult(
            selected_build_depth_key=depth_key,
            depth_key=depth_key,
            build_depth_key=depth_key,
            output_route=route,
            route_key=route,
            output_key=route,
            output_family=route,
            writer_key=route,
            user_confirmed_execution=False,
            execution_attempted=False,
            writer_executed=False,
            executes_writer=False,
            blocked_by_guard=True,
            success=False,
            message="Execution blocked: explicit user confirmation is required before writing selected report artifacts.",
        )

    try:
        writer: Callable[..., Any]
        model_output: Any
        if route == "build_start_summary":
            from .build_start_report_writer import write_build_start_summary_output
            from .build_start_summary import create_build_start_summary_output

            writer = write_build_start_summary_output
            model_output = output if output is not None else create_build_start_summary_output()
        elif route == "owned_cards_by_role":
            from .owned_cards_by_role_report_writer import write_owned_cards_by_role_output
            from .owned_cards_by_role_output import create_owned_cards_by_role_output

            writer = write_owned_cards_by_role_output
            model_output = output if output is not None else create_owned_cards_by_role_output([])
        elif route == "rough_shell":
            from .rough_shell_report_writer import write_rough_shell_output
            from .rough_shell_output import create_rough_shell_output_model

            writer = write_rough_shell_output
            model_output = output if output is not None else create_rough_shell_output_model()
        else:
            from .full_100_card_draft_report_writer import write_full_100_card_draft_output
            from .full_100_card_draft_output import create_full_100_card_draft_output_model

            writer = write_full_100_card_draft_output
            model_output = output if output is not None else create_full_100_card_draft_output_model()

        write_result = _call_writer(writer, model_output, Path(output_root) if output_root is not None else None)
        return BuildFromCollectionSelectedReportExecutionResult(
            selected_build_depth_key=depth_key,
            depth_key=depth_key,
            build_depth_key=depth_key,
            output_route=route,
            route_key=route,
            output_key=route,
            output_family=route,
            writer_key=route,
            user_confirmed_execution=True,
            execution_attempted=True,
            writer_executed=True,
            executes_writer=True,
            blocked_by_guard=False,
            success=True,
            output_directory=_output_dir_from_result(write_result),
            written_files=_written_files_from_result(write_result),
            message=f"Selected report output written for {_DEPTH_LABELS[depth_key]}.",
        )
    except Exception as exc:  # pragma: no cover - surfaced through verifier/UI result text
        return BuildFromCollectionSelectedReportExecutionResult(
            selected_build_depth_key=depth_key,
            depth_key=depth_key,
            build_depth_key=depth_key,
            output_route=route,
            route_key=route,
            output_key=route,
            output_family=route,
            writer_key=route,
            user_confirmed_execution=True,
            execution_attempted=True,
            writer_executed=False,
            executes_writer=False,
            blocked_by_guard=False,
            success=False,
            message="Selected report output failed before completion.",
            errors=(str(exc),),
        )


def build_from_collection_selected_report_execution_lines(
    result: BuildFromCollectionSelectedReportExecutionResult,
) -> list[str]:
    """Return human-readable selected report execution status lines."""

    lines = [
        "Build From Collection - Execute Selected Report Output",
        f"Selected depth: {_DEPTH_LABELS.get(result.selected_build_depth_key, _DEPTH_LABELS['B'])}",
        f"Output route: {result.output_route}",
        f"Requires explicit user confirmation: {result.requires_explicit_user_confirmation}",
        f"Writer executed: {result.writer_executed}",
        f"Success: {result.success}",
        result.message,
        "Boundary: report artifacts only; no deck generation.",
        "Boundary: no exact card selection, no final deck inclusion decisions, no role-count generation, no mana-base generation, no land insertion, no shell generation, and no full 100-card draft generation.",
    ]
    if result.output_directory:
        lines.append(f"Output directory: {result.output_directory}")
    for file_name in result.written_files:
        lines.append(f"Written file: {file_name}")
    for error in result.errors:
        lines.append(f"Error: {error}")
    return lines
