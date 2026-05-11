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
from analysis.deck_building_philosophies import render_philosophy_guide_section  # v0.6.5.3 renders subtype summaries
from legality.companion_rules import (
    OFFICIAL_COMPANION_CARD_NAMES as COMPANION_CARD_NAMES,
    companion_is_banned_as_companion,
    get_companion_banned_note,
    get_companion_intake_lines,
    get_companion_replacement_filter_note,
    get_companion_restriction_summary,
)


# Companion card names are imported from legality.companion_rules.


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


def _build_companion_verification_warning(context: dict[str, Any]) -> list[str]:
    candidates = _possible_companion_names_from_reference(context)
    if not candidates:
        return []

    lines = _section("Companion Intake Check")
    lines.extend([
        "The report detected one or more possible companion cards in **Reference / Non-Mainboard / Ignored Cards**.",
        "These cards are not treated as confirmed companions until the pilot confirms them.",
        "",
        "Detected possible companion(s):",
    ])
    lines.extend(f"- {name}" for name in candidates)
    lines.extend([
        "",
        "Before any final recommendations, confirm one for each listed card:",
        "1. This card is my companion.",
        "2. This card is sideboard / maybeboard only.",
        "3. This card is reference-only.",
        "",
        "If confirmed as companion, apply the appropriate companion legality, cut protection, replacement filter, and card recommendation restriction.",
    ])

    for name in candidates:
        lines.extend(["", f"### {name}"])
        lines.extend(get_companion_intake_lines(name))

    lines.extend([
        "",
        "> Patch note: confirmed companions are checked where implemented. Unconfirmed reference companions remain a verification checkpoint until the pilot confirms companion status.",
    ])
    return lines


def _build_companion_legality_section(context: dict[str, Any]) -> list[str]:
    command_zone = context.get("command_zone")
    legality = context.get("legality")
    companion_names = list(getattr(command_zone, "companion_names", []) or [])
    possible_reference = list(getattr(command_zone, "possible_reference_companion_names", []) or [])
    notes = list(getattr(legality, "companion_legality_notes", []) or [])
    filter_notes = list(getattr(legality, "companion_replacement_filter_notes", []) or [])
    violations = list(getattr(legality, "companion_legality_violations", []) or [])
    manual_reviews = list(getattr(legality, "manual_review_companion_cards", []) or [])

    if not companion_names and not possible_reference and not notes and not filter_notes:
        return []

    lines = _section("Companion Legality / Replacement Filter")

    if companion_names:
        lines.append(f"Confirmed companion(s): {', '.join(companion_names)}")
        for name in companion_names:
            lines.append(f"- {get_companion_restriction_summary(name)}")
            lines.append(f"- {get_companion_replacement_filter_note(name)}")
            if companion_is_banned_as_companion(name):
                lines.append(f"- Companion legality warning: {get_companion_banned_note(name)}")
    else:
        lines.append("Confirmed companion(s): None detected in a Companion section.")

    if possible_reference:
        lines.append(f"Possible reference companion(s): {', '.join(possible_reference)}")
        lines.append("Possible reference companions require pilot confirmation before companion restrictions are enforced.")

    checked = getattr(legality, "companion_legality_checked", False)
    legal = getattr(legality, "companion_legality_legal", None)
    lines.append(f"Companion legality checked: {'Yes' if checked else 'No'}")
    if checked:
        if legal is True:
            result_text = "Pass"
        elif violations:
            result_text = "Violation found by automated companion check"
        elif manual_reviews:
            result_text = "Manual review required — automated restriction check is incomplete for this companion"
        else:
            result_text = "Needs review — automated companion result was inconclusive"
        lines.append(f"Companion legality result: {result_text}")
        lines.append(f"Companion legality violations found by automation: {len(violations)}")
        if manual_reviews:
            lines.append(f"Manual companion reviews required: {len(manual_reviews)}")

    if notes:
        lines.append("")
        lines.append("Companion notes:")
        lines.extend(f"- {note}" for note in notes)

    if filter_notes:
        lines.append("")
        lines.append("Companion-aware recommendation filters:")
        lines.extend(f"- {note}" for note in filter_notes)

    if violations:
        lines.append("")
        lines.append("Companion legality violations:")
        for item in violations[:20]:
            mv = item.get("mana_value")
            mv_text = f"; mana value {mv:g}" if isinstance(mv, (int, float)) else ""
            lines.append(f"- {item.get('card_name')} x{item.get('quantity', 1)}{mv_text}: {item.get('reason')}")

    if manual_reviews:
        lines.append("")
        lines.append("Manual companion reviews:")
        for item in manual_reviews[:20]:
            lines.append(f"- {item.get('card_name')}: {item.get('reason')}")

    if possible_reference and not companion_names:
        lines.append("")
        lines.append("> Replacement filtering is not automatically enforced for reference-only companion candidates until the pilot confirms companion status in the guided review.")

    return lines


