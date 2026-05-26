"""Build From Collection Output Selector UI.

v1.3.27.2 output selector UI route alias hotfix.

This module previews the selected Build From Collection output route for
The Commander's Call. It is selector UI only.

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

try:
    from .output_router import create_build_from_collection_output_route
except Exception:  # pragma: no cover - defensive fallback for isolated imports
    create_build_from_collection_output_route = None


_ROUTE_FALLBACKS: dict[str, dict[str, str]] = {
    "B": {
        "label": "B - Build-Start Summary",
        "route_key": "build_start_summary",
        "writer_key": "build_start_summary",
        "description": "Write the depth-B build-start summary report and AI handoff prompt.",
    },
    "C": {
        "label": "C - Owned Cards By Role",
        "route_key": "owned_cards_by_role",
        "writer_key": "owned_cards_by_role",
        "description": "Write the depth-C owned-cards-by-role report and AI handoff prompt.",
    },
    "D": {
        "label": "D - Rough Shell",
        "route_key": "rough_shell",
        "writer_key": "rough_shell",
        "description": "Write the depth-D rough-shell model report and AI handoff prompt.",
    },
    "E": {
        "label": "E - Full 100-Card Draft",
        "route_key": "full_100_card_draft",
        "writer_key": "full_100_card_draft",
        "description": "Write the depth-E full 100-card draft model report and AI handoff prompt.",
    },
}


def _normalize_depth_key(value: Any) -> str:
    raw = str(value or "B").strip().upper()
    if raw.startswith("B"):
        return "B"
    if raw.startswith("C"):
        return "C"
    if raw.startswith("D"):
        return "D"
    if raw.startswith("E"):
        return "E"
    return "B"


def _route_payload(depth_key: str) -> dict[str, Any]:
    depth_key = _normalize_depth_key(depth_key)
    fallback = dict(_ROUTE_FALLBACKS[depth_key])

    if create_build_from_collection_output_route is None:
        return fallback

    try:
        route = create_build_from_collection_output_route(depth_key)
    except Exception:
        return fallback

    data: dict[str, Any] = {}
    if hasattr(route, "to_dict"):
        try:
            data.update(route.to_dict())
        except Exception:
            pass

    for name in (
        "route_key",
        "output_route",
        "output_key",
        "output_family",
        "writer_key",
        "build_depth_label",
        "depth_label",
        "selected_build_depth_key",
        "build_depth_key",
        "depth_key",
        "label",
        "description",
    ):
        if hasattr(route, name):
            data[name] = getattr(route, name)

    # Route modules have used a few different names during v1.3. Preserve all
    # useful aliases so UI/verifiers can agree on the selected route.
    route_key = (
        data.get("route_key")
        or data.get("output_route")
        or data.get("output_key")
        or data.get("output_family")
        or fallback["route_key"]
    )
    writer_key = data.get("writer_key") or route_key
    label = data.get("build_depth_label") or data.get("depth_label") or data.get("label") or fallback["label"]

    return {
        **fallback,
        **data,
        "route_key": str(route_key),
        "output_route": str(route_key),
        "output_key": str(route_key),
        "output_family": str(route_key),
        "writer_key": str(writer_key),
        "build_depth_label": str(label),
        "depth_label": str(label),
        "label": str(label),
    }


@dataclass(frozen=True)
class BuildFromCollectionOutputSelectorUIPreview:
    """Selector UI preview only; no writer execution and no deck generation."""

    selected_build_depth_key: str = "B"
    build_depth_key: str = "B"
    depth_key: str = "B"
    build_depth_label: str = "B - Build-Start Summary"
    depth_label: str = "B - Build-Start Summary"

    route_key: str = "build_start_summary"
    output_route: str = "build_start_summary"
    output_key: str = "build_start_summary"
    output_family: str = "build_start_summary"
    writer_key: str = "build_start_summary"

    description: str = "Write the depth-B build-start summary report and AI handoff prompt."

    selector_ui_only: bool = True
    selector_routing_only: bool = True
    executes_writer: bool = False
    executes_writers: bool = False
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
            "route_key": self.route_key,
            "output_route": self.output_route,
            "output_key": self.output_key,
            "output_family": self.output_family,
            "writer_key": self.writer_key,
            "description": self.description,
            "selector_ui_only": self.selector_ui_only,
            "selector_routing_only": self.selector_routing_only,
            "executes_writer": self.executes_writer,
            "executes_writers": self.executes_writers,
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


def create_build_from_collection_output_selector_ui_preview(
    selected_build_depth_key: str | None = None,
    *,
    build_depth_key: str | None = None,
    depth_key: str | None = None,
    selected_depth_key: str | None = None,
    **_: Any,
) -> BuildFromCollectionOutputSelectorUIPreview:
    """Create a selector UI preview for B-E output routing.

    This function intentionally previews the route only. It does not execute
    any report writer.
    """

    normalized = _normalize_depth_key(
        selected_build_depth_key or build_depth_key or depth_key or selected_depth_key or "B"
    )
    payload = _route_payload(normalized)

    label = str(payload.get("build_depth_label") or payload.get("depth_label") or _ROUTE_FALLBACKS[normalized]["label"])
    route_key = str(
        payload.get("route_key")
        or payload.get("output_route")
        or payload.get("output_key")
        or payload.get("output_family")
        or _ROUTE_FALLBACKS[normalized]["route_key"]
    )
    writer_key = str(payload.get("writer_key") or route_key)

    return BuildFromCollectionOutputSelectorUIPreview(
        selected_build_depth_key=normalized,
        build_depth_key=normalized,
        depth_key=normalized,
        build_depth_label=label,
        depth_label=label,
        route_key=route_key,
        output_route=route_key,
        output_key=route_key,
        output_family=route_key,
        writer_key=writer_key,
        description=str(payload.get("description") or _ROUTE_FALLBACKS[normalized]["description"]),
    )


def build_from_collection_output_selector_ui_preview_lines(
    preview: BuildFromCollectionOutputSelectorUIPreview | None = None,
    selected_build_depth_key: str | None = None,
) -> list[str]:
    if preview is None:
        preview = create_build_from_collection_output_selector_ui_preview(selected_build_depth_key)

    return [
        "Build From Collection Output Selector UI",
        f"Selected depth: {preview.build_depth_label}",
        f"Selected route: {preview.output_route}",
        f"Writer key: {preview.writer_key}",
        "Available output routes:",
        "- B - Build-Start Summary -> build_start_summary",
        "- C - Owned Cards By Role -> owned_cards_by_role",
        "- D - Rough Shell -> rough_shell",
        "- E - Full 100-Card Draft -> full_100_card_draft",
        "Selector UI only: this preview does not execute writers.",
        "No exact card selection in this patch.",
        "No final deck inclusion decisions in this patch.",
        "No role-count target generation in this patch.",
        "No mana-base generation in this patch.",
        "No land insertion in this patch.",
        "No completed shell generation in this patch.",
        "No shell generation in this patch.",
        "No full 100-card draft generation in this patch.",
        "No deck generation in this patch.",
    ]
