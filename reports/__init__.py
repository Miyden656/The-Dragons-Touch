"""Report and prompt builders for the modular MTG Deck Helper cleanup."""

# v1.5.7 report section registry exports
from reports.sections import (
    ReportSectionSpec,
    get_report_section_specs,
    get_report_section_registry,
    registry_health,
)

__all__ = [
    "ReportSectionSpec",
    "get_report_section_specs",
    "get_report_section_registry",
    "registry_health",
]
