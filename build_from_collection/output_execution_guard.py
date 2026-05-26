"""Build From Collection Output Selector Execution Guard.

v1.3.28.4 route alias recovery hotfix.

This module sits between selected output routing and future writer execution.
It records the selected depth and output route, but it does not execute writers.

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


_ROUTE_BY_DEPTH: dict[str, tuple[str, str]] = {
    "B": ("build_start_summary", "B - Build-Start Summary"),
    "C": ("owned_cards_by_role", "C - Owned Cards By Role"),
    "D": ("rough_shell", "D - Rough Shell"),
    "E": ("full_100_card_draft", "E - Full 100-Card Draft"),
}


def _normalize_depth_key(value: Any) -> str:
    key = str(value or "B").strip().upper()[:1]
    return key if key in _ROUTE_BY_DEPTH else "B"


@dataclass(frozen=True)
class BuildFromCollectionOutputExecutionGuard:
    """Guard-only routing protection before future Build From Collection writer execution."""

    selected_build_depth_key: str
    output_route: str
    build_depth_label: str
    requires_explicit_user_confirmation: bool = True
    writer_execution_allowed: bool = False

    # v1.3.28.3 executes_writer compatibility alias
    executes_writer: bool = False

    # v1.3.28.4 route alias recovery fields
    route_key: str = ""
    output_key: str = ""
    output_family: str = ""
    writer_key: str = ""

    # safety boundaries
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    generates_completed_shell: bool = False
    generates_shell: bool = False
    generates_100_card_draft: bool = False
    generates_deck: bool = False

    @property
    def depth_key(self) -> str:
        return self.selected_build_depth_key

    @property
    def build_depth_key(self) -> str:
        return self.selected_build_depth_key

    @property
    def depth_label(self) -> str:
        return self.build_depth_label

    def to_dict(self) -> dict[str, Any]:
        route = self.output_route
        return {
            "selected_build_depth_key": self.selected_build_depth_key,
            "depth_key": self.depth_key,
            "build_depth_key": self.build_depth_key,
            "build_depth_label": self.build_depth_label,
            "depth_label": self.depth_label,
            "output_route": route,
            "route_key": self.route_key or route,
            "output_key": self.output_key or route,
            "output_family": self.output_family or route,
            "writer_key": self.writer_key or route,
            "requires_explicit_user_confirmation": self.requires_explicit_user_confirmation,
            "writer_execution_allowed": self.writer_execution_allowed,
            "executes_writer": self.executes_writer,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_shell": self.generates_shell,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_deck": self.generates_deck,
            "guard_only": True,
            "no_writer_execution_in_this_patch": True,
            "no_deck_generation_in_this_patch": True,
        }


def create_build_from_collection_output_execution_guard(
    selected_build_depth_key: str = "B",
    *,
    user_confirmed: bool = False,
    allow_writer_execution: bool = False,
) -> BuildFromCollectionOutputExecutionGuard:
    """Create a guard for the selected B-E output route without executing writers."""

    depth_key = _normalize_depth_key(selected_build_depth_key)
    route, label = _ROUTE_BY_DEPTH[depth_key]

    # The v1.3.28 guard is intentionally conservative: even if callers pass
    # confirmation flags, this patch records the route only and does not execute.
    writer_execution_allowed = bool(user_confirmed and allow_writer_execution and False)

    return BuildFromCollectionOutputExecutionGuard(
        selected_build_depth_key=depth_key,
        output_route=route,
        route_key=route,
        output_key=route,
        output_family=route,
        writer_key=route,
        build_depth_label=label,
        requires_explicit_user_confirmation=True,
        writer_execution_allowed=writer_execution_allowed,
        executes_writer=False,
    )


def build_from_collection_output_execution_allowed(
    selected_build_depth_key: str = "B",
    *,
    user_confirmed: bool = False,
    allow_writer_execution: bool = False,
) -> bool:
    """Return whether writer execution is allowed. v1.3.28 guard defaults to False."""

    guard = create_build_from_collection_output_execution_guard(
        selected_build_depth_key,
        user_confirmed=user_confirmed,
        allow_writer_execution=allow_writer_execution,
    )
    return bool(guard.writer_execution_allowed)


def build_from_collection_output_execution_guard_lines(
    guard: BuildFromCollectionOutputExecutionGuard | None = None,
    *,
    selected_build_depth_key: str = "B",
) -> list[str]:
    """Return player-readable guard preview lines."""

    guard = guard or create_build_from_collection_output_execution_guard(selected_build_depth_key)
    return [
        "Build From Collection Output Execution Guard",
        f"Selected depth: {guard.selected_build_depth_key}",
        f"Build depth: {guard.build_depth_label}",
        f"Output route: {guard.output_route}",
        "Writer execution allowed: No",
        "Requires explicit user confirmation: Yes",
        "No writer execution in this patch.",
        "No deck generation in this patch.",
    ]


__all__ = [
    "BuildFromCollectionOutputExecutionGuard",
    "create_build_from_collection_output_execution_guard",
    "build_from_collection_output_execution_allowed",
    "build_from_collection_output_execution_guard_lines",
]
