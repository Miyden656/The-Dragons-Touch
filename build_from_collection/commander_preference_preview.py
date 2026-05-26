"""Commander + Preference handoff preview for Build From Collection v1.3.4.

Display-only setup context. No deck generation, No 100-card shell generation, No role-bucket generation, No mana-base generation, No land insertion.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy
from .preferences import BuildPreferenceDataShape, CommanderBuildStartContext, build_commander_build_start_context, create_default_build_preferences

@dataclass(slots=True)
class CommanderPreferenceHandoffPreviewData:
    """Display-only Commander + Preference Handoff Preview payload."""
    commander_build_start_context: CommanderBuildStartContext
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    preview_version: str = "v1.3.4"
    preview_name: str = "Commander + Preference Handoff Preview"
    setup_context_only: bool = True
    deferred_behavior: list[str] = field(default_factory=lambda: ["No deck generation", "No 100-card shell generation", "No role-bucket generation", "No mana-base generation", "No land insertion", "No card scoring changes", "No cut or replacement changes", "No normal deck review changes"])
    def to_dict(self) -> dict[str, Any]:
        context_payload = self.commander_build_start_context.to_dict()
        return {"preview_version": self.preview_version, "preview_name": self.preview_name, "setup_context_only": self.setup_context_only, "selected_commander": context_payload.get("selected_commander", {}), "build_preferences": context_payload.get("build_preferences", {}), "basic_land_policy": self.basic_land_policy.to_dict(), "commander_build_start_context": context_payload, "deferred_behavior": list(self.deferred_behavior), "v1_3_4_boundary": "Commander + Preference Handoff Preview only. This does not generate a deck, create a 100-card shell, create role buckets, build a mana base, add lands, score cards, or change normal deck review behavior."}

def create_commander_preference_handoff_preview(selected_commander: Any, *, build_preferences: BuildPreferenceDataShape | None = None) -> CommanderPreferenceHandoffPreviewData:
    """Create a display-only Commander + Preference Handoff Preview payload."""
    preferences = build_preferences or create_default_build_preferences()
    context = build_commander_build_start_context(selected_commander, build_preferences=preferences)
    return CommanderPreferenceHandoffPreviewData(commander_build_start_context=context, basic_land_policy=create_basic_land_access_policy())