def _section(title: str) -> list[str]:
    return ["", f"## {title}", ""]


def _none_or_items(items: list[str], empty: str = "None found.") -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- {item}" for item in items]


def _is_structured_watch_reason(reason: str) -> bool:
    prefixes = (
        "Protected Label:",
        "Initial flag:",
        "Philosophy adjustment:",
        "Final verdict:",
        "Why this matters:",
        "Review instruction:",
        "Supporting note:",
    )
    return str(reason).startswith(prefixes)


def _format_cut_entries(entries, empty: str = "None found in this checkpoint.", limit: int = 12) -> list[str]:
    lines: list[str] = []
    if not entries:
        return [f"- {empty}"]
    for entry in entries[:limit]:
        lines.append(f"### {entry.card_name}")
        # Protected entries may now use keep-oriented labels in cut_type. Keep the
        # field name generic so the report does not imply the pilot must cut it.
        label = getattr(entry, "cut_type", "Review candidate")
        is_protected_label = "protected" in str(label).lower() or "keep" in str(label).lower() or getattr(entry, "protected", False)
        if is_protected_label:
            lines.append(f"- Review label: {label}")
        else:
            lines.append(f"- Cut type: {label}")
        lines.append(f"- Confidence: {entry.cut_confidence}")
        lines.append(f"- Replaceability score: {entry.score}")
        reasons = list(getattr(entry, "reasons", []) or [])
        if reasons:
            # v0.6.6.3.1: protected/watch entries use structured reason lines.
            # Show all key fields instead of truncating before Why this matters / Review instruction.
            if any(_is_structured_watch_reason(reason) for reason in reasons):
                lines.append("- Reason:")
                for reason in reasons[:8]:
                    lines.append(f"  - {reason}")
            else:
                lines.append(f"- Reason: {reasons[0]}")
                for reason in reasons[1:4]:
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
    if any(_is_structured_watch_reason(reason) for reason in reasons):
        return headline, reasons[:8]
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


