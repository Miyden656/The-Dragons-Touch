from __future__ import annotations
from replacements.replacement_candidates import ensure_replacement_candidate_summary_from_context
from reports.report_postprocessors import apply_normal_report_postprocessors, _v0952_should_show_exact_preview, _v09551_exact_preview_categories  # v1.5.24 safe postprocessor batch
"""Normal report builder for the modular cleanup version.

Patch Batch 5.1 goal:
- Preserve the normal report as a complete AI handoff packet.
- Include the full decklist.
- Include annotated card-role notes for every main-deck card so another AI can
  reason about cuts, protection, and replacements without losing context.
"""


from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from app_io.output_writer import get_unique_output_path, write_text_file
from reports.strategy_knowledge_sections import build_strategy_knowledge_report_section  # v1.4.13 Strategy Knowledge report handoff
from analysis.deck_building_philosophies import render_philosophy_guide_section as _legacy_render_philosophy_guide_section  # fallback only after v1.1.18
from philosophy.report_section import format_philosophy_guide_section_from_runtime_config  # v1.1.18 live report guide section
# v1.1.22.3 manual-context review clarity: off-plan/manual review examples are context flags, not automatic cuts.
# v1.1.19.1 EXPLANATION WORDING CLEANUP / REPLACEMENT DE-DUP
# - Protected infrastructure entries now use infrastructure-safe wording instead
#   of commander-trigger/copy wording.
# - Replacement-direction explanations remain in Replacement Need Profile and
#   are no longer duplicated in the short Replacement / Addition Needs summary.

from philosophy.cut_explanation_wiring import build_philosophy_cut_explanation  # v1.1.19 live cut explanation wording
from philosophy.protected_explanation_wiring import build_philosophy_protected_explanation  # v1.1.19 live protected explanation wording
from philosophy.replacement_explanation_wiring import build_philosophy_replacement_explanation  # v1.1.19 live replacement-direction wording
from legality.companion_rules import (
    OFFICIAL_COMPANION_CARD_NAMES as COMPANION_CARD_NAMES,
    companion_is_banned_as_companion,
    get_companion_banned_note,
    get_companion_intake_lines,
    get_companion_replacement_filter_note,
    get_companion_restriction_summary,
)


# Companion card names are imported from legality.companion_rules.

def _v1118_build_live_report_philosophy_guide_section(context: dict[str, Any]) -> str:
    """Render the live v1.1 Philosophy Guide report section with legacy fallback."""
    philosophy_context = context.get("philosophy_context")
    if not philosophy_context:
        return ""

    try:
        runtime_philosophy_config = _v1118_runtime_config_from_legacy_philosophy_context(context)
        section = format_philosophy_guide_section_from_runtime_config(
            runtime_philosophy_config,
            include_intensity=True,
            include_notes=True,
        )
        if "## Philosophy Guide" in section and "v0.6.5.3 Philosophy Subtype Report Summary" not in section:
            return section.rstrip()
    except Exception:
        pass

    # Fallback only: preserve old behavior if the v1.1 formatter cannot render.
    return _legacy_render_philosophy_guide_section(philosophy_context).rstrip()

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

def _duplicate_legality_first_pass_lines(context: dict[str, Any]) -> list[str]:
    """Render duplicate-copy fixes before ordinary required cut candidates.

    This is presentation/wording only. It does not change legality, cut scoring,
    replacement scoring, or deck-analysis behavior. The goal is to make the
    player-facing report clearer when a duplicate copy can solve both an illegal
    duplicate and deck-size pressure.
    """
    legality = context.get("legality")
    cut_pressure = context.get("cut_pressure")
    duplicates = list(getattr(legality, "illegal_duplicate_cards", []) or []) if legality else []
    if not duplicates:
        return []

    required_cuts = int(getattr(cut_pressure, "required_cuts", 0) or 0) if cut_pressure else 0
    lines = _section("Duplicate Legality First-Pass Fixes")
    lines.extend([
        "> Review these duplicate-copy fixes before treating non-duplicate cards as mandatory required cuts.",
        "> This section is a player-facing priority note only; the legality engine and cut scoring have not changed.",
    ])
    if required_cuts > 0:
        lines.append("> Because the deck also has deck-size pressure, removing an extra illegal duplicate may solve both the duplicate issue and part or all of the required cut count.")
    else:
        lines.append("> The deck does not appear to need deck-size cuts from this checkpoint, but illegal duplicates still need legality review.")
    lines.append("")
    for item in duplicates[:12]:
        card_name = item.get("card_name", "Unknown card")
        try:
            quantity = int(item.get("quantity", 0) or 0)
        except (TypeError, ValueError):
            quantity = 0
        extra_copies = max(1, quantity - 1) if quantity else "review"
        lines.append(f"### {card_name}")
        lines.append(f"- Reported quantity: {quantity if quantity else 'Unknown'}")
        lines.append(f"- Extra copy/copies to review first: {extra_copies}")
        if required_cuts > 0:
            lines.append("- Priority note: removing an extra illegal duplicate copy should be checked before making a non-duplicate required cut recommendation.")
        else:
            lines.append("- Priority note: resolve the duplicate legality issue even if no deck-size cut is required.")
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

