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
