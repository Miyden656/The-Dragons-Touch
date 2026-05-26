"""
Build-Start Summary Output — v1.3.18

This module creates the first actual Build From Collection output for
Commander’s Call at build depth B: Build-Start Summary.

It produces two text outputs:
- human-readable Build From Collection build-start summary
- AI handoff prompt

Boundaries:
- No exact card selection in this patch
- No role-count target generation in this patch
- No mana-base generation in this patch
- No land insertion in this patch
- No shell generation in this patch
- No deck generation in this patch
- No 100-card shell generation in this patch

Land policy:
- Basic lands are assumed available
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


BUILD_START_SUMMARY_OUTPUT_NAME = "Build-Start Summary Output"


def _value_from(source: Any, *names: str, default: Any = "") -> Any:
    """Safely read a value from an object, mapping, or nested preview payload."""

    if source is None:
        return default
    for name in names:
        if isinstance(source, dict) and name in source:
            value = source.get(name)
            if value not in (None, ""):
                return value
        if hasattr(source, name):
            value = getattr(source, name)
            if value not in (None, ""):
                return value
    return default


def _dict_from_preview(source: Any) -> dict[str, Any]:
    if source is None:
        return {}
    if isinstance(source, dict):
        return source
    if hasattr(source, "to_dict"):
        try:
            payload = source.to_dict()
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
    return {}


def _selected_commander_name(selected_commander: Any) -> str:
    data = _dict_from_preview(selected_commander)
    return str(
        _value_from(
            data or selected_commander,
            "commander_name",
            "card_name",
            "name",
            "display_name",
            default="Selected commander not named yet",
        )
    )


def _selected_commander_color_identity(selected_commander: Any) -> str:
    data = _dict_from_preview(selected_commander)
    return str(
        _value_from(
            data or selected_commander,
            "color_identity_text",
            "color_identity_label",
            "color_identity_key",
            "color_identity",
            default="Not recorded yet",
        )
    )


def _selected_commander_owned_quantity(selected_commander: Any) -> str:
    data = _dict_from_preview(selected_commander)
    value = _value_from(data or selected_commander, "owned_quantity", "quantity", "count", default="Not recorded yet")
    return str(value)


def _strategy_payload(strategy_selection_preview: Any) -> dict[str, Any]:
    data = _dict_from_preview(strategy_selection_preview)
    if "selected_primary_strategy" in data or "selected_secondary_strategy" in data:
        return data
    return {
        "selected_primary_strategy": _value_from(data, "primary_strategy", default=""),
        "selected_secondary_strategy": _value_from(data, "secondary_strategy", default=""),
        "inferred_strategy_suggestions": data.get("inferred_strategy_suggestions", []) if isinstance(data, dict) else [],
    }


def _philosophy_payload(philosophy_bracket_preview: Any) -> dict[str, Any]:
    data = _dict_from_preview(philosophy_bracket_preview)
    return {
        "main_philosophy": _value_from(data, "main_philosophy", default="Not selected yet"),
        "sub_philosophy": _value_from(data, "sub_philosophy", "persona", default="Not selected yet"),
        "bracket_preference": _value_from(data, "bracket_preference", default="Not selected yet"),
    }


def _collection_payload(collection_source_preview: Any) -> dict[str, Any]:
    data = _dict_from_preview(collection_source_preview)
    return {
        "collection_source_preference": _value_from(
            data,
            "collection_source_label",
            "collection_source_preference",
            "preference_label",
            default="Prefer owned cards, suggest exact outside-collection upgrades",
        ),
        "outside_collection_upgrades_allowed": bool(
            _value_from(data, "outside_collection_upgrades_allowed", default=False)
        ),
    }


def _build_depth_payload(build_depth_selection: Any, build_depth_key: str = "B") -> dict[str, Any]:
    data = _dict_from_preview(build_depth_selection)
    key = str(_value_from(data, "selected_key", "build_depth_key", "key", default=build_depth_key or "B")).strip().upper() or "B"
    label = str(
        _value_from(
            data,
            "selected_label",
            "build_depth_label",
            "label",
            default="Build-Start Summary" if key == "B" else key,
        )
    )
    return {"build_depth_key": key, "build_depth_label": label}


@dataclass(frozen=True)
class BuildStartSummaryOutput:
    """Human-readable and AI-handoff build-start output for depth B."""

    name: str = BUILD_START_SUMMARY_OUTPUT_NAME
    patch_version: str = "v1.3.18"
    output_depth_key: str = "B"
    output_depth_label: str = "Build-Start Summary"
    selected_commander_name: str = "Selected commander not named yet"
    selected_commander_color_identity: str = "Not recorded yet"
    selected_commander_owned_quantity: str = "Not recorded yet"
    primary_strategy: str = "Not selected yet"
    secondary_strategy: str = "Not selected yet"
    inferred_strategy_suggestions: tuple[str, ...] = field(default_factory=tuple)
    main_philosophy: str = "Not selected yet"
    sub_philosophy: str = "Not selected yet"
    bracket_preference: str = "Not selected yet"
    collection_source_preference: str = "Prefer owned cards, suggest exact outside-collection upgrades"
    outside_collection_upgrades_allowed: bool = False
    basic_land_policy: str = "Basic lands are assumed available: Plains, Island, Swamp, Mountain, Forest, Wastes."
    nonbasic_land_policy: str = "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
    human_report_markdown: str = ""
    ai_handoff_prompt: str = ""
    exact_card_selection_performed: bool = False
    role_count_targets_generated: bool = False
    mana_base_generated: bool = False
    lands_inserted: bool = False
    shell_generated: bool = False
    deck_generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "patch_version": self.patch_version,
            "output_depth_key": self.output_depth_key,
            "output_depth_label": self.output_depth_label,
            "selected_commander_name": self.selected_commander_name,
            "selected_commander_color_identity": self.selected_commander_color_identity,
            "selected_commander_owned_quantity": self.selected_commander_owned_quantity,
            "primary_strategy": self.primary_strategy,
            "secondary_strategy": self.secondary_strategy,
            "inferred_strategy_suggestions": list(self.inferred_strategy_suggestions),
            "main_philosophy": self.main_philosophy,
            "sub_philosophy": self.sub_philosophy,
            "bracket_preference": self.bracket_preference,
            "collection_source_preference": self.collection_source_preference,
            "outside_collection_upgrades_allowed": self.outside_collection_upgrades_allowed,
            "basic_land_policy": self.basic_land_policy,
            "nonbasic_land_policy": self.nonbasic_land_policy,
            "human_report_markdown": self.human_report_markdown,
            "ai_handoff_prompt": self.ai_handoff_prompt,
            "exact_card_selection_performed": self.exact_card_selection_performed,
            "role_count_targets_generated": self.role_count_targets_generated,
            "mana_base_generated": self.mana_base_generated,
            "lands_inserted": self.lands_inserted,
            "shell_generated": self.shell_generated,
            "deck_generated": self.deck_generated,
        }


def create_build_start_summary_output(
    selected_commander: Any = None,
    build_depth_selection: Any = None,
    strategy_selection_preview: Any = None,
    philosophy_bracket_preview: Any = None,
    collection_source_preview: Any = None,
    setup_summary_preview: Any = None,
    *,
    build_depth_key: str = "B",
    primary_strategy: str = "",
    secondary_strategy: str = "",
    main_philosophy: str = "",
    sub_philosophy: str = "",
    bracket_preference: str = "",
    collection_source_preference: str = "",
    outside_collection_upgrades_allowed: bool | None = None,
) -> BuildStartSummaryOutput:
    """Create the first Build From Collection output without building a deck.

    This is depth B only: Build-Start Summary. It creates human-readable text and
    an AI handoff prompt, but it does not select exact cards or generate a deck.
    """

    setup_data = _dict_from_preview(setup_summary_preview)
    if selected_commander is None and setup_data:
        selected_commander = setup_data.get("selected_commander") or setup_data.get("commander")
    if build_depth_selection is None and setup_data:
        build_depth_selection = setup_data.get("build_depth_selection")
    if strategy_selection_preview is None and setup_data:
        strategy_selection_preview = setup_data.get("strategy_selection_preview")
    if philosophy_bracket_preview is None and setup_data:
        philosophy_bracket_preview = setup_data.get("philosophy_bracket_preview")
    if collection_source_preview is None and setup_data:
        collection_source_preview = setup_data.get("collection_source_preview")

    depth = _build_depth_payload(build_depth_selection, build_depth_key=build_depth_key)
    strategy = _strategy_payload(strategy_selection_preview)
    philosophy = _philosophy_payload(philosophy_bracket_preview)
    collection = _collection_payload(collection_source_preview)

    active_primary = primary_strategy or strategy.get("selected_primary_strategy") or strategy.get("primary_strategy") or "Not selected yet"
    active_secondary = secondary_strategy or strategy.get("selected_secondary_strategy") or strategy.get("secondary_strategy") or "Not selected yet"
    active_main_philosophy = main_philosophy or philosophy.get("main_philosophy") or "Not selected yet"
    active_sub_philosophy = sub_philosophy or philosophy.get("sub_philosophy") or "Not selected yet"
    active_bracket = bracket_preference or philosophy.get("bracket_preference") or "Not selected yet"
    active_collection = collection_source_preference or collection.get("collection_source_preference") or "Prefer owned cards, suggest exact outside-collection upgrades"
    if outside_collection_upgrades_allowed is None:
        active_outside_allowed = bool(collection.get("outside_collection_upgrades_allowed"))
    else:
        active_outside_allowed = bool(outside_collection_upgrades_allowed)

    commander_name = _selected_commander_name(selected_commander)
    color_identity = _selected_commander_color_identity(selected_commander)
    owned_quantity = _selected_commander_owned_quantity(selected_commander)
    inferred = tuple(str(item) for item in (strategy.get("inferred_strategy_suggestions") or ()))

    human = _build_human_report_markdown(
        commander_name=commander_name,
        color_identity=color_identity,
        owned_quantity=owned_quantity,
        build_depth_label=depth["build_depth_label"],
        primary_strategy=active_primary,
        secondary_strategy=active_secondary,
        inferred_strategy_suggestions=inferred,
        main_philosophy=active_main_philosophy,
        sub_philosophy=active_sub_philosophy,
        bracket_preference=active_bracket,
        collection_source_preference=active_collection,
        outside_collection_upgrades_allowed=active_outside_allowed,
    )
    ai_prompt = _build_ai_handoff_prompt(
        commander_name=commander_name,
        color_identity=color_identity,
        owned_quantity=owned_quantity,
        build_depth_label=depth["build_depth_label"],
        primary_strategy=active_primary,
        secondary_strategy=active_secondary,
        main_philosophy=active_main_philosophy,
        sub_philosophy=active_sub_philosophy,
        bracket_preference=active_bracket,
        collection_source_preference=active_collection,
        outside_collection_upgrades_allowed=active_outside_allowed,
    )

    return BuildStartSummaryOutput(
        output_depth_key=depth["build_depth_key"],
        output_depth_label=depth["build_depth_label"],
        selected_commander_name=commander_name,
        selected_commander_color_identity=color_identity,
        selected_commander_owned_quantity=owned_quantity,
        primary_strategy=active_primary,
        secondary_strategy=active_secondary,
        inferred_strategy_suggestions=inferred,
        main_philosophy=active_main_philosophy,
        sub_philosophy=active_sub_philosophy,
        bracket_preference=active_bracket,
        collection_source_preference=active_collection,
        outside_collection_upgrades_allowed=active_outside_allowed,
        human_report_markdown=human,
        ai_handoff_prompt=ai_prompt,
    )


def build_start_summary_output_lines(output: BuildStartSummaryOutput) -> tuple[str, ...]:
    """Return concise lines for UI display or verifier checks."""

    return (
        "Build-Start Summary Output created.",
        "This is the first actual Build From Collection output for depth B.",
        f"Commander: {output.selected_commander_name}",
        f"Color identity: {output.selected_commander_color_identity}",
        f"Selected build depth: {output.output_depth_label}",
        f"Primary strategy: {output.primary_strategy}",
        f"Secondary strategy: {output.secondary_strategy}",
        f"Main philosophy: {output.main_philosophy}",
        f"Sub-philosophy / persona: {output.sub_philosophy}",
        f"Bracket preference: {output.bracket_preference}",
        f"Collection source preference: {output.collection_source_preference}",
        output.basic_land_policy,
        output.nonbasic_land_policy,
        "Human-readable report generated: Yes",
        "AI handoff prompt generated: Yes",
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell generation.",
        "No deck generation.",
    )


def _build_human_report_markdown(**data: Any) -> str:
    inferred = data.get("inferred_strategy_suggestions") or ()
    inferred_text = ", ".join(inferred) if inferred else "No inferred strategies recorded yet."
    outside = "Yes" if data.get("outside_collection_upgrades_allowed") else "No"
    return f"""# Build From Collection — Build-Start Summary

