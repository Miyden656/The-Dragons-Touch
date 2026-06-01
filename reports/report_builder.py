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
from reports.sections.multiplayer_section import build_multiplayer_report_section  # additive 4-player pod-value section
from reports.sections.political_section import build_political_report_section  # additive Section-3 political archetypes
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


# =============================================================================
# FILE LAYOUT (v1.5)
# =============================================================================
# This module assembles the full deck review report by orchestrating section
# builders. Most helpers are private (_-prefixed) with version-stamped families
# from the iterative v0.6 -> v1.1 patch history.
#
# Public API:
#   build_normal_report(...)   the main orchestrator
#   write_normal_report(...)   thin wrapper that writes the report to disk
#
# Helper groups, top-to-bottom by version:
#   _v1118_*    v1.1.18 live philosophy guide section helpers
#   _v1119_*    v1.1.19 cut/protected/replacement explanation helpers
#   _v11191_*   v1.1.19.1 protected-infrastructure wording helpers
#   _build_*    section builders (companion legality, decklist, collection pull)
#   _format_*   per-card formatting (role tags, plan fit, review status)
#   _v0946*     v0.9.4.6 dragon-gate suppression
#   _v095_*     v0.9.5 collection-first weakness + need-aware previews
#   _v0951_*    v0.9.5.1 need text cleanup + category mapping
#   _v0952_*    v0.9.5.2 exact-pool preview construction
#   _v0953_*    v0.9.5.3 color-identity guard for previews
#   _v0954_*    v0.9.5.4 budget/bracket label addition
#   _v0955_*    v0.9.5.5 role-alignment improvements (also referenced externally)
#   _v09551_*   v0.9.5.5.1 need-aligned addendum
#
# NOTE: Many _v*_ helpers are referenced by reports/sections/* and
# reports/strategy_sections/* via from-import. Don't delete _-prefixed
# functions without checking cross-module imports first.
#
# See docs/ARCHITECTURE.md for the full scoring chain and how reports plug in.
# =============================================================================




