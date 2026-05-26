"""Build preference data shape for Build From Collection v1.3.2.

v1.3.2 defines the player preference payload that can travel with a
selected commander handoff. It is intentionally data-only: no deck generation,
no 100-card shell generation, and no scoring/cut/replacement behavior changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_REPLACEMENT_SOURCE_PREFERENCE = "Prefer my collection first, then suggest outside options only when useful."
DEFAULT_COLLECTION_FIRST_PREFERENCE = "Use owned cards as the starting point."


@dataclass(slots=True)
class BuildPreferenceDataShape:
    """Player-facing build preferences for future collection-first shell work."""

    primary_strategy: str = ""
    secondary_strategy: str = ""
    main_philosophy: str = ""
    sub_philosophy: str = ""
    persona: str = ""
    discovery_mode: str = ""
    build_up_mode: str = ""
    prompt_mode: str = ""
    bracket_preference: str = ""
    collection_first_preference: str = DEFAULT_COLLECTION_FIRST_PREFERENCE
    replacement_source_preference: str = DEFAULT_REPLACEMENT_SOURCE_PREFERENCE
    notes: str = ""
    deferred_behavior: list[str] = field(default_factory=lambda: [
        "No deck generation",
        "No 100-card shell generation",
        "No role-bucket generation",
        "No scoring/cut/replacement changes",
        "No normal deck review changes",
        "No Report Viewer changes",
    ])

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["v1_3_2_boundary"] = (
            "Build preference data shape only. No deck generation, no 100-card "
            "shell generation, and no scoring/cut/replacement changes."
        )
        return data


@dataclass(slots=True)
class CommanderBuildStartContext:
    """Combined selected commander + build preferences preview payload."""

    selected_commander: dict[str, Any]
    build_preferences: BuildPreferenceDataShape = field(default_factory=BuildPreferenceDataShape)
    context_version: str = "v1.3.2"
    context_name: str = "Build Preference Data Shape"

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_version": self.context_version,
            "context_name": self.context_name,
            "selected_commander": dict(self.selected_commander),
            "build_preferences": self.build_preferences.to_dict(),
            "v1_3_2_boundary": (
                "Commander + preferences context only. This does not build a deck, "
                "write a decklist, generate cuts, or change normal review behavior."
            ),
        }


def create_default_build_preferences() -> BuildPreferenceDataShape:
    """Return an empty, safe default build preference payload."""
    return BuildPreferenceDataShape()


def build_preferences_from_values(
    *,
    primary_strategy: str = "",
    secondary_strategy: str = "",
    main_philosophy: str = "",
    sub_philosophy: str = "",
    persona: str = "",
    discovery_mode: str = "",
    build_up_mode: str = "",
    prompt_mode: str = "",
    bracket_preference: str = "",
    collection_first_preference: str = DEFAULT_COLLECTION_FIRST_PREFERENCE,
    replacement_source_preference: str = DEFAULT_REPLACEMENT_SOURCE_PREFERENCE,
    notes: str = "",
) -> BuildPreferenceDataShape:
    """Create a build preference data payload without triggering generation."""
    return BuildPreferenceDataShape(
        primary_strategy=primary_strategy.strip(),
        secondary_strategy=secondary_strategy.strip(),
        main_philosophy=main_philosophy.strip(),
        sub_philosophy=sub_philosophy.strip(),
        persona=persona.strip(),
        discovery_mode=discovery_mode.strip(),
        build_up_mode=build_up_mode.strip(),
        prompt_mode=prompt_mode.strip(),
        bracket_preference=bracket_preference.strip(),
        collection_first_preference=collection_first_preference.strip() or DEFAULT_COLLECTION_FIRST_PREFERENCE,
        replacement_source_preference=replacement_source_preference.strip() or DEFAULT_REPLACEMENT_SOURCE_PREFERENCE,
        notes=notes.strip(),
    )


def build_commander_build_start_context(
    selected_commander: Any,
    *,
    build_preferences: BuildPreferenceDataShape | None = None,
) -> CommanderBuildStartContext:
    """Combine selected commander context with preferences for future UI patches.

    selected_commander may be a handoff object with to_dict(), a dataclass-like
    object, or a plain dictionary. This helper returns data only and does not
    build a shell or write files.
    """
    if hasattr(selected_commander, "to_dict"):
        commander_payload = selected_commander.to_dict()
    elif isinstance(selected_commander, dict):
        commander_payload = dict(selected_commander)
    else:
        commander_payload = dict(getattr(selected_commander, "__dict__", {}) or {})

    commander_name = str(
        commander_payload.get("commander_name")
        or commander_payload.get("card_name")
        or ""
    ).strip()
    if not commander_name:
        raise ValueError("CommanderBuildStartContext requires a selected commander name.")

    commander_payload.setdefault("commander_name", commander_name)
    return CommanderBuildStartContext(
        selected_commander=commander_payload,
        build_preferences=build_preferences or create_default_build_preferences(),
    )