def _format_collection_candidate(candidate: Any) -> list[str]:
    lines = [f"### {getattr(candidate, 'card_name', 'Unknown card')}"]
    lines.append(f"- Quantity owned: {getattr(candidate, 'quantity_owned', 0)}")
    lines.append(f"- Confidence: {getattr(candidate, 'confidence', 'Unknown')}")
    lines.append(f"- Fit type: {getattr(candidate, 'fit_type', 'Collection candidate')}")
    quality_gate = getattr(candidate, 'quality_gate', '')
    if quality_gate:
        lines.append(f"- Quality gate: {quality_gate}")
    matched = list(getattr(candidate, 'matched_needs', []) or [])
    if matched:
        lines.append(f"- Matches deck need(s): {', '.join(matched[:6])}")
    strong_fits = list(getattr(candidate, 'strong_fit_needs', []) or [])
    if strong_fits and getattr(candidate, 'confidence', '').lower().startswith('strong'):
        lines.append(f"- Strong-fit role(s): {', '.join(strong_fits[:6])}")
    roles = list(getattr(candidate, 'role_tags', []) or [])
    if roles:
        lines.append(f"- Detected collection roles: {', '.join(roles[:10])}")
    mana_value = getattr(candidate, 'mana_value', None)
    if mana_value is not None:
        lines.append(f"- Mana value: {mana_value}")
    colors = list(getattr(candidate, 'color_identity', []) or [])
    if colors:
        lines.append(f"- Color identity: {'/'.join(colors)}")
    reason = getattr(candidate, 'reason', '')
    if reason:
        lines.append(f"- Reason: {reason}")
    philosophy_matches = list(getattr(candidate, 'philosophy_bias_matches', []) or [])
    philosophy_note = getattr(candidate, 'philosophy_bias_note', '')
    philosophy_nudge = getattr(candidate, 'philosophy_replacement_nudge', 0)
    if philosophy_matches and philosophy_nudge:
        lines.append(f"- Philosophy replacement fit: {', '.join(philosophy_matches[:6])}")
        philosophy_explanation = getattr(candidate, 'philosophy_bias_explanation', '')
        if philosophy_explanation:
            lines.append(f"  - Why this fits the selected lens: {philosophy_explanation}")
        if philosophy_note:
            lines.append(f"  - {philosophy_note}")
        lines.append("  - Still not automatic because collection fit, strategy fit, quality gates, legality, companion rules, and pilot intent still decide the final recommendation.")
    warnings = list(getattr(candidate, 'warnings', []) or [])
    for warning in warnings[:3]:
        lines.append(f"  - Warning: {warning}")
    swap_guidance = list(getattr(candidate, 'swap_guidance', []) or [])
    if swap_guidance:
        lines.append("- Early swap guidance:")
        for item in swap_guidance[:4]:
            lines.append(f"  - {item}")
    sources = list(getattr(candidate, 'source_files', []) or [])
    if sources:
        lines.append("- Source file(s): " + ", ".join(Path(src).name for src in sources[:3]))
    lines.append("")
    return lines


