"""Guarded UI scan path for The Commander's Call.

v1.2.7 keeps the v1.2.6 guarded scan/report path and adds UI-friendly
candidate summaries so The Commander's Call page can populate a live result
list and selector after a scan completes.

This module still does not call main.py, does not run normal deck review, does
not use network/API access, and does not build a 100-card deck shell.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from data.collection_loader import CollectionLoadSummary, load_collection_sources
from data.scryfall_loader import ScryfallDataError, load_scryfall_lookup

from .collection_scanner import scan_collection_for_commanders
from .models import CommanderCandidate, CommanderDiscoveryScanResult
from .reporting import DEFAULT_COMMANDER_DISCOVERY_REPORT_NAME, write_commander_discovery_report


# Verifier/report filename marker: commander_discovery_report.md


@dataclass(slots=True)
class CommanderDiscoveryUiScanResult:
    """Result object returned to the UI after a guarded Commander Discovery scan."""

    success: bool = False
    message: str = ""
    report_path: str = ""
    output_folder: str = ""
    collection_files: list[str] = field(default_factory=list)
    collection_file_count: int = 0
    total_collection_entries: int = 0
    unique_collection_cards: int = 0
    commander_candidate_count: int = 0
    mvp_candidate_count: int = 0
    manual_review_candidate_count: int = 0
    unresolved_collection_cards: int = 0
    skipped_nonlegendary_cards: int = 0
    candidate_summaries: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    @classmethod
    def failure(cls, message: str, *, error: str = "", warnings: Sequence[str] | None = None) -> "CommanderDiscoveryUiScanResult":
        return cls(success=False, message=message, error=error, warnings=list(warnings or []))

    @classmethod
    def from_scan_result(
        cls,
        scan_result: CommanderDiscoveryScanResult,
        *,
        report_path: Path,
        output_folder: Path,
        collection_files: Sequence[str],
    ) -> "CommanderDiscoveryUiScanResult":
        """Build a UI result, including the Commander candidate result list."""
        return cls(
            success=True,
            message="Commander Discovery scan completed and report was written.",
            report_path=str(report_path),
            output_folder=str(output_folder),
            collection_files=[str(path) for path in collection_files],
            collection_file_count=len(collection_files),
            total_collection_entries=scan_result.total_collection_entries,
            unique_collection_cards=scan_result.unique_collection_cards,
            commander_candidate_count=scan_result.commander_candidate_count,
            mvp_candidate_count=scan_result.mvp_candidate_count,
            manual_review_candidate_count=scan_result.manual_review_candidate_count,
            unresolved_collection_cards=scan_result.unresolved_collection_cards,
            skipped_nonlegendary_cards=scan_result.skipped_nonlegendary_cards,
            candidate_summaries=[_candidate_to_ui_summary(candidate) for candidate in scan_result.candidates],
            warnings=list(scan_result.warnings),
        )

    def to_status_text(self) -> str:
        """Return a concise status block suitable for the Commander Discovery page."""
        if not self.success:
            lines = ["Commander Discovery scan did not complete.", f"- Reason: {self.message or 'Unknown failure'}"]
            if self.error:
                lines.append(f"- Error detail: {self.error}")
            for warning in self.warnings[:8]:
                lines.append(f"- Warning: {warning}")
            return "\n".join(lines)

        lines = [
            "Commander Discovery scan completed.",
            f"- Commander candidates found: {self.commander_candidate_count}",
            f"- MVP Legendary Creature candidates: {self.mvp_candidate_count}",
            f"- Manual-review candidates: {self.manual_review_candidate_count}",
            f"- Collection files scanned: {self.collection_file_count}",
            f"- Total collection entries scanned: {self.total_collection_entries}",
            f"- Unique collection cards resolved: {self.unique_collection_cards}",
            f"- Unresolved collection cards: {self.unresolved_collection_cards}",
            f"- Skipped non-commander cards: {self.skipped_nonlegendary_cards}",
            f"- Report written: {self.report_path}",
        ]
        if self.candidate_summaries:
            lines.append("")
            lines.append("Top discovered commander candidates:")
            for candidate in self.candidate_summaries[:8]:
                lines.append(f"- {candidate.get('display_label', candidate.get('card_name', 'Unknown'))}")
            if len(self.candidate_summaries) > 8:
                lines.append(f"- ...and {len(self.candidate_summaries) - 8} more candidate(s)")
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in self.warnings[:12]:
                lines.append(f"- {warning}")
            if len(self.warnings) > 12:
                lines.append(f"- ...and {len(self.warnings) - 12} more warning(s)")
        return "\n".join(lines)


def _candidate_to_ui_summary(candidate: CommanderCandidate) -> dict[str, Any]:
    """Return a compact, UI-safe summary for one commander candidate."""
    mana_value = candidate.mana_value
    if mana_value is None:
        mana_value_text = "MV ?"
    elif float(mana_value).is_integer():
        mana_value_text = f"MV {int(mana_value)}"
    else:
        mana_value_text = f"MV {mana_value}"

    status_text = "MVP eligible" if candidate.is_mvp_eligible else "Manual review"
    if candidate.eligibility_status and candidate.eligibility_status != "eligible":
        status_text = str(candidate.eligibility_status).replace("_", " ").title()

    display_label = (
        f"{candidate.card_name} | {candidate.color_identity_group or candidate.color_identity_text} | "
        f"{mana_value_text} | Qty {candidate.owned_quantity} | {status_text}"
    )
    return {
        "card_name": candidate.card_name,
        "display_label": display_label,
        "owned_quantity": candidate.owned_quantity,
        "color_identity": list(candidate.color_identity),
        "color_identity_text": candidate.color_identity_text,
        "color_identity_key": candidate.color_identity_key,
        "color_identity_group": candidate.color_identity_group,
        "color_count": candidate.color_count,
        "mana_value": candidate.mana_value,
        "mana_value_text": mana_value_text,
        "type_line": candidate.type_line,
        "oracle_text_preview": candidate.oracle_text_preview,
        "source_files": list(candidate.source_files),
        "commander_eligibility_reason": candidate.commander_eligibility_reason,
        "eligibility_status": candidate.eligibility_status,
        "eligibility_rule": candidate.eligibility_rule,
        "special_commander_rule": candidate.special_commander_rule,
        "manual_review_notes": list(candidate.manual_review_notes),
        "is_mvp_eligible": candidate.is_mvp_eligible,
        "is_special_rule_candidate": candidate.is_special_rule_candidate,
        "status_text": status_text,
    }


def resolve_commander_discovery_collection_files(state: Any) -> list[str]:
    """Resolve the UI's staged collection source into local files.

    Supported MVP sources:
    - Select collection files: uses state.selected_collection_files
    - Entire collection folder: scans local .txt and .csv files in state.collection_folder
    """
    source_mode = str(getattr(state, "collection_source_mode", "Entire collection folder") or "Entire collection folder")
    if source_mode == "Select collection files":
        return [str(Path(path)) for path in (getattr(state, "selected_collection_files", []) or []) if str(path).strip()]

    folder_text = str(getattr(state, "collection_folder", "") or "").strip()
    if not folder_text:
        return []
    folder = Path(folder_text).expanduser()
    if not folder.exists() or not folder.is_dir():
        return []
    files = sorted([*folder.glob("*.txt"), *folder.glob("*.csv")], key=lambda path: path.name.lower())
    return [str(path) for path in files if path.is_file()]


def commander_discovery_output_folder(state: Any, *, now_slug: str | None = None, output_root: str | Path | None = None) -> Path:
    """Return the isolated output folder for a Commander Discovery UI scan."""
    root = Path(output_root or getattr(state, "report_output_folder", "Outputs") or "Outputs")
    timestamp = now_slug or datetime.now().strftime("%Y%m%d_%H%M%S")
    return root / "commander_discovery" / timestamp


def run_guarded_commander_discovery_scan(
    state: Any,
    *,
    scryfall_file: str | Path | None = None,
    output_root: str | Path | None = None,
    now_slug: str | None = None,
) -> CommanderDiscoveryUiScanResult:
    """Run the isolated Commander Discovery scan and write a report.

    This is intentionally separate from the normal deck-review backend path.
    It uses local files only and returns a UI-friendly result object.
    """
    collection_files = resolve_commander_discovery_collection_files(state)
    if not collection_files:
        return CommanderDiscoveryUiScanResult.failure(
            "No local collection files are staged. Choose a collection folder or specific collection files first."
        )

    try:
        scryfall_cards, scryfall_lookup = load_scryfall_lookup(scryfall_file) if scryfall_file else load_scryfall_lookup()
    except ScryfallDataError as exc:
        return CommanderDiscoveryUiScanResult.failure(
            "Local Scryfall data could not be loaded. Run the Scryfall download/update tool first.",
            error=str(exc),
        )
    except Exception as exc:  # Defensive UI boundary; verifier still exercises the happy path.
        return CommanderDiscoveryUiScanResult.failure(
            "Unexpected error while loading local Scryfall data.",
            error=str(exc),
        )

    try:
        collection_summary: CollectionLoadSummary = load_collection_sources(
            collection_files,
            mode="prefer",
            scryfall_lookup=scryfall_lookup,
            source_mode=str(getattr(state, "collection_source_mode", "selected_files") or "selected_files"),
            collection_folder=getattr(state, "collection_folder", None),
            scryfall_cards=scryfall_cards,
        )
        if not collection_summary.loaded or collection_summary.unique_cards <= 0:
            return CommanderDiscoveryUiScanResult.failure(
                "Collection files were found, but no usable collection cards were loaded.",
                warnings=list(collection_summary.parse_warnings or []),
            )

        scan_result = scan_collection_for_commanders(collection_summary, scryfall_lookup)
        output_folder = commander_discovery_output_folder(state, now_slug=now_slug, output_root=output_root)
        report_path = write_commander_discovery_report(scan_result, output_folder / DEFAULT_COMMANDER_DISCOVERY_REPORT_NAME)
        return CommanderDiscoveryUiScanResult.from_scan_result(
            scan_result,
            report_path=report_path,
            output_folder=output_folder,
            collection_files=collection_files,
        )
    except Exception as exc:
        return CommanderDiscoveryUiScanResult.failure(
            "Unexpected error while scanning local collection files.",
            error=str(exc),
        )
