"""Small report-section contract types for The Dragon's Touch.

The goal is to make report sections discoverable and testable without forcing
the old report modules to move all at once.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable


@dataclass(frozen=True)
class ReportSectionSpec:
    """Metadata for one report section or report-adjacent section family."""

    section_id: str
    category: str
    module_name: str
    report_function: str | None = None
    prompt_function: str | None = None
    viewer_function: str | None = None
    payload_function: str | None = None
    status: str = "legacy_adapter"
    notes: str = ""

    def available_functions(self) -> dict[str, str]:
        functions: dict[str, str] = {}
        for role, name in (
            ("report", self.report_function),
            ("prompt", self.prompt_function),
            ("viewer", self.viewer_function),
            ("payload", self.payload_function),
        ):
            if name:
                functions[role] = name
        return functions


@dataclass(frozen=True)
class ResolvedReportSection:
    """A resolved callable from a ReportSectionSpec."""

    spec: ReportSectionSpec
    role: str
    callable_name: str
    callable_obj: Callable[..., Any]


def resolve_callable(spec: ReportSectionSpec, role: str = "report") -> ResolvedReportSection:
    """Resolve one callable from a section spec.

    This imports lazily to avoid loading every report module during startup.
    """

    function_name = spec.available_functions().get(role)
    if not function_name:
        raise KeyError(f"Section {spec.section_id!r} has no callable for role {role!r}")

    module = import_module(spec.module_name)
    callable_obj = getattr(module, function_name)
    if not callable(callable_obj):
        raise TypeError(f"{spec.module_name}.{function_name} is not callable")

    return ResolvedReportSection(
        spec=spec,
        role=role,
        callable_name=function_name,
        callable_obj=callable_obj,
    )