def _build_collection_pull_section(context: dict[str, Any]) -> list[str]:
    summary = context.get("collection_candidates")
    collection_summary = context.get("collection_summary")
    if not summary or not getattr(summary, "active", False):
        return []

    lines = _section("Collection Pull Candidates")
    lines.extend([
        f"- Collection mode: {getattr(summary, 'mode', 'none')}",
        f"- Collection loaded: {'Yes' if getattr(summary, 'collection_loaded', False) else 'No'}",
        f"- Total owned cards loaded: {getattr(summary, 'total_owned_cards', 0)}",
        f"- Unique owned card names: {getattr(summary, 'unique_owned_cards', 0)}",
        f"- Selected collection files: {len(getattr(collection_summary, 'selected_files', []) or []) if collection_summary else 0}",
        f"- Philosophy-aware replacement bias active: {'Yes' if getattr(summary, 'replacement_bias_active', False) else 'No'}",
        f"- Replacement bias lens: {getattr(summary, 'replacement_bias_lens', 'Balanced / Unknown')}",
        f"- Replacement-biased owned candidates evaluated: {getattr(summary, 'replacement_bias_candidates_evaluated', 0)}",
        f"- Replacement-biased owned candidates nudged: {getattr(summary, 'replacement_bias_candidates_nudged', getattr(summary, 'replacement_bias_adjusted_cards', 0))}",
        f"- Replacement-biased owned candidates not nudged: {getattr(summary, 'replacement_bias_candidates_not_nudged', 0)}",
        "",
        "> Collection candidates are only shown when they appear to support the current strategy, replacement needs, color identity, and implemented companion filters.",
        "> Strong candidates must pass a semantic fit gate. Broad utility or support-only overlap is not enough.",
        "> Role mapping hardening is active: evasion/trample, board wipe, token, and combat categories require exact semantic matches.",
        "> Strong promotion gate is active: standalone beaters, generic colorless bodies, and self-protection cards are usually capped at Possible.",
        "> v0.6.4.4 prompt/report integration is active: owned cards are review candidates, not automatic swaps.",
        "> v0.6.6.6 philosophy-bias lock is active: candidate presentation may be lightly nudged, overbroad cut-bias aliases are suppressed, visibility counters/examples are recorded, companion manual-review wording is clarified, and the system still cannot force bad recommendations or override collection-only mode.",
        "> Collection gaps are tracked role-by-role. Possible and Shakeup cards do not close a strong-fit gap.",
        "> If no strong owned candidate exists, The Dragon's Touch should say so instead of forcing a bad recommendation.",
    ])

    rb_examples = list(getattr(summary, 'replacement_bias_examples', []) or [])
    rb_no_match = list(getattr(summary, 'replacement_bias_no_match_examples', []) or [])
    rb_no_evidence = list(getattr(summary, 'replacement_bias_no_evidence_examples', []) or [])
    if getattr(summary, 'replacement_bias_active', False):
        lines.append("")
        lines.append("### Philosophy-Aware Replacement Bias Visibility / QA")
        lines.append(f"- Candidates evaluated for replacement bias: {getattr(summary, 'replacement_bias_candidates_evaluated', 0)}")
        lines.append(f"- Candidates nudged by philosophy: {getattr(summary, 'replacement_bias_candidates_nudged', getattr(summary, 'replacement_bias_adjusted_cards', 0))}")
        lines.append(f"- Candidates not nudged: {getattr(summary, 'replacement_bias_candidates_not_nudged', 0)}")
        lines.append(f"- No replacement-bias role match: {getattr(summary, 'replacement_bias_candidates_no_match', 0)}")
        lines.append(f"- Bias role matched but lacked deck evidence: {getattr(summary, 'replacement_bias_candidates_no_deck_evidence', 0)}")
        if rb_examples:
            lines.append("- Replacement bias examples: " + ", ".join(rb_examples[:8]))
        if rb_no_match:
            lines.append("- No replacement-bias match examples: " + ", ".join(rb_no_match[:8]))
        if rb_no_evidence:
            lines.append("- Matched lens but no deck-fit evidence examples: " + ", ".join(rb_no_evidence[:8]))
        lines.append("- Safety boundary: philosophy replacement fit is a presentation/order nudge only, not an automatic swap or quality-gate override.")

    notes = list(getattr(summary, 'notes', []) or [])
    if notes:
        lines.append("")
        lines.append("### Collection Candidate Notes")
        for note in notes[:6]:
            lines.append(f"- {note}")

    strong = list(getattr(summary, 'strong_candidates', []) or [])
    possible = list(getattr(summary, 'possible_candidates', []) or [])
    shakeup = list(getattr(summary, 'shakeup_candidates', []) or [])
    no_fit = list(getattr(summary, 'no_strong_fit_categories', []) or [])
    replacement_needs = context.get("replacement_needs")
    priority_categories = list(getattr(replacement_needs, "priority_categories", []) or [])
    actionable_categories = [
        category for category in priority_categories
        if category and not str(category).lower().startswith("no urgent") and not str(category).lower().startswith("note:")
    ]

    lines.append("")
    lines.append("### Strong Owned Candidates")
    lines.append("> These are owned cards that appear to directly satisfy a current need and support the deck's specific plan. They are still review candidates, not automatic swaps.")
    lines.append("> Use them as the best owned fits to review first, then confirm the pilot actually wants that role changed.")
    if strong:
        for candidate in strong[:10]:
            lines.extend(_format_collection_candidate(candidate))
    else:
        lines.append("- No strong owned candidates found for the current deck needs.")
        if getattr(summary, 'mode', 'none') == 'only':
            lines.append("- Collection-only mode is active, so no outside-card replacement is presented as owned.")

    lines.append("")
    lines.append("### Possible Owned Candidates")
    lines.append("> These are legal or role-relevant owned cards that need pilot review. They may not be clear upgrades over the current list.")
    lines.append("> They should not be presented as upgrades unless the pilot chooses that direction.")
    if possible:
        for candidate in possible[:10]:
            lines.extend(_format_collection_candidate(candidate))
    else:
        lines.append("- No possible owned candidates found beyond the strong/shakeup buckets.")

    lines.append("")
    lines.append("### Collection Gaps")
    if not actionable_categories:
        lines.append("- No active replacement category was available to evaluate for strong collection fits.")
        lines.append("- The collection may still show shakeup candidates, but those are not presented as upgrades.")
    elif no_fit:
        lines.append("The selected collection did not contain a **strong** owned fit for:")
        for category in no_fit[:12]:
            lines.append(f"- {category}")
        lines.append("")
        lines.append("> Possible or shakeup cards may still exist for these categories, but they did not pass the semantic strong-fit gate.")
    else:
        lines.append("- Every current replacement category had at least one visible Strong owned fit after strict role-by-role quality gating.")
        lines.append("- Still confirm with the pilot before treating these as actual swaps.")

    lines.append("")
    lines.append("### Best Available Collection Shakeup Candidates")
    if shakeup:
        lines.append("> These are not guaranteed upgrades. They are the best available experiments from the selected collection pool if the pilot wants a shakeup.")
        for candidate in shakeup[:8]:
            lines.extend(_format_collection_candidate(candidate))
    else:
        lines.append("- No shakeup-only candidates found.")

    return lines