def _v1118_absorb_object_public_attrs(value: Any) -> dict[str, Any]:
    """Best-effort conversion of runtime/config objects into a small safe mapping."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    data: dict[str, Any] = {}
    for name in (
        "guide_preference",
        "philosophy_key",
        "selected_lens",
        "philosophy_lens",
        "philosophy_subtype",
        "intended_bracket",
        "budget_note",
        "prompt_interaction_mode",
    ):
        if hasattr(value, name):
            try:
                data[name] = getattr(value, name)
            except Exception:
                pass
    return data


def _v1118_runtime_config_from_legacy_philosophy_context(context: dict[str, Any]) -> dict[str, Any]:
    """Build a v1.1 runtime-style philosophy config from the existing report context.

    v1.1.18 live report hook:
    - Uses the existing legacy philosophy_context as input.
    - Maps legacy `label` to v1.1 `selected_lens`.
    - Uses runtime bracket/budget fields when available.
    - Does not change deck analysis, cut scoring, replacement scoring, legality,
      collection matching, or combo behavior.
    """
    philosophy_context = context.get("philosophy_context") or {}
    runtime_config = context.get("runtime_config")

    config: dict[str, Any] = {}
    config.update(_v1118_absorb_object_public_attrs(runtime_config))

    if isinstance(philosophy_context, dict):
        # Preserve useful aliases already understood by v1.1 runtime mapping.
        for key in (
            "selected_lens",
            "philosophy_lens",
            "philosophy",
            "selected_philosophy",
            "review_philosophy",
            "subtype",
            "philosophy_subtype",
            "selected_subtype",
            "guide_lens",
            "guide_presentation",
            "guide_style",
            "guide_preference",
            "persona_presentation",
            "persona_style",
            "named_guide_preference",
            "intensity",
            "philosophy_intensity",
            "pilot_notes",
            "philosophy_notes",
            "combo_tolerance",
            "budget_note",
            "table_power_note",
            "intended_bracket",
        ):
            if key in philosophy_context and philosophy_context[key] not in (None, ""):
                config[key] = philosophy_context[key]

        # Legacy context primarily exposes `label`, not v1.1 `selected_lens`.
        if not config.get("selected_lens"):
            config["selected_lens"] = philosophy_context.get("label") or "Balanced / Unknown"

        # Legacy report text used rules_summary as the short pilot-facing note.
        if not config.get("pilot_notes"):
            config["pilot_notes"] = philosophy_context.get("rules_summary") or philosophy_context.get("report_guidance_summary") or ""

        if "named_guide_enabled" in philosophy_context:
            config["named_guide_enabled"] = philosophy_context.get("named_guide_enabled")

    if not config.get("guide_presentation") and not config.get("guide_preference"):
        config["guide_presentation"] = getattr(runtime_config, "guide_preference", None) or "either"

    if not config.get("budget_note"):
        config["budget_note"] = getattr(runtime_config, "budget_note", None) or "No budget note provided"

    if not config.get("table_power_note") and not config.get("intended_bracket"):
        config["table_power_note"] = getattr(runtime_config, "intended_bracket", None) or "Not sure yet"

    if not config.get("intensity"):
        config["intensity"] = "normal"

    return config


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


# v1.1.19 LIVE PHILOSOPHY EXPLANATION WIRING
# Adds philosophy-aware explanation text to existing report entries only.
# This does not change cut selection, cut scoring, cut ranking, protected-card detection,
# replacement detection, replacement scoring, or exact-card recommendations.

def _v1119_runtime_config_for_explanations(context: dict[str, Any] | None) -> dict[str, Any]:
    """Build v1.1 runtime config for live explanation rendering."""
    if not isinstance(context, dict):
        return {}
    try:
        return _v1118_runtime_config_from_legacy_philosophy_context(context)
    except Exception:
        return {}


def _v1119_cut_record_from_entry(entry: Any, explanation_kind: str = "cut") -> dict[str, Any]:
    """Convert an existing cut/protected entry into a safe explanation record."""
    reasons = list(getattr(entry, "reasons", []) or [])
    reason_text = "; ".join(str(reason) for reason in reasons[:3] if reason)
    label = getattr(entry, "cut_type", "Review candidate")
    record = {
        "card_name": getattr(entry, "card_name", None),
        "reason": reason_text,
        "confidence": getattr(entry, "cut_confidence", None),
        "cut_type": label,
        "protection_type": label,
        "score": getattr(entry, "score", None),
    }
    if explanation_kind == "protected":
        record["protected_type"] = label
        record["protection_type"] = label
    return record


def _v11191_is_protected_infrastructure_entry(entry: Any) -> bool:
    """Return True when a protected entry is infrastructure/mana-role support.

    v1.1.19.1 keeps the live explanation wiring, but avoids describing lands and
    other infrastructure pieces as if they protect/copy/convert the commander's
    unique trigger.
    """
    label = str(getattr(entry, "cut_type", "") or "").lower()
    reasons = " ".join(str(reason) for reason in (getattr(entry, "reasons", []) or [])).lower()
    combined = f"{label} {reasons}"

    if "protected infrastructure" in combined:
        return True
    if "fills infrastructure role" in combined:
        return True
    if "mana-base" in combined or "mana base" in combined:
        return True
    if "fixing land" in combined or "mana_source" in combined or "mana source" in combined:
        return True
    return False


def _v11191_build_protected_infrastructure_note(entry: Any) -> str:
    """Build safer v1.1 protected wording for infrastructure entries."""
    card_name = str(getattr(entry, "card_name", "") or "This card").strip()
    reasons = [str(reason) for reason in (getattr(entry, "reasons", []) or []) if reason]
    useful_reasons = []
    for reason in reasons:
        lower = reason.lower()
        if (
            "protected label" in lower
            or "initial flag" in lower
            or "philosophy adjustment" in lower
            or "final verdict" in lower
            or "supporting note" in lower
        ):
            useful_reasons.append(reason)

    base = (
        f"**{card_name}:** I would keep this protected because it supports the deck's mana "
        "or role infrastructure. Review it only against the same role slot, such as better "
        "fixing, ramp, protection, or support for the current plan, rather than treating it "
        "as a normal cut."
    )
    if useful_reasons:
        return base + " " + "; ".join(useful_reasons[:3])
    return base


def _v1119_build_cut_note(entry: Any, context: dict[str, Any] | None, explanation_kind: str = "cut") -> str:
    """Return v1.1 philosophy-aware cut/protected explanation text for an existing entry."""
    runtime_config = _v1119_runtime_config_for_explanations(context)
    record = _v1119_cut_record_from_entry(entry, explanation_kind=explanation_kind)
    try:
        if explanation_kind == "protected":
            if _v11191_is_protected_infrastructure_entry(entry):
                return _v11191_build_protected_infrastructure_note(entry)
            explanation = build_philosophy_protected_explanation(record, runtime_config)
        else:
            explanation = build_philosophy_cut_explanation(record, runtime_config)
        return str(getattr(explanation, "philosophy_note", "") or "").strip()
    except Exception:
        return ""


def _v1119_replacement_record_from_need_detail(detail: Any) -> dict[str, Any]:
    """Convert an existing replacement need detail into a safe explanation record."""
    evidence = list(getattr(detail, "deck_evidence", []) or [])
    reason_parts = []
    reason = getattr(detail, "reason", "")
    if reason:
        reason_parts.append(str(reason))
    caution = getattr(detail, "caution", "")
    if caution:
        reason_parts.append(str(caution))
    if evidence:
        reason_parts.append("; ".join(str(item) for item in evidence[:3]))
    return {
        "role": getattr(detail, "category", None),
        "reason": "; ".join(part for part in reason_parts if part),
        "priority": getattr(detail, "priority", None),
        "replacement_category": getattr(detail, "category", None),
        "need": getattr(detail, "category", None),
        "type": getattr(detail, "need_type", None),
    }


def _v1119_build_replacement_note(detail_or_category: Any, context: dict[str, Any] | None) -> str:
    """Return v1.1 philosophy-aware replacement-direction text for an existing need."""
    runtime_config = _v1119_runtime_config_for_explanations(context)
    if isinstance(detail_or_category, str):
        record = {"role": detail_or_category, "reason": "Existing replacement need from the current report."}
    else:
        record = _v1119_replacement_record_from_need_detail(detail_or_category)
    try:
        explanation = build_philosophy_replacement_explanation(record, runtime_config)
        return str(getattr(explanation, "philosophy_note", "") or "").strip()
    except Exception:
        return ""


def _format_cut_entries(
    entries,
    empty: str = "None found in this checkpoint.",
    limit: int = 12,
    context: dict[str, Any] | None = None,
    explanation_kind: str = "cut",
) -> list[str]:
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

        # v1.1.19: explanation-only live wiring. This adds philosophy-aware wording
        # to the existing candidate, without changing candidate selection, score, or rank.
        if context is not None:
            note_kind = "protected" if explanation_kind == "protected" or is_protected_label else "cut"
            v1119_note = _v1119_build_cut_note(entry, context, explanation_kind=note_kind)
            if v1119_note:
                heading = "v1.1 philosophy protected-card explanation" if note_kind == "protected" else "v1.1 philosophy cut explanation"
                lines.append(f"- {heading}: {v1119_note}")
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



def _replacement_confidence_ceiling_is_active(summary: object) -> bool:
    """Return True when any v0.9.4.x confidence ceiling signal is present."""
    if bool(getattr(summary, 'ranking_confidence_ceiling_active', False)):
        return True

    version = str(getattr(summary, 'ranking_confidence_ceiling_version', '') or '').lower()
    if 'v0.9.4.5' in version or 'confidence' in version:
        return True

    notes = ' '.join(str(item) for item in (getattr(summary, 'notes', []) or [])).lower()
    if 'confidence ceiling' in notes or 'confidence ceilings' in notes:
        return True

    boundaries = ' '.join(str(item) for item in (getattr(summary, 'safety_boundaries', []) or [])).lower()
    if 'confidence ceiling' in boundaries or 'confidence ceilings' in boundaries:
        return True

    for candidate in list(getattr(summary, 'candidates', []) or []):
        if getattr(candidate, 'collection_first_confidence_ceiling', None) is not None:
            return True
        if getattr(candidate, 'collection_first_raw_rank_score', None) is not None:
            return True

    return False


def _replacement_dragon_semantic_gate_is_active(summary: object) -> bool:
    if bool(getattr(summary, "dragon_semantic_gate_active", False)):
        return True
    version = str(getattr(summary, "dragon_semantic_gate_version", "") or "").lower()
    if "v0.9.4.6" in version or "dragon semantic gate" in version:
        return True
    notes = " ".join(str(item) for item in (getattr(summary, "notes", []) or [])).lower()
    if "dragon semantic gate active" in notes:
        return True
    boundaries = " ".join(str(item) for item in (getattr(summary, "safety_boundaries", []) or [])).lower()
    if "dragon semantic gate" in boundaries:
        return True
    for candidate in list(getattr(summary, "candidates", []) or []):
        if getattr(candidate, "dragon_semantic_gate_adjusted", False):
            return True
    return False


def _candidate_dragon_gate_visible_adjusted(candidate: object) -> bool:
    if bool(getattr(candidate, 'dragon_gate_visible_rewrite_active', False)):
        return True
    if bool(getattr(candidate, 'dragon_semantic_gate_adjusted', False)):
        return True
    rec_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
    careful = str(getattr(candidate, 'why_to_be_careful', '') or '').lower()
    return rec_type == 'dragon_need_semantic_review' or 'visible-field rewrite applied' in careful or 'dragon semantic gate' in careful

def _display_candidate_confidence(candidate: object) -> str:
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return 'Manual Review'
    return str(getattr(candidate, 'confidence', 'Review') or 'Review')

def _display_candidate_recommendation_type(candidate: object) -> str:
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return 'dragon_need_semantic_review'
    return str(getattr(candidate, 'recommendation_type', 'review') or 'review')

def _display_candidate_rank_score(candidate: object) -> int:
    score = int(getattr(candidate, 'collection_first_rank_score', 0) or 0)
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return min(score, 49)
    return score

def _display_candidate_rank_band(candidate: object) -> str:
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return 'Dragon Gate Manual Review'
    return str(getattr(candidate, 'collection_first_rank_band', 'Unranked') or 'Unranked')

def _dragon_gate_visible_rewrite_is_active(summary: object) -> bool:
    if bool(getattr(summary, 'dragon_gate_visible_rewrite_active', False)):
        return True
    notes = ' '.join(str(item) for item in (getattr(summary, 'notes', []) or [])).lower()
    if 'dragon gate visible rewrite active' in notes:
        return True
    for candidate in list(getattr(summary, 'candidates', []) or []):
        if _candidate_dragon_gate_visible_adjusted(candidate):
            return True
    return False


def _filter_dragon_gate_from_strong_owned_candidates(candidates: object) -> list[object]:
    return [
        candidate for candidate in list(candidates or [])
        if not _candidate_dragon_gate_visible_adjusted(candidate)
    ]

def _dragon_gate_manual_review_candidates(summary: object) -> list[object]:
    return [
        candidate for candidate in list(getattr(summary, 'candidates', []) or [])
        if _candidate_dragon_gate_visible_adjusted(candidate)
    ]

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

# v0.9.4.6.10-dev — Strong Owned Render Loop Direct Suppression Hotfix
def _v094610_collect_dragon_gate_manual_names(report_text: str) -> set[str]:
    names: set[str] = set()

    top_start = report_text.find("### Top Ranked Collection-First Candidates")
    top_end = report_text.find("### Safety Boundaries", top_start) if top_start != -1 else -1
    top_section = report_text[top_start:top_end] if top_start != -1 and top_end != -1 else ""

    for block in top_section.split("\n#### "):
        if "Dragon Gate Manual Review" not in block:
            continue
        block_lines = block.splitlines()
        if not block_lines:
            continue
        first_line = block_lines[0].strip().lstrip("#").strip()
        if first_line and not first_line.startswith("Top Ranked"):
            names.add(first_line)

    manual_start = report_text.find("### Dragon Gate Manual Review Candidates")
    manual_end = report_text.find("### Possible Owned Candidates", manual_start) if manual_start != -1 else -1
    if manual_end == -1 and manual_start != -1:
        manual_end = report_text.find("### Collection Gaps", manual_start)
    manual_section = report_text[manual_start:manual_end] if manual_start != -1 and manual_end != -1 else (report_text[manual_start:] if manual_start != -1 else "")

    for block in manual_section.split("\n### "):
        block_lines = block.splitlines()
        if not block_lines:
            continue
        first_line = block_lines[0].strip().lstrip("#").strip()
        if not first_line:
            continue
        if first_line.startswith("Dragon Gate Manual Review"):
            continue
        if first_line.startswith(">"):
            continue
        if len(first_line) <= 80:
            names.add(first_line)

    return names


def _v094610_remove_named_blocks_from_strong_owned(strong_section: str, names_to_remove: set[str]) -> str:
    if not strong_section or not names_to_remove:
        return strong_section

    lines = strong_section.splitlines()
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("### ") and not line.startswith("### Strong Owned Candidates"):
            heading = line[4:].strip()
            if heading in names_to_remove:
                i += 1
                while i < len(lines) and not lines[i].startswith("### "):
                    i += 1
                continue
        output.append(line)
        i += 1

    return "\n".join(output)


def _v094610_suppress_dragon_gate_from_strong_owned_text(report_text: str) -> str:
    names_to_remove = _v094610_collect_dragon_gate_manual_names(report_text)
    if not names_to_remove:
        return report_text

    strong_start = report_text.find("### Strong Owned Candidates")
    if strong_start == -1:
        return report_text

    possible_start = report_text.find("### Possible Owned Candidates", strong_start)
    manual_start = report_text.find("### Dragon Gate Manual Review Candidates", strong_start)
    gaps_start = report_text.find("### Collection Gaps", strong_start)
    section_end_candidates = [idx for idx in (manual_start, possible_start, gaps_start) if idx != -1 and idx > strong_start]
    strong_end = min(section_end_candidates) if section_end_candidates else len(report_text)

    strong_section = report_text[strong_start:strong_end]
    cleaned_section = _v094610_remove_named_blocks_from_strong_owned(strong_section, names_to_remove)

    if cleaned_section != strong_section and "v0.9.4.6.10 note" not in cleaned_section:
        note = "\n> v0.9.4.6.10 note: Dragon-gate Manual Review candidates were suppressed from this Strong Owned section.\n"
        first_newline = cleaned_section.find("\n")
        if first_newline != -1:
            cleaned_section = cleaned_section[:first_newline + 1] + note + cleaned_section[first_newline + 1:]
        else:
            cleaned_section += note

    return report_text[:strong_start] + cleaned_section + report_text[strong_end:]

# v0.9.5-dev — Full-Card-Pool Fallback Preview
def _v095_collection_first_pool_is_weak(summary: object) -> bool:
    candidates = list(getattr(summary, "candidates", []) or [])
    strong_count = 0
    good_count = 0

    for candidate in candidates:
        if bool(getattr(candidate, "dragon_semantic_gate_adjusted", False)):
            continue
        if bool(getattr(candidate, "dragon_gate_visible_rewrite_active", False)):
            continue

        confidence = str(getattr(candidate, "confidence", "") or "").lower()
        band = str(getattr(candidate, "collection_first_rank_band", "") or "").lower()
        score = int(getattr(candidate, "collection_first_rank_score", 0) or 0)

        if confidence.startswith("strong") or "top collection fit" in band or score >= 90:
            strong_count += 1
        if score >= 70 or "good" in band or "strong" in band or "top" in band:
            good_count += 1

    # Preview fallback is warranted only when the collection-first pool looks thin.
    return strong_count < 3 or good_count < 6


def _v095_get_replacement_needs_from_context(context: dict) -> list[str]:
    needs = []
    for key in ("replacement_needs", "replacement_need_profile", "needs", "replacement_profile"):
        value = context.get(key)
        if not value:
            continue
        if isinstance(value, dict):
            for item in value.values():
                if isinstance(item, (list, tuple, set)):
                    needs.extend(str(x) for x in item)
                else:
                    needs.append(str(item))
        elif isinstance(value, (list, tuple, set)):
            needs.extend(str(x) for x in value)
        else:
            needs.append(str(value))

    cleaned = []
    for need in needs:
        need = need.strip()
        if need and need not in cleaned:
            cleaned.append(need)
    return cleaned[:8]


def _v095_full_pool_category_for_need(need: str) -> str:
    low = need.lower()
    if "ramp" in low or "mana" in low:
        return "More ramp / mana development"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "removal" in low or "interaction" in low:
        return "More targeted interaction"
    if "wipe" in low or "board clear" in low:
        return "More board wipes"
    if "protection" in low or "protect" in low:
        return "More protection"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "token" in low:
        return "More token support"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "finisher" in low or "win" in low:
        return "More finishers"
    return "Better role coverage"


def _v095_build_full_pool_preview_lines(context: dict) -> list[str]:
    summary = (
        context.get("replacement_candidates")
        or context.get("replacement_candidate_summary")
        or context.get("replacement_summary")
        or context.get("replacement_candidate_engine")
    )

    lines: list[str] = []
    lines.append("## Full-Card-Pool Fallback Preview")
    lines.append("")
    lines.append("> v0.9.5 preview: This section is informational only. It does not override collection-first recommendations and does not create automatic swaps.")
    lines.append("> Use this when the owned-card pool is thin, overly gated, or missing a clear role. Owned cards remain preferred when they are real fits.")
    lines.append("")

    if not summary:
        lines.append("- Full-card-pool fallback active: Preview unavailable — replacement candidate summary was not found.")
        lines.append("- Safety boundary: No outside-card recommendations were generated.")
        lines.append("")
        return lines

    collection_weak = _v095_collection_first_pool_is_weak(summary)
    lines.append(f"- Full-card-pool fallback preview active: {'Yes' if collection_weak else 'No'}")
    lines.append("- Fallback mode: preview only")
    lines.append("- Recommendation authority: collection-first remains primary")
    lines.append("- Automatic swaps: No")
    lines.append("")

    if not collection_weak:
        lines.append("Collection-first candidates appear sufficient for this pass, so full-card-pool fallback stays dormant.")
        lines.append("")
        return lines

    needs = _v095_get_replacement_needs_from_context(context)
    if not needs:
        lines.append("No replacement needs were available to map into fallback categories.")
        lines.append("")
        return lines

    lines.append("### Fallback Categories to Explore Later")
    for need in needs:
        category = _v095_full_pool_category_for_need(need)
        lines.append(f"- {category} — triggered by: {need}")

    lines.append("")
    lines.append("### Safety Boundaries")
    lines.append("- These are replacement categories, not exact card recommendations.")
    lines.append("- Full-card-pool card names should be added in a later patch only after role matching and safety gates are stable.")
    lines.append("- Combo-related outside-card suggestions remain informational unless combo optimization is explicitly enabled.")
    lines.append("")

    return lines

# v0.9.5.1-dev — Full-Pool Preview Need Extraction Cleanup
def _v0951_clean_need_text(value: object) -> list[str]:
    cleaned: list[str] = []

    def add(text: object) -> None:
        item = str(text or "").strip()
        if not item:
            return
        if item.startswith("ReplacementNeedSummary("):
            return
        if item.startswith("[") and "ReplacementNeedSummary(" in item:
            return
        if item not in cleaned:
            cleaned.append(item)

    if value is None:
        return cleaned

    # Dataclass/object style ReplacementNeedSummary support.
    for attr in ("priority_categories", "notes", "role_gap_summary", "strategy_need_summary", "need_details"):
        if hasattr(value, attr):
            attr_value = getattr(value, attr, None)
            if isinstance(attr_value, dict):
                for k, v in attr_value.items():
                    add(k)
                    if isinstance(v, (list, tuple, set)):
                        for item in v:
                            add(item)
                    else:
                        add(v)
            elif isinstance(attr_value, (list, tuple, set)):
                for item in attr_value:
                    add(item)
            else:
                add(attr_value)

    if cleaned:
        return cleaned

    if isinstance(value, dict):
        for key in ("priority_categories", "notes", "role_gap_summary", "strategy_need_summary", "need_details"):
            attr_value = value.get(key)
            if isinstance(attr_value, (list, tuple, set)):
                for item in attr_value:
                    add(item)
            elif attr_value:
                add(attr_value)
        return cleaned

    if isinstance(value, (list, tuple, set)):
        for item in value:
            for sub in _v0951_clean_need_text(item):
                add(sub)
        return cleaned

    add(value)
    return cleaned


def _v0951_get_replacement_needs_from_context(context: dict) -> list[str]:
    needs: list[str] = []

    for key in ("replacement_needs", "replacement_need_profile", "replacement_candidate_needs", "needs", "replacement_profile"):
        for need in _v0951_clean_need_text(context.get(key)):
            if need not in needs:
                needs.append(need)

    # If the only thing available was an empty summary object, provide a readable fallback reason.
    if not needs:
        summary = (
            context.get("replacement_needs")
            or context.get("replacement_need_profile")
            or context.get("replacement_candidate_needs")
            or context.get("replacement_profile")
        )
        if summary is not None:
            notes = _v0951_clean_need_text(getattr(summary, "notes", None))
            for note in notes:
                if note not in needs:
                    needs.append(note)

    if not needs:
        needs.append("No urgent replacement category detected")

    return needs[:8]


def _v0951_full_pool_category_for_need(need: str) -> str:
    low = need.lower()
    if "no urgent" in low or "no active replacement" in low:
        return "General role coverage only if the pilot wants outside-card options"
    if "ramp" in low or "mana" in low:
        return "More ramp / mana development"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "removal" in low or "interaction" in low:
        return "More targeted interaction"
    if "wipe" in low or "board clear" in low:
        return "More board wipes"
    if "protection" in low or "protect" in low:
        return "More protection"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "token" in low:
        return "More token support"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "finisher" in low or "win" in low:
        return "More finishers"
    if "role" in low or "coverage" in low:
        return "Better role coverage"
    return "Better role coverage"


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

# v0.9.5.2-dev — Exact Full-Pool Candidate Preview
def _v0952_exact_preview_pool() -> dict[str, list[str]]:
    # Conservative, role-based examples only. These are not automatic swaps.
    return {
        "More ramp / mana development": [
            "Arcane Signet",
            "Nature's Lore",
            "Three Visits",
            "Farseek",
            "Talisman cycle / Signet cycle",
        ],
        "More card draw / card advantage": [
            "Guardian Project",
            "Beast Whisperer",
            "Return of the Wildspeaker",
            "Rishkar's Expertise",
            "Esper Sentinel",
        ],
        "More targeted interaction": [
            "Beast Within",
            "Generous Gift",
            "Swords to Plowshares",
            "Chaos Warp",
            "Assassin's Trophy",
        ],
        "More board wipes": [
            "Blasphemous Act",
            "Farewell",
            "Austere Command",
            "Toxic Deluge",
            "Cyclonic Rift",
        ],
        "More protection": [
            "Heroic Intervention",
            "Teferi's Protection",
            "Flawless Maneuver",
            "Tamiyo's Safekeeping",
            "Swiftfoot Boots",
        ],
        "More confirmed Dragon support": [
            "Dragon Tempest",
            "Scourge of Valkas",
            "Lathliss, Dragon Queen",
            "Sarkhan's Triumph",
            "Crucible of Fire",
        ],
        "More token support": [
            "Parallel Lives",
            "Anointed Procession",
            "Second Harvest",
            "Adrix and Nev, Twincasters",
            "Mondrak, Glory Dominus",
        ],
        "More recursion": [
            "Eternal Witness",
            "Regrowth",
            "Victimize",
            "Reanimate",
            "Sevinne's Reclamation",
        ],
        "More finishers": [
            "Craterhoof Behemoth",
            "Overwhelming Stampede",
            "Finale of Devastation",
            "Torment of Hailfire",
            "Triumph of the Hordes",
        ],
        "Better role coverage": [
            "Flexible removal",
            "Additional card draw",
            "Efficient ramp",
            "Protection for key engine pieces",
            "A cleaner finisher",
        ],
        "General role coverage only if the pilot wants outside-card options": [
            "Flexible removal",
            "Additional card draw",
            "Efficient ramp",
            "Protection for key engine pieces",
            "A cleaner finisher",
        ],
        "Combo support only if user opts in": [
            "No exact combo card examples shown unless combo optimization is explicitly enabled",
        ],
    }


def _v0952_candidate_examples_for_category(category: str) -> list[str]:
    pool = _v0952_exact_preview_pool()
    if category in pool:
        return pool[category]
    low = category.lower()
    if "dragon" in low:
        return pool["More confirmed Dragon support"]
    if "ramp" in low or "mana" in low:
        return pool["More ramp / mana development"]
    if "draw" in low or "advantage" in low:
        return pool["More card draw / card advantage"]
    if "interaction" in low or "removal" in low:
        return pool["More targeted interaction"]
    if "protection" in low:
        return pool["More protection"]
    if "token" in low:
        return pool["More token support"]
    if "recursion" in low or "graveyard" in low:
        return pool["More recursion"]
    if "finisher" in low or "win" in low:
        return pool["More finishers"]
    return pool["Better role coverage"]



def _v0952_insert_exact_full_pool_preview(report_text: str) -> str:
    if "### Exact Full-Pool Candidate Preview" in report_text:
        return report_text
    if not _v0952_should_show_exact_preview(report_text):
        return report_text

    start = report_text.find("## Full-Card-Pool Fallback Preview")
    end = report_text.find("\n## ", start + 1)
    if start == -1:
        return report_text
    section_end = end if end != -1 else len(report_text)
    section = report_text[start:section_end]

    category_lines = []
    in_categories = False
    for line in section.splitlines():
        if line.strip() == "### Fallback Categories to Explore Later":
            in_categories = True
            continue
        if in_categories and line.startswith("### "):
            break
        if in_categories and line.startswith("- "):
            category = line[2:].split(" — triggered by:", 1)[0].strip()
            if category and category not in category_lines:
                category_lines.append(category)

    if not category_lines:
        category_lines = ["Better role coverage"]

    preview_lines: list[str] = []
    preview_lines.append("### Exact Full-Pool Candidate Preview")
    preview_lines.append("> v0.9.5.2 preview: These are outside-card examples by role, not owned-card claims, not upgrade guarantees, and not automatic swaps.")
    preview_lines.append("> Check color identity, budget, bracket, collection availability, and pilot intent before treating any card as a real recommendation.")
    preview_lines.append("")

    for category in category_lines[:6]:
        preview_lines.append(f"#### {category}")
        for card in _v0952_candidate_examples_for_category(category)[:5]:
            preview_lines.append(f"- {card}")
        preview_lines.append("")

    preview_lines.append("### Exact Preview Safety Boundaries")
    preview_lines.append("- These card names are examples for exploration, not finalized replacement recommendations.")
    preview_lines.append("- Collection-first remains primary when owned cards are real fits.")
    preview_lines.append("- Automatic swaps: No.")
    preview_lines.append("- Combo-card examples stay suppressed unless combo optimization is explicitly enabled.")
    preview_lines.append("")

    insert_text = "\n".join(preview_lines)
    # Insert before Safety Boundaries inside the fallback preview when possible.
    safety = section.find("### Safety Boundaries")
    if safety != -1:
        new_section = section[:safety] + insert_text + "\n" + section[safety:]
    else:
        new_section = section.rstrip() + "\n\n" + insert_text

    return report_text[:start] + new_section + report_text[section_end:]

# v0.9.5.3-dev — Exact Preview Color Identity / Commander Legality Guard
def _v0953_card_color_identity_map() -> dict[str, set[str]]:
    # Conservative examples used by v0.9.5.2 exact preview.
    # Empty set means colorless or effectively color-identity flexible for the preview.
    return {
        "Arcane Signet": set(),
        "Nature's Lore": {"G"},
        "Three Visits": {"G"},
        "Farseek": {"G"},
        "Talisman cycle / Signet cycle": set(),

        "Guardian Project": {"G"},
        "Beast Whisperer": {"G"},
        "Return of the Wildspeaker": {"G"},
        "Rishkar's Expertise": {"G"},
        "Esper Sentinel": {"W"},

        "Beast Within": {"G"},
        "Generous Gift": {"W"},
        "Swords to Plowshares": {"W"},
        "Chaos Warp": {"R"},
        "Assassin's Trophy": {"B", "G"},

        "Blasphemous Act": {"R"},
        "Farewell": {"W"},
        "Austere Command": {"W"},
        "Toxic Deluge": {"B"},
        "Cyclonic Rift": {"U"},

        "Heroic Intervention": {"G"},
        "Teferi's Protection": {"W"},
        "Flawless Maneuver": {"W"},
        "Tamiyo's Safekeeping": {"G"},
        "Swiftfoot Boots": set(),

        "Dragon Tempest": {"R"},
        "Scourge of Valkas": {"R"},
        "Lathliss, Dragon Queen": {"R"},
        "Sarkhan's Triumph": {"R"},
        "Crucible of Fire": {"R"},

        "Parallel Lives": {"G"},
        "Anointed Procession": {"W"},
        "Second Harvest": {"G"},
        "Adrix and Nev, Twincasters": {"G", "U"},
        "Mondrak, Glory Dominus": {"W"},

        "Eternal Witness": {"G"},
        "Regrowth": {"G"},
        "Victimize": {"B"},
        "Reanimate": {"B"},
        "Sevinne's Reclamation": {"W"},

        "Craterhoof Behemoth": {"G"},
        "Overwhelming Stampede": {"G"},
        "Finale of Devastation": {"G"},
        "Torment of Hailfire": {"B"},
        "Triumph of the Hordes": {"G"},

        "Flexible removal": set(),
        "Additional card draw": set(),
        "Efficient ramp": set(),
        "Protection for key engine pieces": set(),
        "A cleaner finisher": set(),
        "No exact combo card examples shown unless combo optimization is explicitly enabled": set(),
    }


def _v0953_extract_commander_color_identity(report_text: str) -> set[str] | None:
    for line in report_text.splitlines():
        if line.startswith("- Commander color identity:"):
            raw = line.split(":", 1)[1].strip()
            if not raw or raw.lower() in {"none", "colorless", "c"}:
                return set()
            parts = [part.strip().upper() for part in raw.replace("/", " ").replace(",", " ").split()]
            colors = {part for part in parts if part in {"W", "U", "B", "R", "G"}}
            return colors
    return None


def _v0953_card_is_color_legal(card_name: str, commander_identity: set[str] | None) -> tuple[bool, str]:
    if commander_identity is None:
        return True, "color identity not verified"
    card_map = _v0953_card_color_identity_map()
    card_identity = card_map.get(card_name)
    if card_identity is None:
        return True, "color identity not verified"
    if card_identity.issubset(commander_identity):
        return True, "color identity verified"
    return False, "filtered by commander color identity"


def _v0953_rebuild_exact_preview_with_color_guard(report_text: str) -> str:
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return report_text

    section_end_marker = "### Exact Preview Safety Boundaries"
    safety_start = report_text.find(section_end_marker, start)
    if safety_start == -1:
        return report_text

    end = report_text.find("\n## ", start)
    if end == -1:
        end = len(report_text)

    exact_body = report_text[start:safety_start]
    safety_and_after = report_text[safety_start:end]

    commander_identity = _v0953_extract_commander_color_identity(report_text)
    commander_label = "not verified" if commander_identity is None else ("/".join(sorted(commander_identity)) if commander_identity else "Colorless")

    lines: list[str] = []
    lines.append("### Exact Full-Pool Candidate Preview")
    lines.append("> v0.9.5.3 preview: These are outside-card examples by role, not owned-card claims, not upgrade guarantees, and not automatic swaps.")
    lines.append("> Color identity is filtered when the commander's color identity is available from the report.")
    lines.append(f"> Commander color identity check: {commander_label}.")
    lines.append("")

    current_category = None
    categories: list[tuple[str, list[str]]] = []
    for line in exact_body.splitlines():
        if line.startswith("#### "):
            current_category = line[5:].strip()
            categories.append((current_category, []))
            continue
        if line.startswith("- ") and current_category and categories:
            card = line[2:].strip()
            # Skip safety/boundary list lines accidentally captured.
            if card and not card.lower().startswith(("these card names", "collection-first", "automatic swaps", "combo-card")):
                categories[-1][1].append(card)

    filtered_any = False
    unverified_any = False

    for category, cards in categories:
        legal_cards: list[tuple[str, str]] = []
        for card in cards:
            ok, status = _v0953_card_is_color_legal(card, commander_identity)
            if not ok:
                filtered_any = True
                continue
            if status == "color identity not verified":
                unverified_any = True
            legal_cards.append((card, status))

        if not legal_cards:
            lines.append(f"#### {category}")
            lines.append("- No exact examples shown after color-identity filtering.")
            lines.append("")
            continue

        lines.append(f"#### {category}")
        for card, status in legal_cards[:5]:
            lines.append(f"- {card} ({status})")
        lines.append("")

    # Rebuild safety section with explicit v0.9.5.3 guard text.
    safety_lines = []
    safety_lines.append("### Exact Preview Safety Boundaries")
    safety_lines.append("- These card names are examples for exploration, not finalized replacement recommendations.")
    safety_lines.append("- Collection-first remains primary when owned cards are real fits.")
    safety_lines.append("- Automatic swaps: No.")
    safety_lines.append("- Exact preview cards are not claimed as owned or collection-sourced.")
    safety_lines.append("- Color identity filtering is applied when the report exposes commander color identity.")
    if filtered_any:
        safety_lines.append("- Some exact examples were filtered out by commander color identity.")
    if unverified_any:
        safety_lines.append("- Some exact examples are marked color identity not verified and require pilot/manual review.")
    safety_lines.append("- Combo-card examples stay suppressed unless combo optimization is explicitly enabled.")
    safety_lines.append("")

    new_section = "\n".join(lines + safety_lines)
    return report_text[:start] + new_section + report_text[end:]

# v0.9.5.4-dev — Exact Preview Budget / Bracket Safety Labels
def _v0954_card_pressure_tags(card_name: str) -> list[str]:
    tags: list[str] = []

    high_budget = {
        "Three Visits",
        "Esper Sentinel",
        "Cyclonic Rift",
        "Teferi's Protection",
        "Flawless Maneuver",
        "Parallel Lives",
        "Anointed Procession",
        "Mondrak, Glory Dominus",
        "Craterhoof Behemoth",
        "Finale of Devastation",
        "Reanimate",
        "Toxic Deluge",
        "Assassin's Trophy",
        "Heroic Intervention",
    }

    bracket_pressure = {
        "Cyclonic Rift",
        "Teferi's Protection",
        "Esper Sentinel",
        "Toxic Deluge",
        "Reanimate",
        "Finale of Devastation",
        "Craterhoof Behemoth",
        "Torment of Hailfire",
        "Triumph of the Hordes",
        "Flawless Maneuver",
    }

    salt_or_table_fit = {
        "Cyclonic Rift",
        "Triumph of the Hordes",
        "Torment of Hailfire",
        "Craterhoof Behemoth",
        "Toxic Deluge",
        "Reanimate",
        "Teferi's Protection",
    }

    if card_name in high_budget:
        tags.append("budget not checked / may be expensive")
    else:
        tags.append("budget not checked")

    if card_name in bracket_pressure:
        tags.append("bracket pressure review")
    else:
        tags.append("bracket not checked")

    if card_name in salt_or_table_fit:
        tags.append("confirm table fit")
    else:
        tags.append("table fit not checked")

    return tags


def _v0954_add_budget_bracket_labels_to_exact_preview(report_text: str) -> str:
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return report_text

    section_end_marker = "### Exact Preview Safety Boundaries"
    safety_start = report_text.find(section_end_marker, start)
    if safety_start == -1:
        return report_text

    exact_body = report_text[start:safety_start]
    safety_end = report_text.find("\n## ", safety_start)
    if safety_end == -1:
        safety_end = len(report_text)

    lines: list[str] = []
    for line in exact_body.splitlines():
        if line.startswith("- ") and "(" in line and ")" in line:
            card_name = line[2:].split("(", 1)[0].strip()
            if card_name and not card_name.lower().startswith(("these card names", "collection-first", "automatic swaps", "combo-card")):
                if "budget not checked" not in line and "bracket" not in line and "table fit" not in line and "confirm table fit" not in line:
                    tags = "; ".join(_v0954_card_pressure_tags(card_name))
                    line = line.rstrip() + f" — {tags}"
        lines.append(line)

    rebuilt_exact_body = "\n".join(lines)

    safety_block = report_text[safety_start:safety_end]
    additions = []
    if "Budget status: not checked" not in safety_block:
        additions.append("- Budget status: not checked for exact full-pool examples.")
    if "Bracket/table-fit status: review required" not in safety_block:
        additions.append("- Bracket/table-fit status: review required before recommending exact examples.")
    if "Price data source: none" not in safety_block:
        additions.append("- Price data source: none.")
    if "Power-level guarantee: none" not in safety_block:
        additions.append("- Power-level guarantee: none; these remain exploratory examples.")

    if additions:
        safety_lines = safety_block.splitlines()
        insert_at = len(safety_lines)
        for i, existing in enumerate(safety_lines):
            if existing.strip() == "":
                insert_at = i
                break
        safety_lines = safety_lines[:insert_at] + additions + safety_lines[insert_at:]
        safety_block = "\n".join(safety_lines)

    return report_text[:start] + rebuilt_exact_body + safety_block + report_text[safety_end:]

# v0.9.5.5-dev — Exact Preview Role-to-Need Alignment Cleanup
def _v0955_need_to_exact_preview_category(need_text: str) -> str:
    low = str(need_text or "").lower()

    if "table-stabilizing" in low or "interaction" in low or "removal" in low:
        return "More targeted interaction"
    if "board wipe" in low or "wipe" in low or "clear" in low:
        return "More board wipes"
    if "board protection" in low or "protection" in low or "protect" in low:
        return "More protection"
    if "evasion" in low or "trample" in low:
        return "More finishers"
    if "combat finisher" in low or "combat payoff" in low or "finisher" in low:
        return "More finishers"
    if "token" in low or "go-wide" in low:
        return "More token support"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "ramp" in low or "mana" in low or "land" in low:
        return "More ramp / mana development"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "no urgent" in low or "general" in low or "broad" in low or "role coverage" in low:
        return "General role coverage only if the pilot wants outside-card options"
    return "Better role coverage"


def _v0955_extract_report_need_lines(report_text: str) -> list[str]:
    needs: list[str] = []

    # Prefer explicit Replacement / Addition Needs section.
    start = report_text.find("## Replacement / Addition Needs")
    if start != -1:
        end = report_text.find("\n## ", start + 1)
        section = report_text[start:end if end != -1 else len(report_text)]
        for line in section.splitlines():
            if not line.startswith("- "):
                continue
            item = line[2:].strip()
            if not item or item.lower().startswith("note:"):
                continue
            if item not in needs:
                needs.append(item)

    # Fallback to Replacement Need Profile role/strategy summaries.
    if not needs:
        for heading in ("### Role Gap Summary", "### Strategy-Specific Need Summary"):
            start = report_text.find(heading)
            if start == -1:
                continue
            end = report_text.find("\n### ", start + 1)
            if end == -1:
                end = report_text.find("\n## ", start + 1)
            section = report_text[start:end if end != -1 else len(report_text)]
            for line in section.splitlines():
                if line.startswith("- "):
                    item = line[2:].split("(", 1)[0].strip()
                    if item and item not in needs:
                        needs.append(item)

    return needs[:10]


def _v0955_existing_exact_categories(report_text: str) -> set[str]:
    categories: set[str] = set()
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return categories
    end = report_text.find("### Exact Preview Safety Boundaries", start)
    section = report_text[start:end if end != -1 else len(report_text)]
    for line in section.splitlines():
        if line.startswith("#### "):
            categories.add(line[5:].strip())
    return categories


def _v0955_build_category_block(category: str) -> list[str]:
    lines: list[str] = []
    lines.append(f"#### {category}")
    examples = []
    if "_v0952_candidate_examples_for_category" in globals():
        try:
            examples = list(_v0952_candidate_examples_for_category(category) or [])
        except Exception:
            examples = []
    if not examples:
        examples = ["Flexible removal", "Additional card draw", "Efficient ramp", "Protection for key engine pieces", "A cleaner finisher"]

    for card in examples[:5]:
        status = "color identity not verified"
        if "_v0953_card_is_color_legal" in globals():
            # Cannot reliably pass commander identity here without re-parsing full text inside this helper.
            # v0.9.5.3 rebuild will run before/inside the final chain; v0.9.5.5 adds role alignment first then reuses v0.9.5.4 labels later.
            status = "color identity not verified"
        tags = ""
        if "_v0954_card_pressure_tags" in globals():
            try:
                tags = "; ".join(_v0954_card_pressure_tags(card))
            except Exception:
                tags = "budget not checked; bracket not checked; table fit not checked"
        else:
            tags = "budget not checked; bracket not checked; table fit not checked"
        lines.append(f"- {card} ({status}) — {tags}")
    lines.append("")
    return lines


def _v0955_improve_exact_preview_role_alignment(report_text: str) -> str:
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return report_text

    safety_start = report_text.find("### Exact Preview Safety Boundaries", start)
    if safety_start == -1:
        return report_text

    existing_categories = _v0955_existing_exact_categories(report_text)
    need_lines = _v0955_extract_report_need_lines(report_text)
    mapped_categories: list[str] = []

    for need in need_lines:
        category = _v0955_need_to_exact_preview_category(need)
        if category not in mapped_categories:
            mapped_categories.append(category)

    # If the report only had vague/general exact categories but actual needs exist,
    # insert up to three more specific need-aligned categories before safety boundaries.
    specific_categories = [
        c for c in mapped_categories
        if c not in {
            "Better role coverage",
            "General role coverage only if the pilot wants outside-card options",
        }
    ]

    categories_to_add = [c for c in specific_categories if c not in existing_categories][:3]
    if not categories_to_add:
        return report_text

    insertion: list[str] = []
    insertion.append("### Need-Aligned Exact Preview Addendum")
    insertion.append("> v0.9.5.5 cleanup: These examples are mapped from detected replacement needs so the exact preview is less generic. They remain exploratory examples only.")
    insertion.append("")

    for category in categories_to_add:
        insertion.extend(_v0955_build_category_block(category))

    insertion_text = "\n".join(insertion)
    return report_text[:safety_start] + insertion_text + "\n" + report_text[safety_start:]

# v0.9.5.5.1-dev — Need-Aligned Addendum Anchor Hotfix
def _v09551_need_to_exact_preview_category(need_text: str) -> str:
    low = str(need_text or "").lower()

    if "table-stabilizing" in low or "interaction" in low or "removal" in low:
        return "More targeted interaction"
    if "board wipe" in low or "wipe" in low or "clear" in low:
        return "More board wipes"
    if "board protection" in low:
        return "More protection"
    if "protection" in low or "protect" in low:
        return "More protection"
    if "evasion" in low or "trample" in low:
        return "More finishers"
    if "combat finisher" in low or "combat payoff" in low or "finisher" in low:
        return "More finishers"
    if "token" in low or "go-wide" in low:
        return "More token support"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "ramp" in low or "mana" in low or "land" in low:
        return "More ramp / mana development"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "no urgent" in low or "general" in low or "broad" in low or "role coverage" in low:
        return "General role coverage only if the pilot wants outside-card options"
    return "Better role coverage"


def _v09551_extract_replacement_addition_needs(report_text: str) -> list[str]:
    needs: list[str] = []

    start = report_text.find("## Replacement / Addition Needs")
    if start != -1:
        end = report_text.find("\n## ", start + 1)
        section = report_text[start:end if end != -1 else len(report_text)]
        for line in section.splitlines():
            if not line.startswith("- "):
                continue
            item = line[2:].strip()
            if not item:
                continue
            if item.lower().startswith("note:"):
                continue
            if "no urgent replacement category" in item.lower():
                continue
            if item not in needs:
                needs.append(item)

    if not needs:
        for heading in ("### Role Gap Summary", "### Strategy-Specific Need Summary"):
            start = report_text.find(heading)
            if start == -1:
                continue
            next_h2 = report_text.find("\n## ", start + 1)
            next_h3 = report_text.find("\n### ", start + len(heading))
            candidates = [idx for idx in (next_h2, next_h3) if idx != -1]
            end = min(candidates) if candidates else len(report_text)
            section = report_text[start:end]
            for line in section.splitlines():
                if not line.startswith("- "):
                    continue
                item = line[2:].split("(", 1)[0].strip()
                if item and item not in needs:
                    needs.append(item)

    return needs[:10]



def _v09551_make_card_line(card: str) -> str:
    status = "color identity not verified"
    tags = "budget not checked; bracket not checked; table fit not checked"
    if "_v0954_card_pressure_tags" in globals():
        try:
            tags = "; ".join(_v0954_card_pressure_tags(card))
        except Exception:
            pass
    return f"- {card} ({status}) — {tags}"


def _v09551_examples_for_category(category: str) -> list[str]:
    if "_v0952_candidate_examples_for_category" in globals():
        try:
            examples = list(_v0952_candidate_examples_for_category(category) or [])
            if examples:
                return examples[:5]
        except Exception:
            pass
    fallback = {
        "More targeted interaction": ["Beast Within", "Generous Gift", "Swords to Plowshares", "Chaos Warp", "Assassin's Trophy"],
        "More board wipes": ["Blasphemous Act", "Farewell", "Austere Command", "Toxic Deluge", "Cyclonic Rift"],
        "More protection": ["Heroic Intervention", "Teferi's Protection", "Flawless Maneuver", "Tamiyo's Safekeeping", "Swiftfoot Boots"],
        "More finishers": ["Craterhoof Behemoth", "Overwhelming Stampede", "Finale of Devastation", "Torment of Hailfire", "Triumph of the Hordes"],
        "More token support": ["Parallel Lives", "Anointed Procession", "Second Harvest", "Adrix and Nev, Twincasters", "Mondrak, Glory Dominus"],
        "More card draw / card advantage": ["Guardian Project", "Beast Whisperer", "Return of the Wildspeaker", "Rishkar's Expertise", "Esper Sentinel"],
        "More ramp / mana development": ["Arcane Signet", "Nature's Lore", "Three Visits", "Farseek", "Talisman cycle / Signet cycle"],
        "More recursion": ["Eternal Witness", "Regrowth", "Victimize", "Reanimate", "Sevinne's Reclamation"],
        "More confirmed Dragon support": ["Dragon Tempest", "Scourge of Valkas", "Lathliss, Dragon Queen", "Sarkhan's Triumph", "Crucible of Fire"],
    }
    return fallback.get(category, ["Flexible removal", "Additional card draw", "Efficient ramp", "Protection for key engine pieces", "A cleaner finisher"])[:5]


def _v09551_force_need_aligned_addendum_after_exact_preview(report_text: str) -> str:
    if "### Exact Full-Pool Candidate Preview" not in report_text:
        return report_text
    if "### Need-Aligned Exact Preview Addendum" in report_text:
        return report_text

    needs = _v09551_extract_replacement_addition_needs(report_text)
    if not needs:
        return report_text

    categories: list[str] = []
    for need in needs:
        cat = _v09551_need_to_exact_preview_category(need)
        if cat not in categories and cat not in {
            "Better role coverage",
            "General role coverage only if the pilot wants outside-card options",
        }:
            categories.append(cat)

    if not categories:
        return report_text

    exact_start = report_text.find("### Exact Full-Pool Candidate Preview")
    safety_start = report_text.find("### Exact Preview Safety Boundaries", exact_start)
    if safety_start == -1:
        return report_text

    exact_block = report_text[exact_start:safety_start]
    existing_categories = set(_v09551_exact_preview_categories(exact_block))
    categories_to_add = [cat for cat in categories if cat not in existing_categories][:4]
    if not categories_to_add:
        return report_text

    addendum: list[str] = []
    addendum.append("### Need-Aligned Exact Preview Addendum")
    addendum.append("> v0.9.5.5.1 hotfix: These examples are mapped directly from detected replacement needs so the exact preview is not stuck on generic role coverage. They remain exploratory examples only.")
    addendum.append("")

    for category in categories_to_add:
        addendum.append(f"#### {category}")
        for card in _v09551_examples_for_category(category):
            addendum.append(_v09551_make_card_line(card))
        addendum.append("")

    addendum_text = "\n".join(addendum)
    return report_text[:safety_start] + addendum_text + "\n" + report_text[safety_start:]

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
        "> Dragon's Touch note: this report is a player-facing handoff packet. Treat recommendations as review guidance and keep the pilot's stated intent as the final authority.",
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
        requested_optional_cut_target = runtime_config.cut_depth_config.get("optional_cut_target", 5)
        if parsed.deck_card_count < 100:
            lines.append(f"- Optional cut target setting: {requested_optional_cut_target} (paused while deck is under 100; addition-first review is active)")
        else:
            lines.append(f"- Optional cut target: {requested_optional_cut_target}")
    lines.append(f"- Intended bracket: {getattr(runtime_config, 'intended_bracket', 'Not sure yet')}")
    lines.append(f"- Budget note: {getattr(runtime_config, 'budget_note', 'No budget note provided')}")

    lines += _section("User-Facing Boundaries")
    lines.extend([
        "- This report is guidance for review, not an automatic deck edit list.",
        "- Required cuts mean legality or deck-size pressure; optional optimization candidates are not mandatory.",
        "- If illegal duplicates, color-identity issues, banned cards, or companion issues exist, resolve those legality concerns before treating ordinary cut candidates as required.",
        "- Collection-mode recommendations are bounded by the selected collection setting; collection-only mode must not present outside cards as available swaps.",
        "- Philosophy/persona language changes explanation style and priorities only; it does not override legality, pilot intent, budget, collection mode, color identity, or deck evidence.",
        "- Combo Awareness is included when combo data is available; raw Combo Spellbook/API debug artifacts remain developer-facing support, not required pilot uploads.",
        "- The desktop Report Viewer shows generated markdown/text as plain readable text; deep markdown rendering and structured report parsing are deferred.",
    ])

    # v1.4.13 Strategy Knowledge Report / AI Handoff integration.
    # Presentation-only: does not generate decks, select exact cards, or make final inclusion decisions.
    strategy_knowledge_section = build_strategy_knowledge_report_section(context)
    if strategy_knowledge_section:
        lines.append("")
        lines.append(strategy_knowledge_section.rstrip())

    # v1.1.18 LIVE REPORT PHILOSOPHY GUIDE SECTION HOOK
    # Use the v1.1 report-section formatter for the visible report Philosophy Guide.
    # The old v0.6.5.3 subtype summary remains fallback-only if v1.1 rendering fails.
    philosophy_context = context.get("philosophy_context")
    if philosophy_context:
        live_philosophy_section = _v1118_build_live_report_philosophy_guide_section(context)
        if live_philosophy_section:
            lines.append("")
            lines.append(live_philosophy_section.rstrip())

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
        lines.append("")
        lines.append("> Duplicate legality note: illegal duplicate copies are first-pass legality fixes. If the deck is also over 100 cards, removing an extra illegal duplicate may be the cleanest way to resolve both duplicate legality and deck-size pressure.")

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

    lines += _section("Possible Off-Plan / Manual Context Review Examples")
    lines.append("> These are cards flagged for pilot/context review, not automatic cuts. Some may later be protected by v1.1 philosophy, commander, synergy, or role-context logic elsewhere in this report.")
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

    # Additive 4-player pod-value section (multiplayer_signal). Self-contained and
    # defensive: returns '' if the summary is absent, so it can never break the report.
    multiplayer_section = build_multiplayer_report_section(context)
    if multiplayer_section:
        lines.append("")
        lines.append(multiplayer_section.rstrip())

    # Additive Section-3 political-archetype section. Self-contained and defensive:
    # returns '' if the deck is not political, so it can never break the report.
    political_section = build_political_report_section(context)
    if political_section:
        lines.append("")
        lines.append(political_section.rstrip())

    lines += _section("Cut Pressure Review")
    lines.extend([
        f"- Deck size status: {cut_pressure.status}",
        f"- Current deck size: {cut_pressure.deck_card_count}",
        f"- Required cuts: {cut_pressure.required_cuts}",
        f"- Short cards: {cut_pressure.short_cards}",
        (f"- Optional cut target currently reviewed: 0 (paused while deck is under 100; requested optional target: {runtime_config.cut_depth_config.get('optional_cut_target', 5)})" if cut_pressure.deck_card_count < 100 else f"- Optional cut target: {cut_pressure.optional_cut_target}"),
        f"- Cut mode: {cut_pressure.cut_mode}",
    ])
    lines.extend(_none_or_items(cut_pressure.notes + possible.notes))
    lines.append("")
    lines.append("> Cut wording note: required cuts are legality/deck-size pressure only. Optional optimization candidates are not mandatory; they are the cards most worth reviewing based on role fit, redundancy, curve pressure, and the deck's actual plan.")
    if getattr(legality, "illegal_duplicate_cards", None):
        lines.append("> If duplicate legality issues are present, resolve those duplicate copies first when they also help the deck reach legal size.")

    lines.extend(_duplicate_legality_first_pass_lines(context))

    lines += _section("Required Cut / Legality Review Candidates")
    lines.append("> These are non-duplicate review candidates for resolving required legality/deck-size pressure. If the Duplicate Legality First-Pass Fixes section appears above, review that section first before treating any ordinary card here as a mandatory cut.")
    lines.extend(_format_cut_entries(possible.required_cut_candidates, "No required cut candidates in this checkpoint.", context=context, explanation_kind="cut"))

    lines += _section("Optional Optimization Review Candidates")
    lines.append("> These are not required cuts. They are optional review candidates for tuning, consistency, role balance, and table fit.")
    lines.extend(_format_cut_entries(possible.optional_cut_candidates, "No optional optimization candidates in this checkpoint.", context=context, explanation_kind="cut"))

    lines += _section("Manual Review Candidates")
    lines.extend(_format_cut_entries(possible.manual_review_candidates, "No manual-review cut candidates in this checkpoint.", limit=10, context=context, explanation_kind="cut"))

    lines += _section("Protected From Cut Examples")
    lines.extend(_format_cut_entries(possible.protected_from_cut, "No protected-card examples in this checkpoint.", limit=10, context=context, explanation_kind="protected"))

    lines.extend(_build_replacement_need_profile_section(context))

    lines += _section("Replacement / Addition Needs")
    if replacement.priority_categories:
        for category in replacement.priority_categories:
            lines.append(f"- {category}")
            # v1.1.19.1: replacement-direction explanation text is kept in the richer
            # Replacement Need Profile details above. Do not repeat shorter duplicate
            # v1.1 replacement-direction lines in this summary list.
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

    lines.extend(_build_replacement_candidate_engine_preview_section(context))
    lines.extend(_build_collection_pull_section(context))
    lines.extend(_v095_build_full_pool_preview_lines(context))

    lines += _section("Parser Hygiene")
    lines.extend([
        f"- Reference/non-mainboard cards ignored: {parsed.reference_card_count}",
        f"- Ignored/unparsed lines: {len(parsed.ignored_lines)}",
    ])
    if parsed.ignored_lines:
        lines.append("- Ignored line examples:")
        for ignored in parsed.ignored_lines[:10]:
            lines.append(f"  - `{ignored}`")

    return apply_normal_report_postprocessors(_v09551_force_need_aligned_addendum_after_exact_preview(_v0954_add_budget_bracket_labels_to_exact_preview(_v0953_rebuild_exact_preview_with_color_guard(_v0952_insert_exact_full_pool_preview(_v0951_replace_full_pool_preview_section(_v094610_suppress_dragon_gate_from_strong_owned_text("\n".join(lines)), context))))).rstrip() + "\n")


def write_normal_report(deck_folder: Path, deck_name: str, context: dict[str, Any]) -> Path:
    path = get_unique_output_path(deck_folder, f"{deck_name}_deck_report", ".md")
    write_text_file(path, build_normal_report(context))
    return path
