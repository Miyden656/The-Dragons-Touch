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
from legality.companion_rules import (
    COMPANION_CARD_NAMES,
    companion_is_banned_as_companion,
    get_companion_banned_note,
    get_companion_replacement_filter_note,
    get_companion_restriction_summary,
)


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

    collection_summary = context.get("collection_summary")
    if collection_summary:
        lines.extend(["", "## Collection loader status"])
        lines.append(f"- Collection mode: {getattr(collection_summary, 'mode', 'none')}")
        lines.append(f"- Collection source mode: {getattr(collection_summary, 'source_mode', 'none')}")
        lines.append(f"- Collection folder: {getattr(collection_summary, 'collection_folder', None) or 'None'}")
        lines.append(f"- Selected collection files: {len(getattr(collection_summary, 'selected_files', []) or [])}")
        for file_path in list(getattr(collection_summary, 'selected_files', []) or [])[:5]:
            lines.append(f"  - {Path(file_path).name}")
        lines.append(f"- Collection loaded: {'Yes' if getattr(collection_summary, 'loaded', False) else 'No'}")
        lines.append(f"- Total owned cards loaded: {getattr(collection_summary, 'total_cards', 0)}")
        lines.append(f"- Unique owned card names: {getattr(collection_summary, 'unique_cards', 0)}")
        lines.append(f"- Cards not found in Scryfall: {len(getattr(collection_summary, 'not_found_cards', []) or [])}")
    if completion:
        lines.extend(["", "## Completion notes"])
        lines.append(f"- Cards needed: {completion.cards_needed}")
        lines.append(f"- Build-up mode: {completion.build_up_label}")
        lines.extend(_bullet_list(completion.notes))
    return "\n".join(lines)


