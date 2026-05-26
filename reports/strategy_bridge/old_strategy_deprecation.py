from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

FINAL_EXPORT_PATH = STRATEGY_ROOT / "final_deck_export" / "final_deck_export_v1.4.25.json"
LIVE_BRIDGE_PATH = STRATEGY_ROOT / "live_bridge" / "strategy_live_bridge_preview_v1.4.21.json"

DEPRECATION_PATH = STRATEGY_ROOT / "deprecation" / "old_strategy_system_deprecation_v1.4.26.json"
DEPRECATION_SUMMARY_PATH = STRATEGY_ROOT / "deprecation" / "OLD_STRATEGY_SYSTEM_DEPRECATION_SUMMARY_v1.4.26.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_old_strategy_deprecation_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    final_export = _load_json(FINAL_EXPORT_PATH)
    live_bridge = _load_json(LIVE_BRIDGE_PATH)

    gate_checks = {
        "final_deck_export_available": final_export.get("final_deck_export_version") == "v1.4.25"
            and final_export.get("final_deck_export_enabled") is True,
        "final_export_kept_legacy_available": final_export.get("legacy_pipeline_still_available") is True,
        "live_bridge_available": live_bridge.get("live_bridge_version") == "v1.4.21"
            and live_bridge.get("live_bridge_enabled") is True,
        "legacy_not_removed_before_this_patch": final_export.get("old_strategy_system_removed") is False,
    }

    export_count = len(final_export.get("final_deck_exports", []) or [])

    return {
        "old_strategy_deprecation_version": "v1.4.26",
        "integration_mode": "old_strategy_system_deprecation_fallback_cleanup",
        "strategy_knowledge_preferred_path_enabled": True,
        "old_strategy_system_deprecated": True,
        "old_strategy_system_removed": False,
        "legacy_pipeline_still_available": True,
        "legacy_pipeline_status": "deprecated_fallback_only",
        "fallback_cleanup_mode": "preserve_rollback_do_not_delete",
        "runtime_behavior_changed": True,
        "main_py_changed": False,
        "requires_live_bridge_opt_in": True,
        "opt_in_env_var": "TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE",
        "active_runtime_replacement": True,
        "final_deck_export_enabled": True,
        "final_deck_export_mode": "opt_in_artifact_export_only",
        "checked_strategy_export_count": export_count,
        "gate_checks": gate_checks,
        "deprecation_policy": {
            "preferred_strategy_path": "Strategy Knowledge live bridge + final deck export artifacts",
            "old_strategy_path_status": "deprecated fallback",
            "delete_old_strategy_files": False,
            "disable_legacy_fallback": False,
            "rollback_supported": True,
            "reason": "v1.4.26 makes Strategy Knowledge the preferred path but keeps the old system available for safe rollback until the v1.4 lock candidate passes regression.",
        },
        "fallback_rules": [
            "Use Strategy Knowledge export artifacts when the live bridge is explicitly enabled.",
            "Keep the old strategy system available as fallback until v1.4 lock/regression passes.",
            "Do not delete old strategy files in this patch.",
            "Do not remove legacy fallback in this patch.",
            "Do not alter main.py in this patch.",
        ],
        "integration_contract": {
            "may_mark_old_strategy_system_deprecated": True,
            "may_prefer_strategy_knowledge_export_path": True,
            "may_remove_old_strategy_system": False,
            "may_delete_legacy_strategy_files": False,
            "may_disable_legacy_fallback": False,
            "must_keep_rollback_available": True,
            "must_require_explicit_opt_in_for_strategy_knowledge_live_bridge": True,
            "next_integration_step": "v1.4.27 — Full Regression / v1.4 Lock Candidate",
        },
        "replacement_gate": {
            "replacement_allowed": True,
            "replacement_status": "strategy_knowledge_preferred_old_system_deprecated_but_not_deleted",
            "reason": "Strategy Knowledge is now the preferred opt-in export path. The old strategy system remains as deprecated fallback until full regression confirms safe lock.",
            "next_safe_step": "v1.4.27 — Full Regression / v1.4 Lock Candidate",
        },
    }