def _resolve_replacement_candidate_summary_for_collection_section(context: dict) -> object:
    return (
        context.get('replacement_candidates')
        or context.get('replacement_candidate_summary')
        or context.get('replacement_summary')
        or context.get('replacement_candidate_engine')
    )

def _build_collection_pull_section(context: dict[str, Any]) -> list[str]:
    replacement_candidates = _resolve_replacement_candidate_summary_for_collection_section(context)
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
        "> v0.6.6.6 philosophy-bias lock is active: candidate presentation may be lightly nudged, overbroad cut-bias aliases are suppressed, visibility counters/examples are recorded, companion manual-review wording is clarified, and the system still cannot force weak or off-plan recommendations or override collection-only mode.",
        "> Collection gaps are tracked role-by-role. Possible and Shakeup cards do not close a strong-fit gap.",
        "> If no strong owned candidate exists, The Dragon's Touch should say so instead of forcing a weak or off-plan recommendation.",
        "> v0.9.3 collection-first hardening is active: Dragon density/payoff and copy-token payoff require stricter Strong-candidate evidence.",
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
    dragon_gate_manual_review = _dragon_gate_manual_review_candidates(replacement_candidates) if replacement_candidates else []
    if dragon_gate_manual_review:
        lines.append("")
        lines.append("### Dragon Gate Manual Review Candidates")
        lines.append("> These candidates were broad Dragon-need matches, but the Dragon semantic gate could not confirm them as actual Dragons, changelings/all-creature-type cards, or explicit Dragon-typal support.")
        lines.append("> They are kept for pilot review, but they should not appear as Strong Owned Dragon-density or Dragon-payoff recommendations.")
        for candidate in dragon_gate_manual_review[:10]:
            lines.append(f"### {getattr(candidate, 'card_name', 'Unknown candidate')}")
            lines.append("- Confidence: Manual Review")
            lines.append(f"- Collection-first rank score: {min(int(getattr(candidate, 'collection_first_rank_score', 0) or 0), 49)}")
            lines.append("- Collection-first rank band: Dragon Gate Manual Review")
            lines.append("- Recommendation type: dragon_need_semantic_review")
            lines.append(f"- Why it needs review: {getattr(candidate, 'why_to_be_careful', 'Dragon semantic gate requires manual review before treating this as Dragon support.')}")
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

