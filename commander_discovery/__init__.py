"""Commander Discovery package for The Dragon's Touch.

v1.2.3 scope:
- Preserve the safe Commander Discovery module boundary.
- Add markdown report/export preview helpers.
- Do not execute scanner work from the UI yet.
- Do not change normal deck review reports, prompt generation, scoring, or selection.
"""

from .candidate_rules import (
    classify_commander_eligibility,
    get_commander_candidate_reason,
    get_special_commander_rule_note,
    is_basic_legendary_creature_candidate,
    is_commander_discovery_candidate,
)
from .collection_scanner import (
    scan_collection_for_commanders,
    scan_collection_for_legendary_creature_candidates,
)
from .discovery import discover_commander_candidates, group_candidates_by_color_identity
from .eligibility import CommanderEligibilityClassification
from .filters import (
    CommanderCandidateFilterOptions,
    candidate_matches_filters,
    filter_commander_candidates,
    normalize_color_identity_key,
    split_candidates_for_filter_preview,
    summarize_candidate_filters,
)
from .models import CommanderCandidate, CommanderDiscoveryScanResult
from .ui_scan_path import (
    CommanderDiscoveryUiScanResult,
    commander_discovery_output_folder,
    resolve_commander_discovery_collection_files,
    run_guarded_commander_discovery_scan,
)
from .reporting import (
    DEFAULT_COMMANDER_DISCOVERY_REPORT_NAME,
    build_commander_discovery_report,
    write_commander_discovery_report,
)

__all__ = [
    "CommanderCandidate",
    "CommanderDiscoveryScanResult",
    "summarize_candidate_filters",
    "split_candidates_for_filter_preview",
    "normalize_color_identity_key",
    "filter_commander_candidates",
    "candidate_matches_filters",
    "CommanderCandidateFilterOptions",
    "CommanderEligibilityClassification",
    "DEFAULT_COMMANDER_DISCOVERY_REPORT_NAME",
    "run_guarded_commander_discovery_scan",
    "resolve_commander_discovery_collection_files",
    "commander_discovery_output_folder",
    "CommanderDiscoveryUiScanResult",
    "build_commander_discovery_report",
    "classify_commander_eligibility",
    "discover_commander_candidates",
    "get_commander_candidate_reason",
    "get_special_commander_rule_note",
    "group_candidates_by_color_identity",
    "is_basic_legendary_creature_candidate",
    "is_commander_discovery_candidate",
    "scan_collection_for_commanders",
    "scan_collection_for_legendary_creature_candidates",
    "write_commander_discovery_report",
]

# v1.5.10 Commander Discovery service boundary exports
try:
    from .service_boundary import (
        CommanderDiscoveryRequest,
        CommanderDiscoveryService,
        CommanderDiscoveryStatus,
        service_health,
    )
except Exception:
    # Keep package import tolerant for legacy discovery paths.
    CommanderDiscoveryRequest = None
    CommanderDiscoveryService = None
    CommanderDiscoveryStatus = None
    service_health = None