def build_diagnostics_debug_section(context: dict[str, Any]) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    original_runtime_config = context.get("original_runtime_config", runtime_config)
    philosophy_context = context.get("philosophy_context") or {}
    lines = [
        "# Debug — Diagnostics",
        "",
        f"Output mode: {runtime_config.output_mode}",
        f"Review direction: {runtime_config.review_direction}",
        f"Original review direction: {getattr(original_runtime_config, 'review_direction', runtime_config.review_direction)}",
        f"Auto-batch source: {'deck_size' if getattr(original_runtime_config, 'review_direction', '') == 'batch_auto' else 'not_applicable'}",
        f"Auto-batch detected deck size: {parsed.deck_card_count if getattr(original_runtime_config, 'review_direction', '') == 'batch_auto' else 'not_applicable'}",
        f"Prompt interaction mode: {runtime_config.prompt_interaction_mode}",
        f"Philosophy key: {getattr(runtime_config, 'philosophy_key', 'balanced_unknown')}",
        f"Guide preference: {getattr(runtime_config, 'guide_preference', 'either')}",
        f"Resolved philosophy lens: {philosophy_context.get('label', 'Balanced / Unknown')}",
        f"Resolved guide: {philosophy_context.get('guide_name') or 'No named guide selected'}",
        f"Build-up config: {runtime_config.build_up_config}",
        f"Cut-depth config: {runtime_config.cut_depth_config}",
        f"Auto-batch pool note: {runtime_config.cut_depth_config.get('auto_batch_pool_note', 'None')}",
        f"Collection mode: {getattr(runtime_config, 'collection_mode', 'none')}",
        f"Collection source mode: {getattr(runtime_config, 'collection_source_mode', 'none')}",
        f"Collection file/folder: {getattr(runtime_config, 'collection_file', '') or 'None'}",
        f"Selected collection files: {len(getattr(runtime_config, 'collection_files', ()) or ())}",
        "",
    ]
    if philosophy_context:
        lines.extend(render_philosophy_diagnostics_section(philosophy_context).splitlines())
        lines.extend([
            "",
            "## Philosophy Guidance Integration",
            "- v0.6.5.1 report guidance active: Yes",
            "- v0.6.5.3 subtype report summaries active: Yes",
            f"- Philosophy subtype summary active: {'Yes' if philosophy_context.get('subtype_summary_active') else 'No'}",
            f"- Report guidance summary available: {'Yes' if philosophy_context.get('report_guidance_summary') else 'No'}",
            f"- Protect / Question / Prefer fields available: {'Yes' if philosophy_context.get('protect_summary') and philosophy_context.get('question_summary') and philosophy_context.get('prefer_summary') else 'No'}",
            "- Scope: normal report guidance and diagnostics only",
            "- Cut scoring changed by philosophy: No",
            "- Replacement scoring changed by philosophy: No",
            "- Strategy detection changed by philosophy: No",
            "- Collection candidate matching changed by philosophy: No",
            "- Next philosophy scoring phase: v0.6.6 Philosophy-Aware Cut / Replacement Bias",
            "",
        ])

    collection_summary = context.get("collection_summary")
    if collection_summary:
        selected_files = list(getattr(collection_summary, 'selected_files', []) or [])
        lines.extend([
            "## Collection Loader Diagnostics",
            f"- Collection mode: {getattr(collection_summary, 'mode', 'none')}",
            f"- Collection source mode: {getattr(collection_summary, 'source_mode', 'none')}",
            f"- Collection folder: {getattr(collection_summary, 'collection_folder', None) or 'None'}",
            f"- Selected collection files: {len(selected_files)}",
        ])
        for file_path in selected_files[:12]:
            lines.append(f"  - {Path(file_path).name}")
        if len(selected_files) > 12:
            lines.append(f"  - ...and {len(selected_files) - 12} more")
        lines.extend([
            f"- At least one collection file exists: {'Yes' if getattr(collection_summary, 'file_exists', False) else 'No'}",
            f"- Loaded: {'Yes' if getattr(collection_summary, 'loaded', False) else 'No'}",
            f"- Total owned cards loaded: {getattr(collection_summary, 'total_cards', 0)}",
            f"- Unique owned card names: {getattr(collection_summary, 'unique_cards', 0)}",
            f"- Collection entries matched to Scryfall: {getattr(collection_summary, 'found_cards', 0)}",
            f"- Collection cards not found in Scryfall: {len(getattr(collection_summary, 'not_found_cards', []) or [])}",
            "- Candidate matching active: Yes — v0.6.4.3 matches loaded collection cards to current deck needs.",
            "",
            "### Collection Scryfall Resolution",
            f"- Exact-name matches: {getattr(collection_summary, 'exact_name_matches', 0)}",
            f"- Normalized-name matches: {getattr(collection_summary, 'normalized_name_matches', 0)}",
            f"- Set-code / collector-number matches: {getattr(collection_summary, 'set_collector_matches', 0)}",
            f"- Printed/alternate-name matches: {getattr(collection_summary, 'printed_or_alternate_name_matches', 0)}",
            f"- Unresolved entries: {getattr(collection_summary, 'unresolved_entries', 0)}",
        ])
        resolved_examples = list(getattr(collection_summary, 'resolved_name_examples', []) or [])
        not_found = list(getattr(collection_summary, 'not_found_cards', []) or [])
        warnings = list(getattr(collection_summary, 'parse_warnings', []) or [])
        if resolved_examples:
            lines.append("- Resolved alternate/export-name examples: " + " | ".join(resolved_examples[:8]))
        if not_found:
            lines.append("- Not-found examples: " + ", ".join(not_found[:12]))
            lines.append("- Not-found note: These entries were not fuzzy-corrected. Fix scanner/export spelling or confirm that the card exists in the local Scryfall data.")
        if warnings:
            lines.append("- Parse warning examples: " + " | ".join(warnings[:5]))
        lines.append("")

    collection_candidates = context.get("collection_candidates")
    if collection_candidates:
        lines.extend([
            "## Collection Candidate Matching Diagnostics",
            f"- Candidate matching active: {'Yes' if getattr(collection_candidates, 'candidate_matching_active', False) else 'No'}",
            f"- Collection mode: {getattr(collection_candidates, 'mode', 'none')}",
            f"- Strong owned candidates: {len(getattr(collection_candidates, 'strong_candidates', []) or [])}",
            f"- Possible owned candidates: {len(getattr(collection_candidates, 'possible_candidates', []) or [])}",
            f"- Shakeup-only candidates: {len(getattr(collection_candidates, 'shakeup_candidates', []) or [])}",
            f"- Rejected / filtered owned cards tracked: {len(getattr(collection_candidates, 'rejected_candidates', []) or [])}",
            "- Quality gate active: Yes — broad role overlap alone is not enough for Strong candidates.",
            "- Semantic gate active: Yes — support-only matches are not displayed as matched deck needs.",
            "- Role mapping hardening active: Yes — evasion/trample, board wipe, token, and combat categories use exact semantic gates.",
            "- Strong promotion gate active: Yes — standalone beaters, generic colorless bodies, and self-protection cards are usually capped at Possible.",
            "- v0.6.4.4 report/prompt integration active: Yes — candidates are review candidates, not automatic swaps.",
            "- Artifact-context cap active: Yes — artifact-context-dependent cards require artifact deck support before Strong.",
            "- Role-by-role gap tracking active: Yes — Possible and Shakeup candidates do not close strong-fit gaps.",
            f"- Strong candidates considered: {getattr(collection_candidates, 'strong_candidates_considered', 0)}",
            f"- Strong candidates accepted: {getattr(collection_candidates, 'strong_candidates_accepted', 0)}",
            f"- Downgraded to Possible: {getattr(collection_candidates, 'downgraded_to_possible', 0)}",
            f"- Downgraded to Shakeup: {getattr(collection_candidates, 'downgraded_to_shakeup', 0)}",
        ])
        no_fit = list(getattr(collection_candidates, 'no_strong_fit_categories', []) or [])
        notes = list(getattr(collection_candidates, 'notes', []) or [])
        quality_notes = list(getattr(collection_candidates, 'quality_gate_notes', []) or [])
        strong = list(getattr(collection_candidates, 'strong_candidates', []) or [])
        possible = list(getattr(collection_candidates, 'possible_candidates', []) or [])
        shakeup = list(getattr(collection_candidates, 'shakeup_candidates', []) or [])
        category_counts = list(getattr(collection_candidates, 'category_strong_fit_counts', []) or [])
        if category_counts:
            lines.append("- Strong-fit coverage by category: " + ", ".join(f"{cat}={count}" for cat, count in category_counts[:12]))
        if no_fit:
            lines.append("- Needs with no strong owned fit: " + ", ".join(no_fit[:12]))
        if notes:
            lines.append("- Candidate notes: " + " | ".join(notes[:4]))
        if quality_notes:
            lines.append("- Quality gate notes: " + " | ".join(quality_notes[:4]))
        downgrade_counts = list(getattr(collection_candidates, 'downgrade_reason_counts', []) or [])
        if downgrade_counts:
            lines.append("- Downgrade reasons: " + ", ".join(f"{reason}={count}" for reason, count in downgrade_counts[:8]))
        if strong:
            lines.append("- Strong owned examples: " + ", ".join(candidate.card_name for candidate in strong[:8]))
        if possible:
            lines.append("- Possible owned examples: " + ", ".join(candidate.card_name for candidate in possible[:8]))
        if shakeup:
            lines.append("- Shakeup examples: " + ", ".join(candidate.card_name for candidate in shakeup[:8]))
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
    ])
    companion_debug_names = list(dict.fromkeys(possible_companions + list(getattr(context.get('command_zone'), 'companion_names', []) or [])))
    if companion_debug_names:
        lines.extend(["", "## Companion Intake Diagnostics"])
        for name in companion_debug_names:
            lines.append(f"### {name}")
            lines.append(f"- Restriction summary: {get_companion_restriction_summary(name)}")
            lines.append(f"- Recommendation filter: {get_companion_replacement_filter_note(name)}")
            lines.append(f"- Banned/manual warning: {get_companion_banned_note(name) if companion_is_banned_as_companion(name) else 'None'}")
    lines.extend([
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