def _build_replacement_need_profile_section(context: dict[str, Any]) -> list[str]:
    replacement = context.get("replacement_needs")
    if not replacement:
        return []

    details = list(getattr(replacement, "need_details", []) or [])
    if not details:
        return []

    lines = _section("Replacement Need Profile")
    lines.extend([
        f"- Detection version: {getattr(replacement, 'detection_version', 'v0.9.2-dev')}",
        "- Purpose: explain what kind of replacement the deck needs before judging exact cards.",
        "- Ranking impact: None in v0.9.2; this is need-detection cleanup only.",
        "",
        "> v0.9.2 note: this section separates generic role gaps from strategy-specific needs so future replacement ranking can target the right kind of card.",
    ])

    role_gap_summary = list(getattr(replacement, "role_gap_summary", []) or [])
    strategy_need_summary = list(getattr(replacement, "strategy_need_summary", []) or [])
    if role_gap_summary:
        lines.append("")
        lines.append("### Role Gap Summary")
        for item in role_gap_summary[:10]:
            lines.append(f"- {item}")
    if strategy_need_summary:
        lines.append("")
        lines.append("### Strategy-Specific Need Summary")
        for item in strategy_need_summary[:10]:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("### Need Details")
    for detail in details[:12]:
        lines.append(f"#### {getattr(detail, 'category', 'Unknown need')}")
        lines.append(f"- Priority: {getattr(detail, 'priority', 'Medium')}")
        lines.append(f"- Need type: {getattr(detail, 'need_type', 'review_need')}")
        lines.append(f"- Source: {getattr(detail, 'source', 'heuristic')}")
        reason = getattr(detail, "reason", "")
        if reason:
            lines.append(f"- Why this need appeared: {reason}")
        evidence = list(getattr(detail, "deck_evidence", []) or [])
        if evidence:
            lines.append("- Deck evidence:")
            for item in evidence[:4]:
                lines.append(f"  - {item}")
        shape = getattr(detail, "suggested_replacement_shape", "")
        if shape:
            lines.append(f"- What a good replacement should look like: {shape}")
        caution = getattr(detail, "caution", "")
        if caution:
            lines.append(f"- Caution: {caution}")

        # v1.1.19: explanation-only replacement-direction wiring for existing needs.
        v1119_replacement_note = _v1119_build_replacement_note(detail, context)
        if v1119_replacement_note:
            lines.append(f"- v1.1 philosophy replacement direction: {v1119_replacement_note}")
        lines.append("")

    return lines

def _build_replacement_candidate_engine_preview_section(context: dict[str, Any]) -> list[str]:
    """Render the v0.9.1 replacement candidate data-model preview.

    This is intentionally a preview. It confirms the new v0.9 candidate model is
    active without changing the existing collection-pull recommendation behavior.
    """
    summary = ensure_replacement_candidate_summary_from_context(context)
    if not summary or not getattr(summary, "active", False):
        return []

    lines = _section("Replacement Candidate Engine Preview")
    lines.extend([
        f"- Engine status: {getattr(summary, 'engine_version', 'v0.9.1-dev')} — {getattr(summary, 'engine_status', 'data_model_foundation')}",
        f"- Candidate source mode: {getattr(summary, 'candidate_source_mode', 'collection_first_adapter')}",
        f"- Ranking method: {getattr(summary, 'ranking_method', 'not_active')}",
        f"- Exact ranking engine active: {'Yes' if getattr(summary, 'exact_ranking_active', False) else 'No'}",
        f"- Full-card-pool fallback active: {'Yes' if getattr(summary, 'full_card_pool_fallback_active', False) else 'No'}",
        f"- Confidence ceiling active: {'Yes' if _replacement_confidence_ceiling_is_active(summary) else 'No'}",
        f"- Dragon semantic gate active: {'Yes' if _replacement_dragon_semantic_gate_is_active(summary) else 'No'}",
        f"- Dragon gate visible rewrite active: {'Yes' if _dragon_gate_visible_rewrite_is_active(summary) else 'No'}",
        "",
        "### Current Candidate Snapshot",
        f"- Collection-owned candidates adapted: {getattr(summary, 'collection_owned_candidates_adapted', 0)}",
        f"- Strong candidates adapted: {getattr(summary, 'strong_candidates_adapted', 0)}",
        f"- Possible candidates adapted: {getattr(summary, 'possible_candidates_adapted', 0)}",
        f"- Shakeup candidates adapted: {getattr(summary, 'shakeup_candidates_adapted', 0)}",
        "",
        "> v0.9.1 note: this section proves the replacement-candidate data model is active. It does not change candidate ranking, does not add outside-card fallback, and does not make automatic swaps.",
    ])

    notes = list(getattr(summary, "notes", []) or [])
    if _replacement_confidence_ceiling_is_active(summary):
        preview_note = "v0.9.4.5.2 preview flag display hotfix active: the top preview flag now recognizes v0.9.4.x confidence-ceiling signals."
        if preview_note not in notes:
            notes.append(preview_note)
    if notes:
        lines.append("")
        lines.append("### Data Model Notes")
        for note in notes[:6]:
            lines.append(f"- {note}")

    candidates = list(getattr(summary, "candidates", []) or [])
    if candidates:
        lines.append("")
        lines.append("### Top Ranked Collection-First Candidates")
        for candidate in candidates[:8]:
            lines.append(f"#### {getattr(candidate, 'card_name', 'Unknown card')}")
            lines.append(f"- Source: {getattr(candidate, 'source', 'unknown')}")
            lines.append(f"- Owned status: {getattr(candidate, 'owned_status', 'unknown')}")
            lines.append(f"- Recommendation type: {getattr(candidate, 'recommendation_type', 'review_candidate')}")
            lines.append(f"- Confidence: {_display_candidate_confidence(candidate)}")
            if getattr(candidate, 'dragon_semantic_gate_adjusted', False):
                lines.append("- Dragon semantic gate adjusted: Yes — manual review required before treating this as Dragon-density or Dragon-payoff support.")
            lines.append(f"- Collection-first rank score: {_display_candidate_rank_score(candidate)}")
            lines.append(f"- Collection-first rank band: {_display_candidate_rank_band(candidate)}")
            ceiling = getattr(candidate, "collection_first_confidence_ceiling", None)
            raw_score = getattr(candidate, "collection_first_raw_rank_score", None)
            if ceiling is not None:
                lines.append(f"- Confidence ceiling: {ceiling}")
            if raw_score is not None and raw_score != getattr(candidate, "collection_first_rank_score", None):
                lines.append(f"- Raw score before confidence ceiling: {raw_score}")
            role = getattr(candidate, "replacement_role", "")
            if role:
                lines.append(f"- Replacement role: {role}")
            fit = getattr(candidate, "why_it_fits", "")
            if fit:
                lines.append(f"- Why it fits: {fit}")
            careful = getattr(candidate, "why_to_be_careful", "")
            if careful:
                lines.append(f"- Why to be careful: {careful}")
            lines.append("")

    ranking_notes = list(getattr(summary, "ranking_notes", []) or [])
    if ranking_notes:
        lines.append("### Ranking Notes")
        for note in ranking_notes[:8]:
            lines.append(f"- {note}")
        lines.append("")

    boundaries = list(getattr(summary, "safety_boundaries", []) or [])
    if boundaries:
        lines.append("### Safety Boundaries")
        for boundary in boundaries[:8]:
            lines.append(f"- {boundary}")

    return lines

