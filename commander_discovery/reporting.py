"""Commander Discovery report/export helpers.

v1.2.3 adds a markdown report preview for The Commander's Call. This module is
safe to import and test in isolation. It does not load collection files by
itself, execute UI scans, modify normal deck-review reports, or change scoring.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any

from .filters import (
    CommanderCandidateFilterOptions,
    filter_commander_candidates,
    summarize_candidate_filters,
)
from .discovery import group_candidates_by_color_identity
from .models import CommanderCandidate, CommanderDiscoveryScanResult

DEFAULT_COMMANDER_DISCOVERY_REPORT_NAME = "commander_discovery_report.md"


def build_commander_discovery_report(
    scan_result: CommanderDiscoveryScanResult | Iterable[CommanderCandidate],
    *,
    title: str = "The Commander's Call — Commander Discovery Report",
) -> str:
    """Build a markdown Commander Discovery report from scan output or candidates.

    The report is intentionally limited to discovery/export preview information:
    owned commander candidates, color identity groups, quantities, source files,
    and manual-review notes. It does not build a 100-card deck shell.
    """
    result = _coerce_scan_result(scan_result)
    candidates = list(result.candidates)
    mvp_candidates = [candidate for candidate in candidates if candidate.is_mvp_eligible]
    manual_review_candidates = [
        candidate for candidate in candidates
        if candidate.eligibility_status == "manual_review" or candidate.is_special_rule_candidate
    ]

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Commander Discovery Summary")
    lines.append("")
    lines.append(f"- Commander candidates found: {len(candidates)}")
    lines.append(f"- MVP Legendary Creature candidates: {len(mvp_candidates)}")
    lines.append(f"- Manual-review special-rule candidates: {len(manual_review_candidates)}")
    lines.append(f"- Total collection entries scanned: {result.total_collection_entries}")
    lines.append(f"- Unique collection cards resolved: {result.resolved_collection_cards}")
    lines.append(f"- Unresolved collection cards: {result.unresolved_collection_cards}")
    lines.append(f"- Skipped non-commander cards: {result.skipped_nonlegendary_cards}")
    lines.append("")
    lines.append("## MVP Boundary")
    lines.append("")
    lines.append("- This report answers: What commanders do I already own?")
    lines.append("- MVP eligible means Scryfall metadata identifies the card as a Legendary Creature.")
    lines.append("- Special command-zone rules are surfaced for manual review instead of being over-promised.")
    lines.append("- This report does not build a full 100-card deck shell.")
    lines.append("- This report does not recommend cuts or replacements.")
    lines.append("")

    if result.warnings:
        lines.append("## Scanner Warnings")
        lines.append("")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Commander Candidates by Color Identity")
    lines.append("")
    if candidates:
        grouped = group_candidates_by_color_identity(candidates)
        for group_name, group in grouped.items():
            lines.append(f"### {group_name}")
            lines.append("")
            for candidate in group:
                lines.extend(_candidate_lines(candidate))
                lines.append("")
    else:
        lines.append("No commander candidates were found in the supplied scan result.")
        lines.append("")

    if manual_review_candidates:
        lines.append("## Manual Review Candidates")
        lines.append("")
        lines.append(
            "These cards were surfaced because they may use special or deferred command-zone rules. "
            "They should be reviewed before being treated as fully supported commanders."
        )
        lines.append("")
        for candidate in sorted(manual_review_candidates, key=lambda item: item.card_name.lower()):
            lines.extend(_manual_review_lines(candidate))
            lines.append("")

    lines.append("## Future Build-From-Collection Boundary")
    lines.append("")
    lines.append("v1.2 discovery/export is intentionally separate from v1.3 build-from-collection work.")
    lines.append("A later version can use this candidate list as the starting point for commander selection, collection-first support scoring, and build-around prompt generation.")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_commander_discovery_report(
    scan_result: CommanderDiscoveryScanResult | Iterable[CommanderCandidate],
    output_path: str | Path,
    *,
    title: str = "The Commander's Call — Commander Discovery Report",
) -> Path:
    """Write a Commander Discovery markdown report and return its path."""
    path = Path(output_path)
    if path.is_dir():
        path = path / DEFAULT_COMMANDER_DISCOVERY_REPORT_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_commander_discovery_report(scan_result, title=title), encoding="utf-8")
    return path


def _coerce_scan_result(
    value: CommanderDiscoveryScanResult | Iterable[CommanderCandidate],
) -> CommanderDiscoveryScanResult:
    if isinstance(value, CommanderDiscoveryScanResult):
        return value
    candidates = list(value)
    return CommanderDiscoveryScanResult(
        candidates=candidates,
        total_collection_entries=len(candidates),
        unique_collection_cards=len(candidates),
        resolved_collection_cards=len(candidates),
        unresolved_collection_cards=0,
        skipped_nonlegendary_cards=0,
        manual_review_candidate_count=sum(1 for candidate in candidates if candidate.eligibility_status == "manual_review"),
        mvp_candidate_count=sum(1 for candidate in candidates if candidate.is_mvp_eligible),
    )


def _candidate_lines(candidate: CommanderCandidate) -> list[str]:
    status_label = _status_label(candidate)
    quantity = f"x{candidate.owned_quantity}" if candidate.owned_quantity else "quantity unknown"
    line = f"- **{candidate.card_name}** ({quantity}) — {candidate.color_identity_text}; {status_label}"
    details = [line]
    if candidate.type_line:
        details.append(f"  - Type: {candidate.type_line}")
    if candidate.mana_value is not None:
        details.append(f"  - Mana value: {candidate.mana_value:g}")
    if candidate.commander_eligibility_reason:
        details.append(f"  - Discovery reason: {candidate.commander_eligibility_reason}")
    if candidate.special_commander_rule:
        details.append(f"  - Special rule note: {candidate.special_commander_rule}")
    if candidate.source_files:
        details.append(f"  - Source files: {', '.join(candidate.source_files)}")
    if candidate.oracle_text_preview:
        details.append(f"  - Oracle preview: {_single_line(candidate.oracle_text_preview)}")
    return details


def _manual_review_lines(candidate: CommanderCandidate) -> list[str]:
    lines = [f"- **{candidate.card_name}** — {candidate.color_identity_text}"]
    if candidate.special_commander_rule:
        lines.append(f"  - Special rule note: {candidate.special_commander_rule}")
    if candidate.manual_review_notes:
        for note in candidate.manual_review_notes:
            lines.append(f"  - Review note: {note}")
    elif candidate.commander_eligibility_reason:
        lines.append(f"  - Review note: {candidate.commander_eligibility_reason}")
    return lines


def _status_label(candidate: CommanderCandidate) -> str:
    if candidate.is_mvp_eligible:
        return "MVP eligible"
    if candidate.eligibility_status == "manual_review" or candidate.is_special_rule_candidate:
        return "manual review"
    return candidate.eligibility_status.replace("_", " ")


def _single_line(value: Any) -> str:
    return " ".join(str(value or "").split())


def build_filtered_commander_discovery_report(
    scan_result: CommanderDiscoveryScanResult | Iterable[CommanderCandidate],
    filter_options: CommanderCandidateFilterOptions | None = None,
    *,
    title: str = "The Commander's Call — Commander Discovery Filtered Candidate Preview",
) -> str:
    """Build a filtered Commander Discovery markdown preview.

    v1.2.4 keeps this as a report/export helper only. It narrows already-built
    Commander Discovery scan results and does not execute collection scanning,
    normal deck review, scoring, cuts, replacements, legality, or deck building.
    """
    if isinstance(scan_result, CommanderDiscoveryScanResult):
        result = scan_result
    elif hasattr(scan_result, "candidates"):
        source = scan_result
        result = CommanderDiscoveryScanResult(
            candidates=list(getattr(source, "candidates", [])),
            total_collection_entries=int(getattr(source, "total_collection_entries", 0) or 0),
            unique_collection_cards=int(getattr(source, "unique_collection_cards", 0) or 0),
            resolved_collection_cards=int(getattr(source, "resolved_collection_cards", 0) or 0),
            unresolved_collection_cards=int(getattr(source, "unresolved_collection_cards", 0) or 0),
            skipped_nonlegendary_cards=int(getattr(source, "skipped_nonlegendary_cards", 0) or 0),
            manual_review_candidate_count=int(getattr(source, "manual_review_candidate_count", 0) or 0),
            mvp_candidate_count=int(getattr(source, "mvp_candidate_count", 0) or 0),
            warnings=list(getattr(source, "warnings", []) or []),
        )
    else:
        result = _coerce_scan_result(scan_result)
    all_candidates = list(result.candidates)
    filtered_candidates = filter_commander_candidates(all_candidates, filter_options)
    filter_summary = summarize_candidate_filters(filter_options)

    filtered_result = CommanderDiscoveryScanResult(
        candidates=filtered_candidates,
        total_collection_entries=result.total_collection_entries,
        unique_collection_cards=result.unique_collection_cards,
        resolved_collection_cards=result.resolved_collection_cards,
        unresolved_collection_cards=result.unresolved_collection_cards,
        skipped_nonlegendary_cards=result.skipped_nonlegendary_cards,
        manual_review_candidate_count=sum(
            1 for candidate in filtered_candidates
            if candidate.eligibility_status == "manual_review" or candidate.is_special_rule_candidate
        ),
        mvp_candidate_count=sum(1 for candidate in filtered_candidates if candidate.is_mvp_eligible),
        warnings=list(result.warnings),
    )

    report = build_commander_discovery_report(filtered_result, title=title)
    header = [
        f"# {title}",
        "",
        "## Filter Preview Summary",
        "",
        f"- Filter summary: {filter_summary}",
        f"- Candidates before filters: {len(all_candidates)}",
        f"- Candidates after filters: {len(filtered_candidates)}",
        f"- Candidates hidden by filters: {max(0, len(all_candidates) - len(filtered_candidates))}",
        "",
    ]
    body = report.split("\n", 2)[2] if report.startswith("# ") and "\n" in report else report
    return "\n".join(header).rstrip() + "\n\n" + body.lstrip()