def build_old_strategy_deprecation_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_old_strategy_deprecation_payload({})
    lines: List[str] = [
        "# Old Strategy System Deprecation / Fallback Cleanup — v1.4.26",
        "",
        "Strategy Knowledge is now the preferred strategy export path.",
        "",
        "## Boundary",
        "",
        "- Strategy Knowledge preferred path: enabled.",
        "- Old strategy system: deprecated fallback.",
        "- Old strategy system deletion: disabled.",
        "- Legacy fallback removal: disabled.",
        "- Rollback support: preserved.",
        "- main.py changed in this patch: no.",
        "",
        "## Policy",
        "",
        f"- Preferred path: {payload.get('deprecation_policy', {}).get('preferred_strategy_path')}",
        f"- Old path status: {payload.get('legacy_pipeline_status')}",
        f"- Checked strategy export count: {payload.get('checked_strategy_export_count')}",
        "",
        "## Fallback Rules",
    ]
    for rule in payload.get("fallback_rules", []):
        lines.append(f"- {rule}")
    return "\n".join(lines).rstrip()


def write_old_strategy_deprecation_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_old_strategy_deprecation_payload(context)
    DEPRECATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEPRECATION_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    DEPRECATION_SUMMARY_PATH.write_text(build_old_strategy_deprecation_summary(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_old_system_deprecation_v1.4.26.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_OLD_SYSTEM_DEPRECATION_SUMMARY_v1.4.26.md").write_text(
            build_old_strategy_deprecation_summary(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_old_strategy_deprecation_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_old_strategy_deprecation_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines = [
        "## Old Strategy System Deprecation / Fallback Cleanup",
        "",
        "Strategy Knowledge is now the preferred strategy export path.",
        "",
        "### Boundary",
        "- Old strategy system is deprecated, not deleted.",
        "- Legacy fallback remains available.",
        "- Rollback remains available.",
        "- Strategy Knowledge live bridge still requires explicit opt-in.",
        "",
        "### Deprecation Summary",
        f"- Strategy Knowledge preferred path enabled: {payload.get('strategy_knowledge_preferred_path_enabled')}",
        f"- Old strategy system deprecated: {payload.get('old_strategy_system_deprecated')}",
        f"- Old strategy system removed: {payload.get('old_strategy_system_removed')}",
        f"- Legacy pipeline status: {payload.get('legacy_pipeline_status')}",
    ]
    return "\n".join(lines).rstrip()


def build_old_strategy_deprecation_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_old_strategy_deprecation_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Old Strategy System Deprecation Context",
        "",
        "Strategy Knowledge is now the preferred strategy export path.",
        "",
        "Rules:",
        "- Prefer Strategy Knowledge live bridge artifacts when explicitly enabled.",
        "- Treat the old strategy system as deprecated fallback.",
        "- Do not delete old strategy files in this stage.",
        "- Do not disable rollback in this stage.",
        "- Keep legacy fallback available until full regression passes.",
    ]).rstrip()


def build_old_strategy_deprecation_viewer_summary() -> str:
    payload = build_old_strategy_deprecation_payload({})
    lines = [
        "Old Strategy System Deprecation",
        "===============================",
        "",
        "Strategy Knowledge is now the preferred strategy export path.",
        "",
        f"Old strategy system deprecated: {payload.get('old_strategy_system_deprecated')}",
        f"Old strategy system removed: {payload.get('old_strategy_system_removed')}",
        f"Legacy pipeline status: {payload.get('legacy_pipeline_status')}",
        "Rollback support: preserved",
        "",
        "This is deprecation/fallback cleanup, not file deletion.",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.26 - Old Strategy System Deprecation / Fallback Cleanup")
    print("=" * 78)
    payload = write_old_strategy_deprecation_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Strategy Knowledge preferred path enabled: {payload.get('strategy_knowledge_preferred_path_enabled')}")
    print(f"Old strategy system deprecated: {payload.get('old_strategy_system_deprecated')}")
    print(f"Old strategy system removed: {payload.get('old_strategy_system_removed')}")
    print(f"Legacy pipeline status: {payload.get('legacy_pipeline_status')}")
    print(f"Artifact written: {DEPRECATION_PATH}")
    print(f"Summary written: {DEPRECATION_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_export_count", 0) < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.27 — Full Regression / v1.4 Lock Candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
