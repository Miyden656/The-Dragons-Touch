"""Debug/stress-test section builders.

These helpers format structured checkpoint summaries into separate debug files.
They intentionally do not perform analysis; they only render already-built data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app_io.output_writer import get_unique_output_path, write_text_file
from analysis.deck_building_philosophies import render_philosophy_diagnostics_section
from legality.companion_rules import COMPANION_CARD_NAMES


COMPANION_CARD_NAMES: set[str] = {
    "Gyruda, Doom of Depths",
    "Jegantha, the Wellspring",
    "Kaheera, the Orphanguard",
    "Keruga, the Macrosage",
    "Lurrus of the Dream-Den",
    "Lutri, the Spellchaser",
    "Obosh, the Preypiercer",
    "Umori, the Collector",
    "Yorion, Sky Nomad",
    "Zirda, the Dawnwaker",
}


def _possible_companion_names_from_reference(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    command_zone = context.get("command_zone")
    known_companions = {str(name).lower() for name in getattr(command_zone, "companion_names", []) or []}
    candidates: list[str] = []
    for name in getattr(parsed, "reference_cards", []) or []:
        clean_name = str(name).strip()
        if clean_name in COMPANION_CARD_NAMES and clean_name.lower() not in known_companions:
            if clean_name not in candidates:
                candidates.append(clean_name)
    return candidates


@dataclass(slots=True)
class DebugSectionPaths:
    legality: Path
    strategy: Path
    bracket: Path
    cut_pressure: Path
    replacement_prompt: Path
    diagnostics: Path


def _bullet_list(values: list[str], empty: str = "None") -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def build_legality_debug_section(context: dict[str, Any]) -> str:
    parsed = context["parsed_deck"]
    command_zone = context["command_zone"]
    legality = context["legality"]
    lines = [
        "# Debug — Legality",
        "",
        f"Deck file: {parsed.deck_file}",
        f"Deck card count: {parsed.deck_card_count}",
        f"Commander(s): {', '.join(command_zone.commander_names) if command_zone.commander_names else 'Unknown'}",
        f"Command-zone rule: {command_zone.command_zone_rule_detected}",
        f"Commander color identity: {command_zone.commander_color_identity_text}",
        f"Deck size legal: {legality.deck_size_legal}",
        f"Companion(s): {', '.join(getattr(command_zone, 'companion_names', []) or []) if getattr(command_zone, 'companion_names', []) else 'None'}",
        f"Possible reference companion(s): {', '.join(getattr(command_zone, 'possible_reference_companion_names', []) or []) if getattr(command_zone, 'possible_reference_companion_names', []) else 'None'}",
        f"Companion legality checked: {getattr(legality, 'companion_legality_checked', False)}",
        f"Companion legality legal: {getattr(legality, 'companion_legality_legal', None)}",
        f"Companion legality violations: {len(getattr(legality, 'companion_legality_violations', []) or [])}",
        f"Manual companion reviews: {len(getattr(legality, 'manual_review_companion_cards', []) or [])}",
        "",
        "## Cards not found",
        *_bullet_list(legality.cards_not_found),
        "",
        "## Color identity violations",
    ]
    if legality.color_identity_violations:
        for item in legality.color_identity_violations:
            lines.append(f"- {item.get('card_name')}: card {item.get('card_color_identity')} vs commander {item.get('commander_color_identity')}")
    else:
        lines.append("- None")
    lines.extend(["", "## Illegal duplicates"])
    if legality.illegal_duplicate_cards:
        for item in legality.illegal_duplicate_cards:
            lines.append(f"- {item.get('card_name')}: {item.get('quantity')} copies")
    else:
        lines.append("- None")

    lines.extend(["", "## Companion legality notes"])
    companion_notes = list(getattr(legality, "companion_legality_notes", []) or [])
    lines.extend(_bullet_list(companion_notes))

    lines.extend(["", "## Companion recommendation filters"])
    filter_notes = list(getattr(legality, "companion_replacement_filter_notes", []) or [])
    lines.extend(_bullet_list(filter_notes))

    lines.extend(["", "## Companion legality violations"])
    violations = list(getattr(legality, "companion_legality_violations", []) or [])
    if violations:
        for item in violations:
            lines.append(f"- {item.get('card_name')} x{item.get('quantity', 1)}: {item.get('reason')}")
    else:
        lines.append("- None")

    lines.extend(["", "## Manual companion reviews"])
    manual_reviews = list(getattr(legality, "manual_review_companion_cards", []) or [])
    if manual_reviews:
        for item in manual_reviews:
            lines.append(f"- {item.get('card_name')}: {item.get('reason')}")
    else:
        lines.append("- None")

    return "\n".join(lines)


def build_strategy_debug_section(context: dict[str, Any]) -> str:
    role_summary = context["role_summary"]
    strategy = context["strategy_summary"]
    plan_fit = context["plan_fit_summary"]
    lines = [
        "# Debug — Strategy",
        "",
        f"Primary strategy: {strategy.primary_strategy}",
        f"Secondary strategy: {strategy.secondary_strategy}",
        f"Confidence: {strategy.confidence}",
        "",
        "## Top role counts",
    ]
    for tag, count in role_summary.role_counts.most_common(25):
        lines.append(f"- {tag}: {count}")
    lines.extend(["", "## Strategy candidates"])
    for candidate in strategy.candidates[:20]:
        lines.append(f"- {candidate.name}: score {candidate.score}; layer {candidate.layer}; gate {candidate.gate_passed}; {candidate.gate_reason}")
    lines.extend(["", "## Strong synergy examples"])
    for entry in plan_fit.strong_synergy_cards[:20]:
        lines.append(f"- {entry.card_name}: {'; '.join(entry.reasons)}")
    lines.extend(["", "## Possible off-plan examples"])
    for entry in plan_fit.possible_off_plan_cards[:20]:
        lines.append(f"- {entry.card_name}: {'; '.join(entry.reasons)}")
    return "\n".join(lines)


def build_bracket_debug_section(context: dict[str, Any]) -> str:
    bracket = context["bracket_summary"]
    lines = [
        "# Debug — Bracket Pressure",
        "",
        f"Estimated pressure: {bracket.estimated_bracket}",
        f"Pressure level: {bracket.pressure_level}",
        "",
        "## Notes",
        *_bullet_list(bracket.notes),
        "",
        "## Pressure cards",
    ]
    if bracket.pressure_cards:
        for entry in bracket.pressure_cards:
            lines.append(f"- {entry.card_name} x{entry.quantity}: {entry.pressure_type} — {entry.reason}")
    else:
        lines.append("- None")
    return "\n".join(lines)


def build_cut_pressure_debug_section(context: dict[str, Any]) -> str:
    cut_pressure = context["cut_pressure"]
    possible = context["possible_cuts"]
    lines = [
        "# Debug — Cut Pressure",
        "",
        f"Status: {cut_pressure.status}",
        f"Current deck size: {cut_pressure.deck_card_count}",
        f"Required cuts: {cut_pressure.required_cuts}",
        f"Short cards: {cut_pressure.short_cards}",
        f"Optional cut target: {cut_pressure.optional_cut_target}",
        f"Cut mode: {cut_pressure.cut_mode}",
        "",
        "## Notes",
        *_bullet_list(cut_pressure.notes + possible.notes),
        "",
        "## Required candidates",
    ]
    for entry in possible.required_cut_candidates:
        lines.append(f"- {entry.card_name}: {entry.cut_type}; confidence {entry.cut_confidence}; score {entry.score}; {'; '.join(entry.reasons)}")
    if not possible.required_cut_candidates:
        lines.append("- None")
    lines.extend(["", "## Optional candidates"])
    for entry in possible.optional_cut_candidates:
        lines.append(f"- {entry.card_name}: {entry.cut_type}; confidence {entry.cut_confidence}; score {entry.score}; {'; '.join(entry.reasons)}")
    if not possible.optional_cut_candidates:
        lines.append("- None")
    return "\n".join(lines)


def build_replacement_prompt_debug_section(context: dict[str, Any]) -> str:
    replacement = context["replacement_needs"]
    completion = context.get("deck_completion")
    legality = context.get("legality")
    lines = ["# Debug — Replacement / Completion", "", "## Priority categories"]
    lines.extend(_bullet_list(replacement.priority_categories))
    lines.extend(["", "## Replacement notes"])
    lines.extend(_bullet_list(replacement.notes))
    companion_filters = list(getattr(legality, "companion_replacement_filter_notes", []) or []) if legality else []
    lines.extend(["", "## Companion-aware recommendation filters"])
    lines.extend(_bullet_list(companion_filters))
    if completion:
        lines.extend(["", "## Completion notes"])
        lines.append(f"- Cards needed: {completion.cards_needed}")
        lines.append(f"- Build-up mode: {completion.build_up_label}")
        lines.extend(_bullet_list(completion.notes))
    return "\n".join(lines)


def build_diagnostics_debug_section(context: dict[str, Any]) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    philosophy_context = context.get("philosophy_context") or {}
    lines = [
        "# Debug — Diagnostics",
        "",
        f"Output mode: {runtime_config.output_mode}",
        f"Review direction: {runtime_config.review_direction}",
        f"Prompt interaction mode: {runtime_config.prompt_interaction_mode}",
        f"Philosophy key: {getattr(runtime_config, 'philosophy_key', 'balanced_unknown')}",
        f"Guide preference: {getattr(runtime_config, 'guide_preference', 'either')}",
        f"Resolved philosophy lens: {philosophy_context.get('label', 'Balanced / Unknown')}",
        f"Resolved guide: {philosophy_context.get('guide_name') or 'No named guide selected'}",
        f"Build-up config: {runtime_config.build_up_config}",
        f"Cut-depth config: {runtime_config.cut_depth_config}",
        "",
    ]
    if philosophy_context:
        lines.extend(render_philosophy_diagnostics_section(philosophy_context).splitlines())
        lines.append("")
    cards_by_section = getattr(parsed, "cards_by_section", {}) or {}
    reference_by_section = getattr(parsed, "reference_cards_by_section", {}) or {}
    card_roles = getattr(context.get("role_summary"), "card_roles", []) if context.get("role_summary") else []
    possible_companions = _possible_companion_names_from_reference(context)
    lines.extend([
        "## AI Handoff Export Checks",
        "- Full decklist expected in normal report: Yes",
        "- Annotated card role notes expected in normal report: Yes",
        "- Companion verification warning expected when reference companion is detected: Yes",
        f"- Main deck card count available to report: {parsed.deck_card_count}",
        f"- Unique main deck cards available to report: {len(parsed.unique_cards)}",
        f"- Sectioned main-deck groups available to report: {len(cards_by_section)}",
        f"- Annotated role entries available to report: {len(card_roles)}",
        f"- Reference/non-mainboard cards available to report: {parsed.reference_card_count}",
        f"- Reference/non-mainboard section groups available to report: {len(reference_by_section)}",
        f"- Possible companion detected in reference/non-mainboard cards: {'Yes' if possible_companions else 'No'}",
        f"- Possible companion names: {', '.join(possible_companions) if possible_companions else 'None'}",
        f"- Confirmed companion names: {', '.join(getattr(context.get('command_zone'), 'companion_names', []) or []) if getattr(context.get('command_zone'), 'companion_names', []) else 'None'}",
        f"- Companion legality checked: {'Yes' if getattr(context.get('legality'), 'companion_legality_checked', False) else 'No'}",
        f"- Companion legality violations: {len(getattr(context.get('legality'), 'companion_legality_violations', []) or [])}",
        f"- Manual companion reviews: {len(getattr(context.get('legality'), 'manual_review_companion_cards', []) or [])}",
        "",
        "## Parser hygiene",
        f"- Ignored/unparsed lines: {len(parsed.ignored_lines)}",
        f"- Reference/non-mainboard cards ignored: {parsed.reference_card_count}",
    ])
    if parsed.ignored_lines:
        lines.extend(["", "## Ignored lines"])
        lines.extend(_bullet_list(parsed.ignored_lines[:30]))
    return "\n".join(lines)


def write_debug_sections(deck_folder: Path, deck_name: str, context: dict[str, Any]) -> DebugSectionPaths:
    builders = [
        ("legality", build_legality_debug_section),
        ("strategy", build_strategy_debug_section),
        ("bracket", build_bracket_debug_section),
        ("cut_pressure", build_cut_pressure_debug_section),
        ("replacement_prompt", build_replacement_prompt_debug_section),
        ("diagnostics", build_diagnostics_debug_section),
    ]
    paths: dict[str, Path] = {}
    for key, builder in builders:
        path = get_unique_output_path(deck_folder, f"{deck_name}_{key}_debug", ".md")
        write_text_file(path, builder(context))
        paths[key] = path
    return DebugSectionPaths(
        legality=paths["legality"],
        strategy=paths["strategy"],
        bracket=paths["bracket"],
        cut_pressure=paths["cut_pressure"],
        replacement_prompt=paths["replacement_prompt"],
        diagnostics=paths["diagnostics"],
    )
