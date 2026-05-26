"""Canonical report section registry for the v1.5 cleanup/refactor line.

This is a compatibility registry: existing report modules stay in place, while
new code can discover them through a single backend-owned boundary.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Iterable

from .section_contract import ReportSectionSpec, ResolvedReportSection, resolve_callable


_SECTION_SPECS: tuple[ReportSectionSpec, ...] = (
    ReportSectionSpec(
        section_id="strategy_knowledge_status",
        category="strategy",
        module_name="reports.strategy_knowledge_sections",
        report_function="build_strategy_knowledge_report_section",
        prompt_function="build_strategy_knowledge_prompt_block",
        viewer_function="build_strategy_knowledge_viewer_summary",
        payload_function="build_strategy_knowledge_payload",
        notes="Primary Strategy Knowledge report section boundary.",
    ),
    ReportSectionSpec(
        section_id="strategy_live_bridge",
        category="strategy",
        module_name="reports.strategy_bridge.strategy_live_bridge",
        payload_function="build_strategy_live_bridge_payload",
        notes="Strategy live bridge diagnostics/status boundary.",
    ),
    ReportSectionSpec(
        section_id="active_scoring",
        category="strategy",
        module_name="reports.strategy_bridge.strategy_knowledge_active_scoring",
        report_function="build_active_scoring_report_section",
        payload_function="score_strategy_profiles",
        notes="249-profile active scoring report/scoring boundary.",
    ),
    ReportSectionSpec(
        section_id="strategy_shell",
        category="commander_building",
        module_name="reports.strategy_bridge.strategy_shell_planning",
        report_function="build_strategy_shell_report_section",
        prompt_function="build_strategy_shell_prompt_block",
        viewer_function="build_strategy_shell_viewer_summary",
        payload_function="build_strategy_shell_plan_payload",
        notes="Strategy shell planning output boundary.",
    ),
    ReportSectionSpec(
        section_id="exact_card_candidates",
        category="commander_building",
        module_name="reports.strategy_bridge.exact_card_candidate_preview",
        report_function="build_exact_card_candidate_report_section",
        prompt_function="build_exact_card_candidate_prompt_block",
        viewer_function="build_exact_card_candidate_viewer_summary",
        payload_function="build_exact_card_candidate_payload",
        notes="Exact card candidate preview boundary.",
    ),
    ReportSectionSpec(
        section_id="role_count",
        category="commander_building",
        module_name="reports.strategy_bridge.strategy_role_count_generation",
        report_function="build_strategy_role_count_report_section",
        prompt_function="build_strategy_role_count_prompt_block",
        viewer_function="build_strategy_role_count_viewer_summary",
        payload_function="build_strategy_role_count_payload",
        notes="Role count generation boundary.",
    ),
    ReportSectionSpec(
        section_id="mana_base",
        category="mana_base",
        module_name="reports.strategy_bridge.mana_base_planning",
        report_function="build_mana_base_report_section",
        prompt_function="build_mana_base_prompt_block",
        viewer_function="build_mana_base_viewer_summary",
        payload_function="build_mana_base_planning_payload",
        notes="Mana base planning boundary.",
    ),
    ReportSectionSpec(
        section_id="land_insertion",
        category="mana_base",
        module_name="reports.strategy_bridge.land_insertion_preview",
        report_function="build_land_insertion_report_section",
        prompt_function="build_land_insertion_prompt_block",
        viewer_function="build_land_insertion_viewer_summary",
        payload_function="build_land_insertion_preview_payload",
        notes="Land insertion preview boundary.",
    ),
    ReportSectionSpec(
        section_id="full_100_card_draft",
        category="commander_building",
        module_name="reports.strategy_bridge.full_100_card_draft_preview",
        report_function="build_full_100_card_draft_report_section",
        prompt_function="build_full_100_card_draft_prompt_block",
        viewer_function="build_full_100_card_draft_viewer_summary",
        payload_function="build_full_100_card_draft_preview_payload",
        notes="Full 100-card draft preview boundary.",
    ),
    ReportSectionSpec(
        section_id="final_inclusion_lock",
        category="commander_building",
        module_name="reports.strategy_bridge.final_inclusion_lock",
        report_function="build_final_inclusion_lock_report_section",
        prompt_function="build_final_inclusion_lock_prompt_block",
        viewer_function="build_final_inclusion_lock_viewer_summary",
        payload_function="build_final_inclusion_lock_payload",
        notes="Final inclusion lock boundary.",
    ),
    ReportSectionSpec(
        section_id="finished_mana_base",
        category="mana_base",
        module_name="reports.strategy_bridge.finished_mana_base_generation",
        report_function="build_finished_mana_base_report_section",
        prompt_function="build_finished_mana_base_prompt_block",
        viewer_function="build_finished_mana_base_viewer_summary",
        payload_function="build_finished_mana_base_payload",
        notes="Finished mana base generation boundary.",
    ),
    ReportSectionSpec(
        section_id="land_deck_write",
        category="mana_base",
        module_name="reports.strategy_bridge.land_deck_write_integration",
        report_function="build_land_deck_write_report_section",
        prompt_function="build_land_deck_write_prompt_block",
        viewer_function="build_land_deck_write_viewer_summary",
        payload_function="build_land_deck_write_payload",
        notes="Land deck-write integration boundary.",
    ),
    ReportSectionSpec(
        section_id="final_deck_export",
        category="commander_building",
        module_name="reports.strategy_bridge.final_deck_export_integration",
        report_function="build_final_deck_export_report_section",
        prompt_function="build_final_deck_export_prompt_block",
        viewer_function="build_final_deck_export_viewer_summary",
        payload_function="build_final_deck_export_payload",
        notes="Final deck export integration boundary.",
    ),
    ReportSectionSpec(
        section_id="old_strategy_deprecation",
        category="debug_legacy",
        module_name="reports.strategy_bridge.old_strategy_deprecation",
        report_function="build_old_strategy_deprecation_report_section",
        prompt_function="build_old_strategy_deprecation_prompt_block",
        viewer_function="build_old_strategy_deprecation_viewer_summary",
        payload_function="build_old_strategy_deprecation_payload",
        notes="Deprecated five-profile strategy fallback status boundary.",
    ),
    ReportSectionSpec(
        section_id="v1_4_stable_lock",
        category="debug_lock",
        module_name="reports.strategy_bridge.strategy_v1_4_stable_lock_handoff",
        report_function="build_v1_4_stable_lock_report_section",
        prompt_function="build_v1_4_stable_lock_prompt_block",
        viewer_function="build_v1_4_stable_lock_viewer_summary",
        payload_function="build_v1_4_stable_lock_payload",
        notes="v1.4 stable lock handoff boundary.",
    ),
)


def get_report_section_specs() -> tuple[ReportSectionSpec, ...]:
    """Return all known report section specs."""

    return _SECTION_SPECS


def get_report_section_registry() -> "OrderedDict[str, ReportSectionSpec]":
    """Return an ordered mapping of section_id to section spec."""

    return OrderedDict((spec.section_id, spec) for spec in _SECTION_SPECS)


def get_report_section_spec(section_id: str) -> ReportSectionSpec:
    """Return one section spec by id."""

    registry = get_report_section_registry()
    try:
        return registry[section_id]
    except KeyError as exc:
        known = ", ".join(registry)
        raise KeyError(f"Unknown report section {section_id!r}. Known: {known}") from exc


def iter_specs(category: str | None = None) -> Iterable[ReportSectionSpec]:
    """Iterate specs, optionally filtered by category."""

    for spec in _SECTION_SPECS:
        if category is None or spec.category == category:
            yield spec


def resolve_report_section_callable(section_id: str, role: str = "report") -> ResolvedReportSection:
    """Resolve a callable for one report section by section_id and role."""

    return resolve_callable(get_report_section_spec(section_id), role=role)


def registry_health() -> dict[str, object]:
    """Return non-invasive registry health details.

    This checks callable availability but does not execute section callables.
    """

    sections: list[dict[str, object]] = []
    failures: list[str] = []

    for spec in _SECTION_SPECS:
        function_status: dict[str, str] = {}
        for role in ("report", "prompt", "viewer", "payload"):
            if role not in spec.available_functions():
                continue
            try:
                resolve_callable(spec, role=role)
                function_status[role] = "ok"
            except Exception as exc:  # pragma: no cover - diagnostic path
                function_status[role] = f"error: {exc}"
                failures.append(f"{spec.section_id}:{role}:{exc}")

        sections.append(
            {
                "section_id": spec.section_id,
                "category": spec.category,
                "module_name": spec.module_name,
                "status": spec.status,
                "functions": function_status,
            }
        )

    return {
        "section_count": len(_SECTION_SPECS),
        "sections": sections,
        "failure_count": len(failures),
        "failures": failures,
    }
