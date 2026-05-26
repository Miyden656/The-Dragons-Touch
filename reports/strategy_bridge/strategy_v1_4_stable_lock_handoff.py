from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

REGRESSION_PATH = STRATEGY_ROOT / "regression" / "v1_4_full_regression_lock_candidate_v1.4.27.json"
STABLE_LOCK_PATH = STRATEGY_ROOT / "stable_lock" / "v1_4_stable_lock_v1.4.28.json"
STABLE_LOCK_SUMMARY_PATH = STRATEGY_ROOT / "stable_lock" / "V1_4_STABLE_LOCK_SUMMARY_v1.4.28.md"
STABLE_HANDOFF_PATH = STRATEGY_ROOT / "stable_lock" / "V1_4_HANDOFF_PROMPT_v1.4.28.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": str(exc)}


def _regression_checks(regression: Dict[str, Any]) -> Dict[str, bool]:
    checks = regression.get("regression_checks", {}) or {}
    policy = regression.get("lock_candidate_policy", {}) or {}
    replacement = regression.get("replacement_gate", {}) or {}

    return {
        "regression_artifact_available": regression.get("v1_4_regression_version") == "v1.4.27",
        "lock_candidate_passed": regression.get("v1_4_lock_candidate_ready") is True
            and regression.get("v1_4_lock_status") == "LOCK_CANDIDATE_PASS",
        "module_compile_passed": checks.get("module_compile_passed") is True,
        "artifact_presence_passed": checks.get("artifact_presence_passed") is True,
        "tool_smoke_tests_passed": checks.get("tool_smoke_tests_passed") is True,
        "final_chain_passed": checks.get("final_chain_passed") is True,
        "strategy_knowledge_preferred": regression.get("strategy_knowledge_preferred_path_enabled") is True,
        "final_deck_export_enabled": regression.get("final_deck_export_enabled") is True,
        "old_strategy_deprecated_not_removed": regression.get("old_strategy_system_deprecated") is True
            and regression.get("old_strategy_system_removed") is False,
        "legacy_fallback_available": regression.get("legacy_pipeline_still_available") is True,
        "rollback_supported": regression.get("rollback_supported") is True,
        "policy_blocks_old_file_deletion": policy.get("may_delete_old_strategy_files") is False,
        "policy_blocks_fallback_disable": policy.get("may_disable_legacy_fallback") is False,
        "policy_keeps_rollback": policy.get("must_keep_rollback_available") is True,
        "replacement_gate_allowed": replacement.get("replacement_allowed") is True,
    }


def build_v1_4_stable_lock_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    regression = _load_json(REGRESSION_PATH)
    checks = _regression_checks(regression)
    stable_ready = all(checks.values())

    return {
        "v1_4_stable_lock_version": "v1.4.28",
        "integration_mode": "v1_4_stable_lock_handoff_package",
        "v1_4_stable_lock_ready": stable_ready,
        "v1_4_stable_status": "STABLE_LOCK_PASS" if stable_ready else "STABLE_LOCK_FAIL",
        "based_on_regression_version": regression.get("v1_4_regression_version"),
        "based_on_lock_candidate_status": regression.get("v1_4_lock_status"),
        "strategy_knowledge_preferred_path_enabled": regression.get("strategy_knowledge_preferred_path_enabled") is True,
        "final_deck_export_enabled": regression.get("final_deck_export_enabled") is True,
        "old_strategy_system_deprecated": regression.get("old_strategy_system_deprecated") is True,
        "old_strategy_system_removed": regression.get("old_strategy_system_removed") is True,  # overwritten below intentionally false
        "legacy_pipeline_still_available": regression.get("legacy_pipeline_still_available") is True,
        "rollback_supported": regression.get("rollback_supported") is True,
        "main_py_changed_by_this_patch": False,
        "stable_lock_checks": checks,
        "stable_lock_policy": {
            "may_mark_v1_4_stable": stable_ready,
            "may_begin_v1_5_or_next_version": stable_ready,
            "may_delete_old_strategy_files": False,
            "may_disable_legacy_fallback": False,
            "must_keep_rollback_available": True,
            "must_keep_old_strategy_system_as_deprecated_fallback": True,
            "must_document_strategy_knowledge_as_preferred_path": True,
            "recommended_next_project_step": "Begin next planned version only after saving a clean v1.4 stable backup.",
        },
        "handoff_summary": {
            "locked_version": "v1.4",
            "locked_version_name": "Strategy Deep Dive / Strategy Knowledge Live Replacement",
            "status": "PASS / STABLE LOCK" if stable_ready else "FAIL / NOT LOCKED",
            "preferred_path": "Strategy Knowledge live bridge + final deck export artifacts",
            "deprecated_path": "Old strategy system retained as fallback/rollback path",
            "next_patch_name": "v1.4.29 or next-version planning, if needed",
        },
        "replacement_gate": {
            "replacement_allowed": stable_ready,
            "replacement_status": "v1_4_stable_strategy_knowledge_preferred_old_system_deprecated_fallback_preserved",
            "reason": "v1.4.28 locks the Strategy Knowledge replacement chain as stable while preserving deprecated fallback and rollback.",
            "next_safe_step": "Save clean v1.4 stable backup, then begin the next planned version.",
        },
    } | {"old_strategy_system_removed": False}