## Selected Commander
- Commander: {data['commander_name']}
- Color identity: {data['color_identity']}
- Owned quantity: {data['owned_quantity']}

## User Build Direction
- Build depth: {data['build_depth_label']}
- Primary strategy: {data['primary_strategy']}
- Secondary strategy: {data['secondary_strategy']}
- Inferred strategy suggestions: {inferred_text}

## Preference Context
- Main philosophy: {data['main_philosophy']}
- Sub-philosophy / persona: {data['sub_philosophy']}
- Bracket preference: {data['bracket_preference']}
- Collection source preference: {data['collection_source_preference']}
- Outside-collection upgrades allowed: {outside}

## Land Policy
- Basic lands are assumed available: Plains, Island, Swamp, Mountain, Forest, Wastes.
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.

## Current Output Boundary
This build-start summary does not select exact cards, create role-count targets, generate a mana base, insert lands, generate a shell, or generate a deck.
""".strip()


def _build_ai_handoff_prompt(**data: Any) -> str:
    outside = "allowed" if data.get("outside_collection_upgrades_allowed") else "not allowed unless the user changes the preference"
    return f"""You are helping continue a Magic: The Gathering Commander Build From Collection workflow.

Use this build-start context:
- Selected commander: {data['commander_name']}
- Color identity: {data['color_identity']}
- Owned quantity: {data['owned_quantity']}
- Build depth requested: {data['build_depth_label']}
- Primary strategy: {data['primary_strategy']}
- Secondary strategy: {data['secondary_strategy']}
- Main philosophy: {data['main_philosophy']}
- Sub-philosophy / persona: {data['sub_philosophy']}
- Bracket preference: {data['bracket_preference']}
- Collection source preference: {data['collection_source_preference']}
- Outside-collection upgrades are {outside}.

Respect these land rules:
- Assume all needed basic lands are available.
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.

For this v1.3.18 output, do not generate a full deck yet unless a later build-depth execution step explicitly asks for it. Do not invent collection ownership. Do not select exact cards as final inclusions in this build-start summary.
""".strip()
