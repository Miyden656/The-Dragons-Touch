"""Report section boundary package.

This package is the v1.5.7 compatibility boundary for report section wiring.
It intentionally wraps the existing report modules instead of moving or
rewriting them in this patch.
"""

from .section_contract import ReportSectionSpec, ResolvedReportSection
from .registry import (
    get_report_section_specs,
    get_report_section_registry,
    get_report_section_spec,
    resolve_report_section_callable,
    registry_health,
)

__all__ = [
    "ReportSectionSpec",
    "ResolvedReportSection",
    "get_report_section_specs",
    "get_report_section_registry",
    "get_report_section_spec",
    "resolve_report_section_callable",
    "registry_health",
]
