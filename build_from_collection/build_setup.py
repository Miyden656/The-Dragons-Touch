"""Build setup panel preview data for Build From Collection v1.3.3.

This module combines the selected commander handoff baseline, build preference
shape, and basic land access assumption into a display-only preview payload.
It does not generate a deck, create role buckets, add lands, or write build files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy
from .preferences import BuildPreferenceDataShape, build_commander_build_start_context, create_default_build_preferences


@dataclass(slots=True)
class BuildSetupPanelPreviewData:
    """Display-only Build Setup Panel Preview payload."""

    selected_commander: dict[str, Any] = field(default_factory=dict)
    build_preferences: BuildPreferenceDataShape = field(default_factory=create_default_build_preferences)
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    preview_version: str = "v1.3.3"
    preview_name: str = "Build Setup Panel Preview"
    deferred_behavior: list[str] = field(default_factory=lambda: [
        "No deck generation",
        "No 100-card shell generation",
        "No role-bucket generation",
        "No mana-base generation",
        "No land insertion",
        "No normal deck review changes",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_version": self.preview_version,
            "preview_name": self.preview_name,
            "selected_commander": dict(self.selected_commander),
            "build_preferences": self.build_preferences.to_dict(),
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_3_boundary": (
                "Build setup preview only. This does not generate a deck, create a "
                "100-card shell, add basic lands, or change normal deck review behavior."
            ),
        }


def build_setup_panel_preview(
    selected_commander: Any | None = None,
    *,
    build_preferences: BuildPreferenceDataShape | None = None,
) -> BuildSetupPanelPreviewData:
    """Create a display-only build setup preview payload."""
    preferences = build_preferences or create_default_build_preferences()
    selected_payload: dict[str, Any] = {}
    if selected_commander is not None:
        selected_payload = build_commander_build_start_context(
            selected_commander,
            build_preferences=preferences,
        ).to_dict().get("selected_commander", {})
    return BuildSetupPanelPreviewData(
        selected_commander=selected_payload,
        build_preferences=preferences,
        basic_land_policy=create_basic_land_access_policy(),
    )
