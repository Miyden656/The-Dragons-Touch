"""
Build Depth Selection Model for The Dragon's Touch v1.3.12.

Marker: v1.3.12 Build Depth Selection Model.
Marker: selectable build depth options.
Marker: Build-Start Summary.
Marker: Owned Cards By Role.
Marker: Rough Shell.
Marker: Full 100-Card Draft.
Marker: user-selected build depth.
Marker: No deck generation in this patch.
Marker: No exact card selection in this patch.
Marker: No mana-base generation in this patch.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

BUILD_DEPTH_START_SUMMARY = "build_start_summary"
BUILD_DEPTH_OWNED_CARDS_BY_ROLE = "owned_cards_by_role"
BUILD_DEPTH_ROUGH_SHELL = "rough_shell"
BUILD_DEPTH_FULL_100_CARD_DRAFT = "full_100_card_draft"

DEFAULT_BUILD_DEPTH_KEY = BUILD_DEPTH_START_SUMMARY

BUILD_DEPTH_ALIASES: dict[str, str] = {
    "summary": BUILD_DEPTH_START_SUMMARY,
    "build summary": BUILD_DEPTH_START_SUMMARY,
    "build-start summary": BUILD_DEPTH_START_SUMMARY,
    "build_start": BUILD_DEPTH_START_SUMMARY,
    "start": BUILD_DEPTH_START_SUMMARY,
    "b": BUILD_DEPTH_START_SUMMARY,
    "role bucket preview": BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
    "owned cards by role": BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
    "cards by role": BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
    "role preview": BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
    "c": BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
    "rough shell": BUILD_DEPTH_ROUGH_SHELL,
    "shell": BUILD_DEPTH_ROUGH_SHELL,
    "incomplete shell": BUILD_DEPTH_ROUGH_SHELL,
    "d": BUILD_DEPTH_ROUGH_SHELL,
    "full draft": BUILD_DEPTH_FULL_100_CARD_DRAFT,
    "100-card draft": BUILD_DEPTH_FULL_100_CARD_DRAFT,
    "full 100-card draft": BUILD_DEPTH_FULL_100_CARD_DRAFT,
    "complete draft": BUILD_DEPTH_FULL_100_CARD_DRAFT,
    "e": BUILD_DEPTH_FULL_100_CARD_DRAFT,
}


@dataclass(frozen=True, slots=True)
class BuildDepthOption:
    """A selectable future build depth for Commander's Call."""

    key: str
    label: str
    user_choice_label: str
    description: str
    includes_build_start_summary: bool = True
    includes_owned_cards_by_role: bool = False
    includes_rough_shell: bool = False
    includes_full_100_card_draft: bool = False
    can_select_exact_cards_when_executed: bool = False
    can_generate_role_counts_when_executed: bool = False
    can_generate_mana_base_when_executed: bool = False
    can_insert_lands_when_executed: bool = False
    can_generate_deck_when_executed: bool = False
    produces_human_readable_report_when_executed: bool = True
    produces_ai_handoff_prompt_when_executed: bool = True
    model_only_now: bool = True
    boundary_note: str = "v1.3.12 defines selectable build depth only; it does not execute deck generation."

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "user_choice_label": self.user_choice_label,
            "description": self.description,
            "includes_build_start_summary": self.includes_build_start_summary,
            "includes_owned_cards_by_role": self.includes_owned_cards_by_role,
            "includes_rough_shell": self.includes_rough_shell,
            "includes_full_100_card_draft": self.includes_full_100_card_draft,
            "can_select_exact_cards_when_executed": self.can_select_exact_cards_when_executed,
            "can_generate_role_counts_when_executed": self.can_generate_role_counts_when_executed,
            "can_generate_mana_base_when_executed": self.can_generate_mana_base_when_executed,
            "can_insert_lands_when_executed": self.can_insert_lands_when_executed,
            "can_generate_deck_when_executed": self.can_generate_deck_when_executed,
            "produces_human_readable_report_when_executed": self.produces_human_readable_report_when_executed,
            "produces_ai_handoff_prompt_when_executed": self.produces_ai_handoff_prompt_when_executed,
            "model_only_now": self.model_only_now,
            "boundary_note": self.boundary_note,
        }


BUILD_DEPTH_OPTIONS: tuple[BuildDepthOption, ...] = (
    BuildDepthOption(
        key=BUILD_DEPTH_START_SUMMARY,
        label="Build-Start Summary",
        user_choice_label="B — Build-Start Summary",
        description=(
            "Creates a light commander build-start report with selected commander, inferred/selected strategy, "
            "philosophy context, land policy, and next-step guidance."
        ),
    ),
    BuildDepthOption(
        key=BUILD_DEPTH_OWNED_CARDS_BY_ROLE,
        label="Owned Cards By Role",
        user_choice_label="C — Owned Cards By Role",
        description=(
            "Shows role buckets and owned collection candidates that may fit each role without making final deck inclusions."
        ),
        includes_owned_cards_by_role=True,
    ),
    BuildDepthOption(
        key=BUILD_DEPTH_ROUGH_SHELL,
        label="Rough Shell",
        user_choice_label="D — Rough Shell",
        description=(
            "Builds a rough/incomplete commander shell from the collection when executed, while still clearly labeling it as a draft."
        ),
        includes_owned_cards_by_role=True,
        includes_rough_shell=True,
        can_select_exact_cards_when_executed=True,
        can_generate_role_counts_when_executed=True,
    ),
    BuildDepthOption(
        key=BUILD_DEPTH_FULL_100_CARD_DRAFT,
        label="Full 100-Card Draft",
        user_choice_label="E — Full 100-Card Draft",
        description=(
            "Creates a complete collection-first 100-card draft when executed, using assumed basics and user-approved outside-collection upgrades when allowed."
        ),
        includes_owned_cards_by_role=True,
        includes_rough_shell=True,
        includes_full_100_card_draft=True,
        can_select_exact_cards_when_executed=True,
        can_generate_role_counts_when_executed=True,
        can_generate_mana_base_when_executed=True,
        can_insert_lands_when_executed=True,
        can_generate_deck_when_executed=True,
    ),
)