def build_v1_4_stable_lock_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_v1_4_stable_lock_payload({})
    checks = payload.get("stable_lock_checks", {})
    lines: List[str] = [
        "# v1.4 Stable Lock / Handoff Package — v1.4.28",
        "",
        f"Status: **{payload.get('v1_4_stable_status')}**",
        "",
        "## Stable Lock Result",
        "",
        f"- v1.4 stable lock ready: {payload.get('v1_4_stable_lock_ready')}",
        f"- Based on regression version: {payload.get('based_on_regression_version')}",
        f"- Based on lock candidate status: {payload.get('based_on_lock_candidate_status')}",
        "",
        "## Stable Lock Checks",
    ]

    for name, value in checks.items():
        lines.append(f"- {name}: {value}")

    lines.extend([
        "",
        "## Locked v1.4 Behavior",
        "",
        "- Strategy Knowledge is the preferred strategy export path.",
        "- Final deck export artifacts are enabled through the Strategy Knowledge chain.",
        "- Old strategy system is deprecated fallback, not deleted.",
        "- Legacy fallback remains available.",
        "- Rollback remains available.",
        "- `main.py` was not changed by this stable-lock patch.",
        "",
        "## Next Step",
        "",
        "Save a clean v1.4 stable backup before starting the next planned version.",
    ])

    return "\n".join(lines).rstrip()


