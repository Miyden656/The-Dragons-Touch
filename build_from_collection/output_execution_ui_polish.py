"""Build From Collection Execute Selected Report UI Polish.

v1.3.31 Build From Collection Execute Selected Report UI Polish.

This module provides display-only polish text for the guarded selected report
execution flow. It is intentionally a UI/readability helper only.

No writer execution in this patch.
No deck generation in this patch.
No exact card selection in this patch.
No final deck inclusion decisions in this patch.
No role-count target generation in this patch.
No mana-base generation in this patch.
No land insertion in this patch.
No completed shell generation in this patch.
No shell generation in this patch.
No full 100-card draft generation in this patch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_ROUTE_LABELS: dict[str, tuple[str, str]] = {
    "B": ("build_start_summary", "B - Build-Start Summary"),
    "C": ("owned_cards_by_role", "C - Owned Cards By Role"),
    "D": ("rough_shell", "D - Rough Shell"),
    "E": ("full_100_card_draft", "E - Full 100-Card Draft"),
}


@dataclass(frozen=True)
class BuildFromCollectionExecuteSelectedReportUIPolish:
    """Display-only UI polish for the selected report execution control."""

    selected_build_depth_key: str = "B"
    depth_key: str = "B"
    build_depth_key: str = "B"
    route_key: str = "build_start_summary"
    output_route: str = "build_start_summary"
    output_key: str = "build_start_summary"
    output_family: str = "build_start_summary"
    writer_key: str = "build_start_summary"
    selected_route_label: str = "B - Build-Start Summary"
    button_label: str = "Execute Selected Report Output"
    status_heading: str = "Selected Report Output Status"
    confirmation_required: bool = True
    requires_explicit_user_confirmation: bool = True
    ready_message: str = "Ready after explicit confirmation."
    output_target_hint: str = "Writes the selected Build From Collection report artifacts only."
    report_artifacts_only: bool = True
    writer_execution_allowed: bool = False
    executes_writer: bool = False
    generates_deck: bool = False
    generates_100_card_draft: bool = False
    generates_shell: bool = False
    generates_completed_shell: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_build_depth_key": self.selected_build_depth_key,
            "depth_key": self.depth_key,
            "build_depth_key": self.build_depth_key,
            "route_key": self.route_key,
            "output_route": self.output_route,
            "output_key": self.output_key,
            "output_family": self.output_family,
            "writer_key": self.writer_key,
            "selected_route_label": self.selected_route_label,
            "button_label": self.button_label,
            "status_heading": self.status_heading,
            "confirmation_required": self.confirmation_required,
            "requires_explicit_user_confirmation": self.requires_explicit_user_confirmation,
            "ready_message": self.ready_message,
            "output_target_hint": self.output_target_hint,
            "report_artifacts_only": self.report_artifacts_only,
            "writer_execution_allowed": self.writer_execution_allowed,
            "executes_writer": self.executes_writer,
            "generates_deck": self.generates_deck,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_shell": self.generates_shell,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
        }


def _normalize_depth_key(selected_build_depth_key: str | None) -> str:
    key = str(selected_build_depth_key or "B").strip().upper()[:1]
    return key if key in _ROUTE_LABELS else "B"


def create_build_from_collection_execute_selected_report_ui_polish(
    selected_build_depth_key: str | None = "B",
) -> BuildFromCollectionExecuteSelectedReportUIPolish:
    """Create display-only polish state for the selected report execution UI."""

    depth_key = _normalize_depth_key(selected_build_depth_key)
    route_key, route_label = _ROUTE_LABELS[depth_key]
    return BuildFromCollectionExecuteSelectedReportUIPolish(
        selected_build_depth_key=depth_key,
        depth_key=depth_key,
        build_depth_key=depth_key,
        route_key=route_key,
        output_route=route_key,
        output_key=route_key,
        output_family=route_key,
        writer_key=route_key,
        selected_route_label=route_label,
    )


def build_from_collection_execute_selected_report_ui_polish_lines(
    polish: BuildFromCollectionExecuteSelectedReportUIPolish,
) -> list[str]:
    """Human-readable UI polish lines for the selected report execution status."""

    return [
        "Execute Selected Report Output",
        f"Selected route: {polish.selected_route_label}",
        f"Output family: {polish.output_family}",
        "Confirmation required: Yes",
        "Action: Writes report artifacts only after explicit confirmation.",
        "Boundary: No writer execution in this display-only polish patch.",
        "Boundary: No deck generation.",
        "Boundary: No exact card selection, role-count generation, mana-base generation, land insertion, shell generation, or full 100-card draft generation.",
    ]