def _v0951_replace_full_pool_preview_section(report_text: str, context: dict) -> str:
    heading = "## Full-Card-Pool Fallback Preview"
    start = report_text.find(heading)
    if start == -1:
        return report_text

    # End at next H2 heading.
    next_h2 = report_text.find("\n## ", start + len(heading))
    end = next_h2 if next_h2 != -1 else len(report_text)

    # Preserve v0.9.5 active/weak logic if available, but use cleaned need extraction.
    summary = (
        context.get("replacement_candidates")
        or context.get("replacement_candidate_summary")
        or context.get("replacement_summary")
        or context.get("replacement_candidate_engine")
    )

    collection_weak = True
    if "_v095_collection_first_pool_is_weak" in globals() and summary:
        try:
            collection_weak = _v095_collection_first_pool_is_weak(summary)
        except Exception:
            collection_weak = True

    lines: list[str] = []
    lines.append("## Full-Card-Pool Fallback Preview")
    lines.append("")
    lines.append("> v0.9.5.1 preview: This section is informational only. It does not override collection-first recommendations and does not create automatic swaps.")
    lines.append("> Use this when the owned-card pool is thin, overly gated, or missing a clear role. Owned cards remain preferred when they are real fits.")
    lines.append("")
    lines.append(f"- Full-card-pool fallback preview active: {'Yes' if collection_weak else 'No'}")
    lines.append("- Fallback mode: preview only")
    lines.append("- Recommendation authority: collection-first remains primary")
    lines.append("- Automatic swaps: No")
    lines.append("")

    if not collection_weak:
        lines.append("Collection-first candidates appear sufficient for this pass, so full-card-pool fallback stays dormant.")
        lines.append("")
    else:
        needs = _v0951_get_replacement_needs_from_context(context)
        lines.append("### Fallback Categories to Explore Later")
        for need in needs:
            category = _v0951_full_pool_category_for_need(need)
            lines.append(f"- {category} — triggered by: {need}")
        lines.append("")
        lines.append("### Safety Boundaries")
        lines.append("- These are replacement categories, not exact card recommendations.")
        lines.append("- Full-card-pool card names should be added in a later patch only after role matching and safety gates are stable.")
        lines.append("- Combo-related outside-card suggestions remain informational unless combo optimization is explicitly enabled.")
        lines.append("")

    new_section = "\n".join(lines)
    return report_text[:start] + new_section + report_text[end:]
