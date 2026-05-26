"""Legacy report-section adapter helpers.

These helpers intentionally do not change report output. They provide a single
place for future patches to call existing report section functions while the old
modules are gradually split into cleaner packages.
"""
from __future__ import annotations

from typing import Any

from .registry import resolve_report_section_callable


def call_report_section(section_id: str, *args: Any, role: str = "report", **kwargs: Any) -> Any:
    """Resolve and call an existing legacy report-section function."""

    resolved = resolve_report_section_callable(section_id, role=role)
    return resolved.callable_obj(*args, **kwargs)
