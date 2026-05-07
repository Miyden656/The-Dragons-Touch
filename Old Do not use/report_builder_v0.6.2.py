"""Normal report builder for the modular cleanup version.

Patch Batch 5.1 goal:
- Preserve the normal report as a complete AI handoff packet.
- Include the full decklist.
- Include annotated card-role notes for every main-deck card so another AI can
  reason about cuts, protection, and replacements without losing context.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from app_io.output_writer import get_unique_output_path, write_text_file
from analysis.deck_building_philosophies import render_philosophy_guide_section


def _section(title: str) -> list[str]:
    return ["", f"## {title}", ""]


def _none_or_items(items: list[str], empty: str = "None found.") -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- {item}" for item in items]


def _format_cut_entries(entries, empty: str = "None found in this checkpoint.", limit: int = 12) -> list[str]:
    lines: list[str] = []
    if not entries:
        return [f"- {empty}"]
    for entry in entries[:limit]:
        lines.append(f"### {entry.card_name}")
        # Protected entries may now use keep-oriented labels in cut_type. Keep the
        # field name generic so the report does not imply the pilot must cut it.
        label = getattr(entry, "cut_type", "Review candidate")
        if "protected" in str(label).lower() or "keep" in str(label).lower():
            lines.append(f"- Review label: {label}")
        else:
            lines.append(f"- Cut type: {label}")
        lines.append(f"- Confidence: {entry.cut_confidence}")
        lines.append(f"- Replaceability score: {entry.score}")
        if entry.reasons:
            lines.append(f"- Reason: {entry.reasons[0]}")
            for reason in entry.reasons[1:4]:
                lines.append(f"  - {reason}")
        lines.append("")
    return lines


def _card_name_key(name: str) -> str:
    return str(name).strip().lower()


def _card_roles_by_name(context: dict[str, Any]) -> dict[str, Any]:
    role_summary = context.get("role_summary")
    entries = getattr(role_summary, "card_roles", []) if role_summary else []
    return {_card_name_key(getattr(entry, "card_name", "")): entry for entry in entries}


def _plan_fit_by_name(context: dict[str, Any]) -> dict[str, Any]:
    plan_fit = context.get("plan_fit_summary")
    result: dict[str, Any] = {}
    if not plan_fit:
        return result
    for collection_name in ("strong_synergy_cards", "possible_off_plan_cards", "manual_review_cards", "protected_cards"):
        for entry in getattr(plan_fit, collection_name, []) or []:
            name = getattr(entry, "card_name", "")
            if name:
                result[_card_name_key(name)] = entry
    return result


def _review_status_by_name(context: dict[str, Any]) -> dict[str, tuple[str, Any]]:
    possible = context.get("possible_cuts")
    result: dict[str, tuple[str, Any]] = {}
    if not possible:
        return result
    buckets = [
        ("Required cut candidate", getattr(possible, "required_cut_candidates", []) or []),
        ("Optional optimization candidate", getattr(possible, "optional_cut_candidates", []) or []),
        ("Manual review candidate", getattr(possible, "manual_review_candidates", []) or []),
        ("Protected / low cut pressure", getattr(possible, "protected_from_cut", []) or []),
    ]
    for label, entries in buckets:
        for entry in entries:
            name = getattr(entry, "card_name", "")
            if name:
                result[_card_name_key(name)] = (label, entry)
    return result


def _format_role_tags(entry: Any) -> str:
    tags = list(getattr(entry, "detected_roles", []) or [])
    if not tags:
        return "None detected"
    return ", ".join(tags[:14]) + ("..." if len(tags) > 14 else "")


def _format_card_types(entry: Any) -> str:
    type_line = getattr(entry, "type_line", "") or ""
    if type_line:
        return type_line
    types = list(getattr(entry, "card_types", []) or [])
    return ", ".join(types) if types else "Unknown type"


def _format_plan_fit(entry: Any | None) -> tuple[str, list[str]]:
    if not entry:
        return "No specific plan-fit note generated", []
    plan_fit = getattr(entry, "plan_fit", "") or "Plan-fit note"
    reasons = list(getattr(entry, "reasons", []) or [])
    return str(plan_fit), reasons[:4]


def _format_review_status(status: tuple[str, Any] | None) -> tuple[str, list[str]]:
    if not status:
        return "No explicit cut/review/protection status generated", []
    bucket, entry = status
    label = getattr(entry, "cut_type", "Review candidate")
    confidence = getattr(entry, "cut_confidence", "Unknown")
    score = getattr(entry, "score", "Unknown")
    reasons = list(getattr(entry, "reasons", []) or [])
    headline = f"{bucket}: {label}; confidence {confidence}; score {score}"
    return headline, reasons[:4]


def _format_quantity_decklist(cards: Iterable[str]) -> list[str]:
    counts = Counter(cards)
    return [f"{qty} {name}" for name, qty in sorted(counts.items(), key=lambda item: item[0].lower())]


def _build_full_decklist_section(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    lines = _section("Full Decklist / Main Deck Cards for AI Review")
    lines.extend([
        "> This section is included so this report can be pasted into another AI or deck-review tool without losing the actual card list.",
        "> The pilot still makes the final keep/cut/build decisions.",
        "",
        f"- Main deck card count: {parsed.deck_card_count}",
        f"- Unique main deck cards: {len(parsed.unique_cards)}",
        "",
    ])

    cards_by_section = getattr(parsed, "cards_by_section", {}) or {}
    if cards_by_section:
        for section_name, cards in cards_by_section.items():
            if not cards:
                continue
            lines.append(f"### {section_name}")
            lines.append("```text")
            lines.extend(_format_quantity_decklist(cards))
            lines.append("```")
            lines.append("")
    else:
        lines.append("```text")
        lines.extend(_format_quantity_decklist(getattr(parsed, "cards", []) or []))
        lines.append("```")
        lines.append("")
    return lines


def _build_annotated_decklist_section(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    roles_by_name = _card_roles_by_name(context)
    plan_by_name = _plan_fit_by_name(context)
    review_by_name = _review_status_by_name(context)
    card_sections = getattr(parsed, "card_manual_sections", {}) or {}
    counts = Counter(getattr(parsed, "cards", []) or [])

    lines = _section("Annotated Decklist / Card Role Notes for AI Review")
    lines.extend([
        "> These notes explain what The Dragon's Touch currently believes each main-deck card is doing.",
        "> They are generated context for AI/human review, not final truth. The pilot should correct strategy, protect cards that matter, and make the final decisions.",
        "",
    ])

    if not counts:
        lines.append("- No main-deck cards were available to annotate.")
        return lines

    for card_name in sorted(counts, key=str.lower):
        key = _card_name_key(card_name)
        role_entry = roles_by_name.get(key)
        plan_entry = plan_by_name.get(key)
        status = review_by_name.get(key)
        plan_label, plan_reasons = _format_plan_fit(plan_entry)
        review_label, review_reasons = _format_review_status(status)
        sections = sorted(card_sections.get(card_name, [])) if hasattr(card_sections, "get") else []

        lines.append(f"### {card_name}")
        lines.append(f"- Quantity: {counts[card_name]}")
        if sections:
            lines.append(f"- Deck section(s): {', '.join(sections)}")
        if role_entry:
            mana_value = getattr(role_entry, "mana_value", None)
            if mana_value is not None:
                lines.append(f"- Mana value: {mana_value}")
            lines.append(f"- Card type / type line: {_format_card_types(role_entry)}")
            lines.append(f"- Role tags: {_format_role_tags(role_entry)}")
            short_reason = getattr(role_entry, "short_reason", "") or ""
            if short_reason:
                lines.append(f"- Role note: {short_reason}")
        else:
            lines.append("- Role tags: No role tags available for this checkpoint.")
        lines.append(f"- Plan-fit note: {plan_label}")
        for reason in plan_reasons:
            lines.append(f"  - {reason}")
        lines.append(f"- Cut/review/protection status: {review_label}")
        for reason in review_reasons:
            lines.append(f"  - {reason}")
        lines.append("")
    return lines


def _build_reference_cards_section(context: dict[str, Any]) -> list[str]:
    parsed = context["parsed_deck"]
    lines = _section("Reference / Non-Mainboard / Ignored Cards")
    lines.extend([
        "> These cards were detected outside the counted main deck or ignored for deck-size counting.",
        "> Review them manually if they are intended as companion, sideboard, maybeboard, token, attraction, sticker, or reference-only cards.",
        "",
        f"- Reference/non-mainboard card count: {parsed.reference_card_count}",
        f"- Ignored/unparsed line count: {len(parsed.ignored_lines)}",
        "",
    ])

    reference_by_section = getattr(parsed, "reference_cards_by_section", {}) or {}
    if reference_by_section:
        for section_name, cards in reference_by_section.items():
            lines.append(f"### {section_name}")
            if cards:
                lines.append("```text")
                lines.extend(_format_quantity_decklist(cards))
                lines.append("```")
            else:
                lines.append("- None")
            lines.append("")
    else:
        reference_cards = getattr(parsed, "reference_cards", []) or []
        if reference_cards:
            lines.append("```text")
            lines.extend(_format_quantity_decklist(reference_cards))
            lines.append("```")
            lines.append("")
        else:
            lines.append("- None detected.")
            lines.append("")

    if parsed.ignored_lines:
        lines.append("### Ignored / Unparsed Lines")
        lines.append("```text")
        lines.extend(str(line) for line in parsed.ignored_lines[:50])
        lines.append("```")
        lines.append("")
    return lines


def build_normal_report(context: dict[str, Any]) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    command_zone = context["command_zone"]
    legality = context["legality"]
    role_summary = context["role_summary"]
    strategy = context["strategy_summary"]
    plan_fit = context["plan_fit_summary"]
    bracket = context["bracket_summary"]
    cut_pressure = context["cut_pressure"]
    possible = context["possible_cuts"]
    replacement = context["replacement_needs"]
    completion = context.get("deck_completion")

    lines: list[str] = [
        f"# MTG Commander Deck Helper Report — {parsed.commander_name}",
        "",
        f"Generated by {context.get('version_label', 'The Dragon\'s Touch modular cleanup')}.",
        "",
        "> Cleanup note: this modular report is a refactor checkpoint. Continue comparing against known-good outputs before replacing your stable backup.",
    ]

    lines += _section("Run Settings")
    lines.extend([
        f"- Output mode: {runtime_config.output_mode}",
        f"- Review direction: {runtime_config.review_direction}",
        f"- Prompt interaction mode: {runtime_config.prompt_interaction_mode}",
    ])
    if runtime_config.review_direction == "build_up":
        lines.append(f"- Build-up mode: {runtime_config.build_up_config.get('label', 'Not applicable')}")
    else:
        lines.append(f"- Cut depth mode: {runtime_config.cut_depth_config.get('mode', 'normal')}")
        lines.append(f"- Optional cut target: {runtime_config.cut_depth_config.get('optional_cut_target', 5)}")

    philosophy_context = context.get("philosophy_context")
    if philosophy_context:
        lines.append("")
        lines.append(render_philosophy_guide_section(philosophy_context).rstrip())

    lines += _section("Deck / Command Zone")
    lines.extend([
        f"- Deck file: `{parsed.deck_file}`",
        f"- Main deck card count: {parsed.deck_card_count}",
        f"- Unique main deck cards: {len(parsed.unique_cards)}",
        f"- Commander(s): {', '.join(command_zone.commander_names) if command_zone.commander_names else 'Unknown'}",
        f"- Companion(s): {', '.join(command_zone.companion_names) if command_zone.companion_names else 'None'}",
        f"- Command-zone rule detected: {command_zone.command_zone_rule_detected}",
        f"- Commander color identity: {command_zone.commander_color_identity_text}",
        f"- Commander type line: {command_zone.commander_type_line}",
    ])

    lines += _section("Legality Checkpoint")
    lines.extend([
        f"- Deck size legal: {'Yes' if legality.deck_size_legal else 'No'}",
        f"- Cards not found in Scryfall: {len(legality.cards_not_found)}",
        f"- Color identity violations: {len(legality.color_identity_violations)}",
        f"- Banned cards detected: {len(legality.banned_cards) + len(legality.banned_commanders)}",
        f"- Illegal duplicate cards: {len(legality.illegal_duplicate_cards)}",
    ])
    if legality.cards_not_found:
        lines.append("- Manual review cards: " + ", ".join(legality.cards_not_found[:12]))
    if legality.color_identity_violations:
        lines.append("- Color identity violation examples:")
        for item in legality.color_identity_violations[:8]:
            lines.append(f"  - {item.get('card_name')}: {item.get('card_color_identity')} outside {item.get('commander_color_identity')}")
    if legality.illegal_duplicate_cards:
        lines.append("- Illegal duplicate examples:")
        for item in legality.illegal_duplicate_cards[:8]:
            lines.append(f"  - {item.get('card_name')}: {item.get('quantity')} copies")

    # AI handoff packet: full list + per-card notes must appear before strategy/cut summaries.
    lines.extend(_build_full_decklist_section(context))
    lines.extend(_build_annotated_decklist_section(context))
    lines.extend(_build_reference_cards_section(context))

    lines += _section("Strategy Read")
    lines.extend([
        f"- Primary strategy: {strategy.primary_strategy}",
        f"- Secondary strategy: {strategy.secondary_strategy}",
        f"- Strategy confidence: {strategy.confidence}",
    ])
    if strategy.primary_candidate:
        lines.append(f"- Primary evidence: {'; '.join(strategy.primary_candidate.evidence) if strategy.primary_candidate.evidence else strategy.primary_candidate.gate_reason}")
    if strategy.core_synergy_packages:
        lines.append("- Core synergy packages:")
        for package in strategy.core_synergy_packages:
            lines.append(f"  - {package}")
    if strategy.warnings:
        lines.append("- Strategy warnings:")
        for warning in strategy.warnings:
            lines.append(f"  - {warning}")

    lines += _section("Role Snapshot")
    for tag, count in role_summary.role_counts.most_common(15):
        lines.append(f"- {tag}: {count}")

    lines += _section("Strong Plan-Fit Examples")
    if plan_fit.strong_synergy_cards:
        for entry in plan_fit.strong_synergy_cards[:12]:
            reason = entry.reasons[0] if entry.reasons else entry.plan_fit
            lines.append(f"- {entry.card_name}: {reason}")
    else:
        lines.append("- None found in this checkpoint.")

    lines += _section("Possible Off-Plan / Manual Review Examples")
    if plan_fit.possible_off_plan_cards:
        for entry in plan_fit.possible_off_plan_cards[:12]:
            reason = entry.reasons[0] if entry.reasons else entry.plan_fit
            lines.append(f"- {entry.card_name}: {reason}")
    else:
        lines.append("- None found in this checkpoint.")

    lines += _section("Bracket / Table-Fit Pressure")
    lines.extend([
        f"- Estimated pressure: {bracket.estimated_bracket}",
        f"- Pressure level: {bracket.pressure_level}",
        f"- Pressure cards found: {len(bracket.pressure_cards)}",
    ])
    lines.extend(_none_or_items(bracket.notes))
    if bracket.pressure_cards:
        lines.append("- Pressure card examples:")
        for entry in bracket.pressure_cards[:12]:
            lines.append(f"  - {entry.card_name}: {entry.pressure_type}")

    lines += _section("Cut Pressure Review")
    lines.extend([
        f"- Deck size status: {cut_pressure.status}",
        f"- Current deck size: {cut_pressure.deck_card_count}",
        f"- Required cuts: {cut_pressure.required_cuts}",
        f"- Short cards: {cut_pressure.short_cards}",
        f"- Optional cut target: {cut_pressure.optional_cut_target}",
        f"- Cut mode: {cut_pressure.cut_mode}",
    ])
    lines.extend(_none_or_items(cut_pressure.notes + possible.notes))

    lines += _section("Required Cut Candidates")
    lines.extend(_format_cut_entries(possible.required_cut_candidates, "No required cut candidates in this checkpoint."))

    lines += _section("Optional Optimization Cut Candidates")
    lines.extend(_format_cut_entries(possible.optional_cut_candidates, "No optional cut candidates in this checkpoint."))

    lines += _section("Manual Review Candidates")
    lines.extend(_format_cut_entries(possible.manual_review_candidates, "No manual-review cut candidates in this checkpoint.", limit=10))

    lines += _section("Protected From Cut Examples")
    lines.extend(_format_cut_entries(possible.protected_from_cut, "No protected-card examples in this checkpoint.", limit=10))

    lines += _section("Replacement / Addition Needs")
    if replacement.priority_categories:
        for category in replacement.priority_categories:
            lines.append(f"- {category}")
    else:
        lines.append("- No urgent replacement category was detected by the checkpoint heuristics.")
    for note in replacement.notes:
        lines.append(f"- Note: {note}")
    if completion and completion.addition_first:
        lines.append("")
        lines.append("### Deck Completion Notes")
        lines.append(f"- Cards needed to reach 100: {completion.cards_needed}")
        lines.append(f"- Build-up mode: {completion.build_up_label}")
        for note in completion.notes:
            lines.append(f"- {note}")

    lines += _section("Parser Hygiene")
    lines.extend([
        f"- Reference/non-mainboard cards ignored: {parsed.reference_card_count}",
        f"- Ignored/unparsed lines: {len(parsed.ignored_lines)}",
    ])
    if parsed.ignored_lines:
        lines.append("- Ignored line examples:")
        for ignored in parsed.ignored_lines[:10]:
            lines.append(f"  - `{ignored}`")

    return "\n".join(lines).rstrip() + "\n"


def write_normal_report(deck_folder: Path, deck_name: str, context: dict[str, Any]) -> Path:
    path = get_unique_output_path(deck_folder, f"{deck_name}_deck_report", ".md")
    write_text_file(path, build_normal_report(context))
    return path
