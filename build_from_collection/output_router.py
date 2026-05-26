"""Build From Collection Output Selector / Routing.

v1.3.33.1 output router route alias lock candidate hotfix.

This module maps selected build depths B-E to report-output families.
It is selector/routing only and does not execute writers.

No writer execution in this patch.
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

from dataclasses import dataclass
from typing import Any


ROUTE_MAP: dict[str, tuple[str, str]] = {
    "B": ("build_start_summary", "B - Build-Start Summary"),
    "C": ("owned_cards_by_role", "C - Owned Cards By Role"),
    "D": ("rough_shell", "D - Rough Shell"),
    "E": ("full_100_card_draft", "E - Full 100-Card Draft"),
}


@dataclass(frozen=True)
class BuildFromCollectionOutputRoute:
    """Selected build-depth route for Build From Collection output."""

    selected_build_depth_key: str
    build_depth_key: str
    depth_key: str
    build_depth_label: str
    depth_label: str
    output_route: str
    route_key: str
    output_key: str
    output_family: str
    writer_key: str
    route_label: str
    selector_routing_only: bool = True
    executes_writer: bool = False
    writer_execution_allowed: bool = False
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
            "build_depth_key": self.build_depth_key,
            "depth_key": self.depth_key,
            "build_depth_label": self.build_depth_label,
            "depth_label": self.depth_label,
            "output_route": self.output_route,
            "route_key": self.route_key,
            "output_key": self.output_key,
            "output_family": self.output_family,
            "writer_key": self.writer_key,
            "route_label": self.route_label,
            "selector_routing_only": self.selector_routing_only,
            "executes_writer": self.executes_writer,
            "writer_execution_allowed": self.writer_execution_allowed,
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


def _normalize_depth_key(selected_build_depth_key: str | None) -> str:
    key = str(selected_build_depth_key or "B").strip().upper()[:1]
    return key if key in ROUTE_MAP else "B"


def create_build_from_collection_output_route(selected_build_depth_key: str | None = "B") -> BuildFromCollectionOutputRoute:
    key = _normalize_depth_key(selected_build_depth_key)
    route_key, label = ROUTE_MAP[key]
    return BuildFromCollectionOutputRoute(
        selected_build_depth_key=key,
        build_depth_key=key,
        depth_key=key,
        build_depth_label=label,
        depth_label=label,
        output_route=route_key,
        route_key=route_key,
        output_key=route_key,
        output_family=route_key,
        writer_key=route_key,
        route_label=label,
    )


def build_from_collection_output_routes() -> list[BuildFromCollectionOutputRoute]:
    return [create_build_from_collection_output_route(key) for key in ("B", "C", "D", "E")]


def build_from_collection_output_route_names() -> list[str]:
    return [route.build_depth_label for route in build_from_collection_output_routes()]


def build_from_collection_output_route_lines(route: BuildFromCollectionOutputRoute | None = None) -> list[str]:
    selected = route or create_build_from_collection_output_route("B")
    return [
        "Build From Collection Output Selector / Routing",
        f"Selected depth: {selected.build_depth_label}",
        f"Output route: {selected.output_route}",
        "Selector/routing only: no writer execution in this patch.",
        "No deck generation in this patch.",
    ]