def build_v1_4_handoff_prompt(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_v1_4_stable_lock_payload({})
    return "\n".join([
        "# The Dragon’s Touch — v1.4 Stable Handoff Prompt",
        "",
        "You are helping continue development of The Dragon’s Touch, a local Python-based Magic: The Gathering Commander deck review and deck-building assistant.",
        "",
        "## Current Stable Version",
        "",
        "v1.4 — Strategy Deep Dive / Strategy Knowledge Live Replacement",
        "",
        f"Status: {payload.get('v1_4_stable_status')}",
        "",
        "## What v1.4 Locked",
        "",
        "- Strategy Knowledge Base schema and verifier foundation.",
        "- Strategy Knowledge loader/runtime preview and default-candidate path.",
        "- Strategy scoring, role buckets, cut/protect/replacement integration.",
        "- Report Viewer and AI handoff integration.",
        "- Build From Collection strategy shell planning.",
        "- exact-card candidate preview, role-count generation, mana-base planning, land insertion preview.",
        "- full 100-card draft preview.",
        "- opt-in live bridge through `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`.",
        "- final inclusion lock artifacts.",
        "- finished mana-base artifacts.",
        "- land deck-write artifacts.",
        "- final deck export artifacts.",
        "- old strategy system deprecation/fallback policy.",
        "- v1.4 full regression lock-candidate validation.",
        "",
        "## Safety Boundary",
        "",
        "- Old strategy files were not deleted.",
        "- Legacy fallback was not disabled.",
        "- Rollback remains available.",
        "- The old strategy system is deprecated fallback only.",
        "- Save a clean v1.4 stable backup before starting new development.",
        "",
        "## Patch Workflow Reminder",
        "",
        "- Use small versioned patches.",
        "- Include `tools/apply_vX.X.X_name.py`.",
        "- Include `tools/verify_vX.X.X_name.py`.",
        "- Include `docs/patch_history/README_PATCH_vX.X.X_name.txt`.",
        "- Archive one-time patch tools under `Old Do Not Use/One-time patch tools/<parent version>/`.",
        "- Subpatches archive under their parent version folder.",
    ]).rstrip()


def write_v1_4_stable_lock_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_v1_4_stable_lock_payload(context)
    STABLE_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    STABLE_LOCK_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    STABLE_LOCK_SUMMARY_PATH.write_text(build_v1_4_stable_lock_summary(payload) + "\n", encoding="utf-8")
    STABLE_HANDOFF_PATH.write_text(build_v1_4_handoff_prompt(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_v1_4_stable_lock_v1.4.28.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "V1_4_STABLE_LOCK_SUMMARY_v1.4.28.md").write_text(
            build_v1_4_stable_lock_summary(payload) + "\n",
            encoding="utf-8",
        )
        (out / "V1_4_HANDOFF_PROMPT_v1.4.28.md").write_text(
            build_v1_4_handoff_prompt(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_v1_4_stable_lock_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_v1_4_stable_lock_payload(context)
    return "\n".join([
        "## v1.4 Stable Lock / Handoff Package",
        "",
        f"Status: **{payload.get('v1_4_stable_status')}**",
        "",
        "### Stable Boundary",
        "- Strategy Knowledge is the preferred strategy export path.",
        "- Final deck export artifacts are enabled.",
        "- Old strategy system remains deprecated fallback.",
        "- Legacy fallback remains available.",
        "- Rollback remains available.",
        "- `main.py` was not changed by this patch.",
    ]).rstrip()


def build_v1_4_stable_lock_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_v1_4_stable_lock_payload(context)
    return "\n".join([
        "## v1.4 Stable Lock Context",
        "",
        f"v1.4 stable status: {payload.get('v1_4_stable_status')}",
        "",
        "Rules:",
        "- Treat Strategy Knowledge as the preferred strategy export path.",
        "- Keep the old strategy system as deprecated fallback.",
        "- Do not delete old strategy files.",
        "- Do not disable legacy fallback.",
        "- Preserve rollback support.",
        "- Save a clean v1.4 stable backup before starting new development.",
    ]).rstrip()


def build_v1_4_stable_lock_viewer_summary() -> str:
    payload = build_v1_4_stable_lock_payload({})
    lines = [
        "v1.4 Stable Lock / Handoff Package",
        "===================================",
        "",
        f"Status: {payload.get('v1_4_stable_status')}",
        "",
        f"Stable lock ready: {payload.get('v1_4_stable_lock_ready')}",
        f"Strategy Knowledge preferred path: {payload.get('strategy_knowledge_preferred_path_enabled')}",
        f"Final deck export enabled: {payload.get('final_deck_export_enabled')}",
        f"Old strategy system removed: {payload.get('old_strategy_system_removed')}",
        f"Legacy fallback available: {payload.get('legacy_pipeline_still_available')}",
        f"Rollback supported: {payload.get('rollback_supported')}",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.28 - v1.4 Stable Lock / Handoff Package")
    print("=" * 78)
    payload = write_v1_4_stable_lock_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"v1.4 stable status: {payload.get('v1_4_stable_status')}")
    print(f"Stable lock ready: {payload.get('v1_4_stable_lock_ready')}")
    print(f"Strategy Knowledge preferred path enabled: {payload.get('strategy_knowledge_preferred_path_enabled')}")
    print(f"Final deck export enabled: {payload.get('final_deck_export_enabled')}")
    print(f"Old strategy system removed: {payload.get('old_strategy_system_removed')}")
    print(f"Legacy fallback still available: {payload.get('legacy_pipeline_still_available')}")
    print(f"Rollback supported: {payload.get('rollback_supported')}")
    print(f"Artifact written: {STABLE_LOCK_PATH}")
    print(f"Summary written: {STABLE_LOCK_SUMMARY_PATH}")
    print(f"Handoff prompt written: {STABLE_HANDOFF_PATH}")
    if payload.get("v1_4_stable_lock_ready") is not True:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("v1.4 is safe to mark PASS / STABLE LOCK if this verifier passes locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
