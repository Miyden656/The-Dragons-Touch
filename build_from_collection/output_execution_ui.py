"""Build From Collection Output Execution UI Hook.

v1.3.29 Build From Collection Output Execution UI Hook.

This module creates a display-only UI preview for the selected Build From
Collection output execution guard.

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

from .output_execution_guard import (
    BuildFromCollectionOutputExecutionGuard,
    create_build_from_collection_output_execution_guard,
)


@dataclass(frozen=True)
class BuildFromCollectionOutputExecutionUIPreview:
    """Display-only preview of the selected output execution guard."""

    selected_build_depth_key: str
    build_depth_key: str
    depth_key: str
    route_key: str
    output_route: str
    output_family: str
    writer_key: str
    requires_explicit_user_confirmation: bool
    writer_execution_allowed: bool
    executes_writer: bool
    selector_ui_hook_only: bool
    generates_deck: bool
    generates_100_card_draft: bool
    generates_shell: bool
    generates_completed_shell: bool
    generates_mana_base: bool
    inserts_lands: bool
    selects_exact_cards: bool
    makes_final_deck_inclusion_decisions: bool
    generates_role_count_targets: bool
    status_label: str
    user_message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_build_depth_key": self.selected_build_depth_key,
            "build_depth_key": self.build_depth_key,
            "depth_key": self.depth_key,
            "route_key": self.route_key,
            "output_route": self.output_route,
            "output_family": self.output_family,
            "writer_key": self.writer_key,
            "requires_explicit_user_confirmation": self.requires_explicit_user_confirmation,
            "writer_execution_allowed": self.writer_execution_allowed,
            "executes_writer": self.executes_writer,
            "selector_ui_hook_only": self.selector_ui_hook_only,
            "generates_deck": self.generates_deck,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_shell": self.generates_shell,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "status_label": self.status_label,
            "user_message": self.user_message,
        }


def _value_from_guard(guard: BuildFromCollectionOutputExecutionGuard, name: str, default: Any = None) -> Any:
    return getattr(guard, name, default)



# v1.3.29.1 guard signature compatibility hotfix
def _create_output_execution_guard_compat(selected_build_depth_key: str, user_confirmed_execution: bool = False):
    """Create an output execution guard while tolerating older/newer guard helper signatures."""
    try:
        return create_build_from_collection_output_execution_guard(
            selected_build_depth_key,
            user_confirmed_execution=user_confirmed_execution,
        )
    except TypeError:
        guard = create_build_from_collection_output_execution_guard(selected_build_depth_key)
        if hasattr(guard, "user_confirmed_execution"):
            try:
                setattr(guard, "user_confirmed_execution", bool(user_confirmed_execution))
            except Exception:
                pass
        return guard

def create_build_from_collection_output_execution_ui_preview(
    selected_build_depth_key: str = "B",
    *,
    user_confirmed_execution: bool = False,
) -> BuildFromCollectionOutputExecutionUIPreview:
    """Create a display-only execution-guard UI preview.

    The preview may show whether a future writer would be guarded, but this
    helper does not execute a writer.
    """

    guard = _create_output_execution_guard_compat(
        selected_build_depth_key,
        user_confirmed_execution=user_confirmed_execution,
    )

    route = _value_from_guard(guard, "route_key", _value_from_guard(guard, "output_route", "build_start_summary"))
    selected_depth = _value_from_guard(guard, "selected_build_depth_key", selected_build_depth_key)
    writer_allowed = bool(_value_from_guard(guard, "writer_execution_allowed", False))
    confirmed_required = bool(_value_from_guard(guard, "requires_explicit_user_confirmation", True))

    if writer_allowed:
        status_label = "Execution allowed after explicit user confirmation"
        user_message = "The selected output route is confirmed, but this UI hook still does not execute writers by itself."
    else:
        status_label = "Execution guarded"
        user_message = "This route requires explicit user confirmation before a future writer may run."

    return BuildFromCollectionOutputExecutionUIPreview(
        selected_build_depth_key=str(selected_depth),
        build_depth_key=str(_value_from_guard(guard, "build_depth_key", selected_depth)),
        depth_key=str(_value_from_guard(guard, "depth_key", selected_depth)),
        route_key=str(route),
        output_route=str(_value_from_guard(guard, "output_route", route)),
        output_family=str(_value_from_guard(guard, "output_family", route)),
        writer_key=str(_value_from_guard(guard, "writer_key", route)),
        requires_explicit_user_confirmation=confirmed_required,
        writer_execution_allowed=writer_allowed,
        executes_writer=bool(_value_from_guard(guard, "executes_writer", False)),
        selector_ui_hook_only=True,
        generates_deck=bool(_value_from_guard(guard, "generates_deck", False)),
        generates_100_card_draft=bool(_value_from_guard(guard, "generates_100_card_draft", False)),
        generates_shell=bool(_value_from_guard(guard, "generates_shell", False)),
        generates_completed_shell=bool(_value_from_guard(guard, "generates_completed_shell", False)),
        generates_mana_base=bool(_value_from_guard(guard, "generates_mana_base", False)),
        inserts_lands=bool(_value_from_guard(guard, "inserts_lands", False)),
        selects_exact_cards=bool(_value_from_guard(guard, "selects_exact_cards", False)),
        makes_final_deck_inclusion_decisions=bool(_value_from_guard(guard, "makes_final_deck_inclusion_decisions", False)),
        generates_role_count_targets=bool(_value_from_guard(guard, "generates_role_count_targets", False)),
        status_label=status_label,
        user_message=user_message,
    )


def build_from_collection_output_execution_ui_preview_lines(
    preview: BuildFromCollectionOutputExecutionUIPreview,
) -> list[str]:
    """Return player-facing lines for the execution guard UI hook."""

    return [
        "Build From Collection Output Execution Guard",
        f"Selected depth: {preview.selected_build_depth_key}",
        f"Selected route: {preview.route_key}",
        f"Status: {preview.status_label}",
        preview.user_message,
        "Requires explicit user confirmation before writer execution: "
        f"{preview.requires_explicit_user_confirmation}",
        "Writer execution allowed right now: "
        f"{preview.writer_execution_allowed}",
        "No writer execution in this patch.",
        "No deck generation in this patch.",
    ]
