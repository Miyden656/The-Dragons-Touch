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

def _filter_dragon_gate_from_strong_owned_candidates(candidates: object) -> list[object]:
    return [
        candidate for candidate in list(candidates or [])
        if not _candidate_dragon_gate_visible_adjusted(candidate)
    ]

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