def build_normal_report(context: dict[str, Any]) -> str:
    parsed = context["parsed_deck"]
    runtime_config = context["runtime_config"]
    original_runtime_config = context.get("original_runtime_config", runtime_config)
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
    if getattr(original_runtime_config, "review_direction", "") == "batch_auto":
        lines.extend([
            "- Auto-batch source: deck size",
            f"- Auto-batch detected deck size: {parsed.deck_card_count}",
            f"- Auto-batch applied review direction: {runtime_config.review_direction}",
        ])
        if runtime_config.review_direction == "build_up":
            lines.append(f"- Auto-batch cards needed to reach 100: {runtime_config.build_up_config.get('cards_needed', max(0, 100 - parsed.deck_card_count))}")
        else:
            note = runtime_config.cut_depth_config.get("auto_batch_pool_note")
            if note:
                lines.append(f"- Auto-batch pool note: {note}")
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
        f"- Possible reference companion(s): {', '.join(getattr(command_zone, 'possible_reference_companion_names', []) or []) if getattr(command_zone, 'possible_reference_companion_names', []) else 'None'}",
        f"- Companion note: {getattr(command_zone, 'companion_note', 'No companion detected.')} ",
        f"- Command-zone rule detected: {command_zone.command_zone_rule_detected}",
        f"- Commander color identity: {command_zone.commander_color_identity_text}",
        f"- Commander type line: {command_zone.commander_type_line}",
    ])

    lines.extend(_build_companion_verification_warning(context))
    lines.extend(_build_companion_legality_section(context))

    lines += _section("Legality Checkpoint")
    lines.extend([
        f"- Deck size legal: {'Yes' if legality.deck_size_legal else 'No'}",
        f"- Cards not found in Scryfall: {len(legality.cards_not_found)}",
        f"- Color identity violations: {len(legality.color_identity_violations)}",
        f"- Banned cards detected: {len(legality.banned_cards) + len(legality.banned_commanders)}",
        f"- Illegal duplicate cards: {len(legality.illegal_duplicate_cards)}",
        f"- Companion legality checked: {'Yes' if getattr(legality, 'companion_legality_checked', False) else 'No'}",
        f"- Companion legality violations: {len(getattr(legality, 'companion_legality_violations', []) or [])}",
        f"- Manual companion reviews: {len(getattr(legality, 'manual_review_companion_cards', []) or [])}",
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
    companion_filter_notes = list(getattr(legality, "companion_replacement_filter_notes", []) or [])
    if companion_filter_notes:
        lines.append("")
        lines.append("### Companion-Aware Recommendation Filters")
        for note in companion_filter_notes:
            lines.append(f"- {note}")
    if completion and completion.addition_first:
        lines.append("")
        lines.append("### Deck Completion Notes")
        lines.append(f"- Cards needed to reach 100: {completion.cards_needed}")
        lines.append(f"- Build-up mode: {completion.build_up_label}")
        for note in completion.notes:
            lines.append(f"- {note}")

    lines.extend(_build_collection_pull_section(context))

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