@dataclass(slots=True)
class BuildDepthSelectionModel:
    """Selected build depth contract for future Build From Collection execution."""

    selected_depth_key: str = DEFAULT_BUILD_DEPTH_KEY
    available_depths: tuple[BuildDepthOption, ...] = field(default_factory=lambda: BUILD_DEPTH_OPTIONS)
    user_selectable: bool = True
    strategy_inference_allowed: bool = True
    strategy_override_allowed: bool = True
    philosophy_selection_allowed: bool = True
    collection_source_selectable: bool = True
    outside_collection_upgrades_user_controlled: bool = True
    produces_human_readable_report: bool = True
    produces_ai_handoff_prompt: bool = True
    model_only_now: bool = True
    exact_card_selection_now: bool = False
    role_count_target_generated_now: bool = False
    mana_base_generated_now: bool = False
    land_inserted_now: bool = False
    shell_generated_now: bool = False
    deck_generated_now: bool = False
    basic_land_policy: str = "Basic lands are assumed available."
    nonbasic_land_policy: str = "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
    deferred_behavior: tuple[str, ...] = (
        "No exact card selection in this patch",
        "No role-count target generation in this patch",
        "No mana-base generation in this patch",
        "No land insertion in this patch",
        "No shell generation in this patch",
        "No deck generation in this patch",
        "No normal deck review changes",
    )

    @property
    def selected_option(self) -> BuildDepthOption:
        return get_build_depth_option(self.selected_depth_key)

    def to_dict(self) -> dict[str, Any]:
        selected = self.selected_option
        return {
            "selected_depth_key": selected.key,
            "selected_depth_label": selected.label,
            "selected_depth_user_choice_label": selected.user_choice_label,
            "available_depths": [option.to_dict() for option in self.available_depths],
            "user_selectable": self.user_selectable,
            "strategy_inference_allowed": self.strategy_inference_allowed,
            "strategy_override_allowed": self.strategy_override_allowed,
            "philosophy_selection_allowed": self.philosophy_selection_allowed,
            "collection_source_selectable": self.collection_source_selectable,
            "outside_collection_upgrades_user_controlled": self.outside_collection_upgrades_user_controlled,
            "produces_human_readable_report": self.produces_human_readable_report,
            "produces_ai_handoff_prompt": self.produces_ai_handoff_prompt,
            "model_only_now": self.model_only_now,
            "exact_card_selection_now": self.exact_card_selection_now,
            "role_count_target_generated_now": self.role_count_target_generated_now,
            "mana_base_generated_now": self.mana_base_generated_now,
            "land_inserted_now": self.land_inserted_now,
            "shell_generated_now": self.shell_generated_now,
            "deck_generated_now": self.deck_generated_now,
            "basic_land_policy": self.basic_land_policy,
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_12_boundary": (
                "Build Depth Selection Model defines how far the user wants Commander's Call to build. "
                "It supports build-start summary, owned cards by role, rough shell, and full 100-card draft as selectable depths, "
                "but v1.3.12 itself does not select cards, create role counts, generate a mana base, insert lands, build a shell, or generate a deck."
            ),
        }


def normalize_build_depth_key(value: str | None) -> str:
    """Normalize user-facing build depth text into a stable key."""
    raw = (value or "").strip()
    if not raw:
        return DEFAULT_BUILD_DEPTH_KEY
    normalized = raw.lower().replace("_", " ").replace("/", " ").strip()
    normalized = " ".join(normalized.split())
    if normalized in {option.key for option in BUILD_DEPTH_OPTIONS}:
        return normalized
    if raw in {option.key for option in BUILD_DEPTH_OPTIONS}:
        return raw
    return BUILD_DEPTH_ALIASES.get(normalized, DEFAULT_BUILD_DEPTH_KEY)


def get_build_depth_option(value: str | None = None) -> BuildDepthOption:
    """Return a build-depth option by key/alias, defaulting to Build-Start Summary."""
    key = normalize_build_depth_key(value)
    for option in BUILD_DEPTH_OPTIONS:
        if option.key == key:
            return option
    return BUILD_DEPTH_OPTIONS[0]


def build_depth_option_labels() -> tuple[str, ...]:
    """Return labels for UI dropdowns or reports."""
    return tuple(option.user_choice_label for option in BUILD_DEPTH_OPTIONS)


def create_build_depth_selection_model(selected_depth: str | None = None) -> BuildDepthSelectionModel:
    """Create the v1.3.12 build-depth selection model without executing the selected depth."""
    return BuildDepthSelectionModel(selected_depth_key=normalize_build_depth_key(selected_depth))


def build_depth_selection_lines(model: BuildDepthSelectionModel) -> tuple[str, ...]:
    """Return concise report/UI lines for the selected build depth."""
    selected = model.selected_option
    return (
        "Build Depth Selection Model created.",
        f"Selected build depth: {selected.user_choice_label}",
        selected.description,
        "Available build depths: " + "; ".join(build_depth_option_labels()),
        "Strategy can be inferred and overridden by the user.",
        "Philosophy/persona selection is part of future build narrowing.",
        "Collection source behavior should be user-selectable.",
        "Human-readable report output is expected.",
        "AI handoff prompt output is expected.",
        model.basic_land_policy,
        model.nonbasic_land_policy,
        "No deck generation in this patch.",
    )
