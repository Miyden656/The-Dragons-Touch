"""
Build From Collection Setup Summary Preview for The Dragon's Touch v1.3.11.

Marker: v1.3.11 Build From Collection Setup Summary Preview.
Marker: v1.3.13 Build Depth Selection UI.
Marker: v1.3.14 Strategy Selection / Override Preview.
Marker: v1.3.15 Philosophy + Bracket Build Preference UI.
Marker: v1.3.16 Collection Source Preference UI.
Marker: collection source preference carried into setup summary.
Marker: outside-collection upgrades are user-controlled.
Marker: philosophy selection carried into setup summary.
Marker: bracket preference carried into setup summary.
Marker: selected strategy carried into setup summary.
Marker: selected build depth carried into setup summary.
Marker: setup summary is preview-only.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No mana-base generation.
Marker: No land insertion.
Marker: No shell completion.
Marker: No deck generation.
Marker: No 100-card shell generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .basic_lands import BasicLandAccessPolicy, create_basic_land_access_policy
from .build_depth import BuildDepthSelectionModel, create_build_depth_selection_model
from .candidate_pool import CollectionCandidatePoolEntry, CollectionCandidatePoolShape, create_collection_candidate_pool_shape
from .owned_role_classification import OwnedCardRoleClassificationPreview, create_owned_card_role_classification_preview
from .preferences import BuildPreferenceDataShape, build_preferences_from_values, create_default_build_preferences
from .role_buckets import CollectionFirstRoleBucketPlan, create_collection_first_role_bucket_plan
from .shell_skeleton import CommanderShellSkeletonPreview, create_commander_shell_skeleton_preview
from .strategy_role_mapping import StrategyRoleBucketMappingPreview, create_strategy_role_bucket_mapping_preview
from .strategy_selection import StrategySelectionOverridePreview, create_strategy_selection_override_preview
from .philosophy_bracket_preferences import PhilosophyBracketBuildPreferencePreview, create_philosophy_bracket_build_preference_preview
from .collection_source_preferences import CollectionSourcePreferencePreview, create_collection_source_preference_preview


@dataclass(slots=True)
class BuildFromCollectionSetupSummaryPreview:
    """Combined preview-only setup summary for future Build From Collection work."""

    selected_commander: Any = None
    build_preferences: BuildPreferenceDataShape = field(default_factory=create_default_build_preferences)
    role_bucket_plan: CollectionFirstRoleBucketPlan = field(default_factory=create_collection_first_role_bucket_plan)
    strategy_mapping_preview: StrategyRoleBucketMappingPreview | None = None
    strategy_selection_preview: StrategySelectionOverridePreview | None = None
    philosophy_bracket_preview: PhilosophyBracketBuildPreferencePreview | None = None
    collection_source_preview: CollectionSourcePreferencePreview | None = None
    candidate_pool_shape: CollectionCandidatePoolShape = field(default_factory=create_collection_candidate_pool_shape)
    owned_role_classification_preview: OwnedCardRoleClassificationPreview | None = None
    shell_skeleton_preview: CommanderShellSkeletonPreview | None = None
    basic_land_policy: BasicLandAccessPolicy = field(default_factory=create_basic_land_access_policy)
    nonbasic_land_policy: str = "Nonbasic lands remain collection-first."
    build_depth_selection: BuildDepthSelectionModel = field(default_factory=create_build_depth_selection_model)
    preview_name: str = "Build From Collection Setup Summary Preview"
    preview_version: str = "v1.3.11"
    preview_only: bool = True
    collection_first: bool = True
    setup_summary_only: bool = True
    exact_card_selection: bool = False
    role_count_target_generated: bool = False
    mana_base_generated: bool = False
    land_inserted: bool = False
    shell_completed: bool = False
    deck_generated: bool = False
    deferred_behavior: tuple[str, ...] = (
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell completion",
        "No shell generation",
        "No deck generation",
        "No 100-card shell generation",
        "No scoring changes",
        "No cut or replacement changes",
        "No normal deck review changes",
    )

    def to_dict(self) -> dict[str, Any]:
        commander_payload: Any
        if hasattr(self.selected_commander, "to_dict"):
            commander_payload = self.selected_commander.to_dict()
        else:
            commander_payload = self.selected_commander

        return {
            "preview_name": self.preview_name,
            "preview_version": self.preview_version,
            "preview_only": self.preview_only,
            "collection_first": self.collection_first,
            "setup_summary_only": self.setup_summary_only,
            "selected_commander": commander_payload,
            "build_preferences": self.build_preferences.to_dict(),
            "role_bucket_plan": self.role_bucket_plan.to_dict(),
            "strategy_mapping_preview": self.strategy_mapping_preview.to_dict() if self.strategy_mapping_preview else {},
            "strategy_selection_preview": self.strategy_selection_preview.to_dict() if self.strategy_selection_preview else {},
            "philosophy_bracket_preview": self.philosophy_bracket_preview.to_dict() if self.philosophy_bracket_preview else {},
            "collection_source_preview": self.collection_source_preview.to_dict() if self.collection_source_preview else {},
            "candidate_pool_shape": self.candidate_pool_shape.to_dict(),
            "owned_role_classification_preview": self.owned_role_classification_preview.to_dict() if self.owned_role_classification_preview else {},
            "shell_skeleton_preview": self.shell_skeleton_preview.to_dict() if self.shell_skeleton_preview else {},
            "basic_land_policy": self.basic_land_policy.to_dict(),
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "build_depth_selection": self.build_depth_selection.to_dict(),
            "exact_card_selection": self.exact_card_selection,
            "role_count_target_generated": self.role_count_target_generated,
            "mana_base_generated": self.mana_base_generated,
            "land_inserted": self.land_inserted,
            "shell_completed": self.shell_completed,
            "deck_generated": self.deck_generated,
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_11_boundary": (
                "Build From Collection Setup Summary Preview combines existing setup context only. "
                "v1.3.13 boundary: selected build depth is carried for future execution but does not execute deck generation now. v1.3.14 boundary: strategy selection and override preview is carried for future execution but does not execute card selection now. "
                "It does not select exact cards, create role-count targets, generate a mana base, insert lands, "
                "complete a shell, generate a deck, score cards, recommend cuts, or change normal deck review behavior. "
                "Basic lands are assumed available; nonbasic lands remain collection-first."
            ),
        }


def create_build_from_collection_setup_summary_preview(
    selected_commander: Any = None,
    primary_strategy: str = "",
    secondary_strategy: str = "",
    main_philosophy: str = "",
    sub_philosophy: str = "",
    persona: str = "",
    discovery_mode: str = "",
    bracket_preference: str = "",
    collection_source_preference: str = "Prefer owned cards, suggest exact outside-collection upgrades",
    collection_first_preference: str = "Collection first",
    replacement_source_preference: str = "Prefer collection first, then wider card pool when needed",
    build_depth_key: str = "B",
    candidate_entries: Iterable[CollectionCandidatePoolEntry] | CollectionCandidatePoolShape | None = None,
) -> BuildFromCollectionSetupSummaryPreview:
    """Create a combined setup summary without selecting cards or generating a shell."""
    if any([
        primary_strategy,
        secondary_strategy,
        main_philosophy,
        sub_philosophy,
        discovery_mode,
        bracket_preference,
        collection_first_preference,
        replacement_source_preference,
    ]):
        preferences = build_preferences_from_values(
            primary_strategy=primary_strategy,
            secondary_strategy=secondary_strategy,
            main_philosophy=main_philosophy,
            sub_philosophy=sub_philosophy,
            persona=persona,
            discovery_mode=discovery_mode,
            bracket_preference=bracket_preference,
            collection_first_preference=collection_first_preference,
            replacement_source_preference=replacement_source_preference,
        )
    else:
        preferences = create_default_build_preferences()

    if isinstance(candidate_entries, CollectionCandidatePoolShape):
        candidate_pool = candidate_entries
    else:
        candidate_pool = create_collection_candidate_pool_shape(tuple(candidate_entries or ()))

    collection_source = create_collection_source_preference_preview(
        collection_source_preference=collection_source_preference,
    )
    philosophy_bracket = create_philosophy_bracket_build_preference_preview(
        main_philosophy=main_philosophy,
        sub_philosophy=sub_philosophy,
        persona=persona,
        bracket_preference=bracket_preference,
        user_override_allowed=True,
    )
    strategy_selection = create_strategy_selection_override_preview(
        selected_commander=selected_commander,
        primary_strategy=preferences.primary_strategy,
        secondary_strategy=preferences.secondary_strategy,
        user_override_allowed=True,
    )
    strategy_mapping = create_strategy_role_bucket_mapping_preview(
        primary_strategy=strategy_selection.primary_strategy or preferences.primary_strategy,
        secondary_strategy=strategy_selection.secondary_strategy or preferences.secondary_strategy,
    )
    owned_roles = create_owned_card_role_classification_preview(
        candidate_pool,
        primary_strategy=preferences.primary_strategy,
        secondary_strategy=preferences.secondary_strategy,
    )
    shell_skeleton = create_commander_shell_skeleton_preview(
        selected_commander=selected_commander,
        primary_strategy=preferences.primary_strategy,
        secondary_strategy=preferences.secondary_strategy,
    )

    return BuildFromCollectionSetupSummaryPreview(
        selected_commander=selected_commander,
        build_preferences=preferences,
        role_bucket_plan=create_collection_first_role_bucket_plan(),
        strategy_mapping_preview=strategy_mapping,
        strategy_selection_preview=strategy_selection,
        philosophy_bracket_preview=philosophy_bracket,
        collection_source_preview=collection_source,
        candidate_pool_shape=candidate_pool,
        owned_role_classification_preview=owned_roles,
        shell_skeleton_preview=shell_skeleton,
        build_depth_selection=create_build_depth_selection_model(build_depth_key),
    )


def setup_summary_preview_lines(preview: BuildFromCollectionSetupSummaryPreview) -> tuple[str, ...]:
    """Return concise UI/report lines for the v1.3.11 setup summary preview."""
    data = preview.to_dict()
    prefs = data.get("build_preferences", {}) or {}
    build_depth = data.get("build_depth_selection", {}) or {}
    strategy_selection = data.get("strategy_selection_preview", {}) or {}
    philosophy_bracket = data.get("philosophy_bracket_preview", {}) or {}
    collection_source = data.get("collection_source_preview", {}) or {}
    shell = data.get("shell_skeleton_preview", {}) or {}
    sections = shell.get("sections", []) or []
    basic_policy = data.get("basic_land_policy", {}) or {}
    basics = basic_policy.get("assumed_available_basic_lands", []) or []
    lines = [
        "Build From Collection Setup Summary Preview created.",
        "This is setup context only; it does not build the deck.",
        f"Primary strategy: {prefs.get('primary_strategy') or 'Not selected yet'}",
        f"Secondary strategy: {prefs.get('secondary_strategy') or 'Not selected yet'}",
        f"Main philosophy: {prefs.get('main_philosophy') or 'Not selected yet'}",
        f"Sub-philosophy / persona: {prefs.get('sub_philosophy') or 'Not selected yet'}",
        f"Discovery mode: {prefs.get('discovery_mode') or 'Not selected yet'}",
        f"Bracket preference: {prefs.get('bracket_preference') or 'Not selected yet'}",
        f"Collection-first preference: {prefs.get('collection_first_preference') or 'Collection first'}",
        f"Replacement source preference: {prefs.get('replacement_source_preference') or 'Prefer collection first, then wider card pool when needed'}",
        f"Selected build depth: {build_depth.get('selected_depth_user_choice_label') or build_depth.get('selected_depth_label') or 'B — Build-Start Summary'}",
        "Build depth selection is user-controlled.",
        "Strategy selection:",
        f"Primary strategy: {strategy_selection.get('primary_strategy') or prefs.get('primary_strategy') or 'Not selected yet'}",
        f"Secondary strategy: {strategy_selection.get('secondary_strategy') or prefs.get('secondary_strategy') or 'Not selected yet'}",
        f"Inferred strategy suggestions: {', '.join(strategy_selection.get('inferred_strategy_labels', [])) if strategy_selection.get('inferred_strategy_labels') else 'None'}",
        "Strategy selection can be inferred or user-overridden.",
        "Collection source preference:",
        f"Collection behavior: {collection_source.get('collection_source_label') or prefs.get('collection_source_preference') or 'Prefer owned cards, suggest exact outside-collection upgrades'}",
        f"Outside-collection upgrades allowed: {'Yes' if collection_source.get('outside_collection_upgrades_allowed') else 'No'}",
        "Outside-collection upgrades are user-controlled.",
        "Philosophy + bracket preference:",
        f"Main philosophy: {philosophy_bracket.get('main_philosophy') or prefs.get('main_philosophy') or 'Not selected yet'}",
        f"Sub-philosophy/persona: {philosophy_bracket.get('sub_philosophy') or philosophy_bracket.get('persona') or prefs.get('sub_philosophy') or prefs.get('persona') or 'Not selected yet'}",
        f"Bracket preference: {philosophy_bracket.get('bracket_preference') or prefs.get('bracket_preference') or 'Not Sure Yet'}",
        "Philosophy and bracket preferences narrow future deck-building choices.",
        f"Shell skeleton sections: {len(sections)} preview sections",
        f"Basic lands assumed available: {', '.join(basics) if basics else 'Plains, Island, Swamp, Mountain, Forest, Wastes'}",
        data.get("nonbasic_land_policy", "Nonbasic lands remain collection-first."),
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell completion.",
        "No deck generation.",
    ]
    return tuple(lines)

# v1.3.15 boundary: philosophy and bracket preferences are carried for future deck-building guidance; No deck generation.

# v1.3.16 boundary: collection source preference is carried for future deck-building guidance; No deck generation.
