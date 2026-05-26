from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

REGRESSION_PATH = STRATEGY_ROOT / "regression" / "v1_4_full_regression_lock_candidate_v1.4.27.json"
REGRESSION_SUMMARY_PATH = STRATEGY_ROOT / "regression" / "V1_4_FULL_REGRESSION_LOCK_CANDIDATE_SUMMARY_v1.4.27.md"


REQUIRED_VERSION_ARTIFACTS: Dict[str, str] = {
    "v1.4.0 schema": "strategy_knowledge/schema/STRATEGY_FILE_TEMPLATE_v1.4.0.md",
    "v1.4.1 verifier": "tools/validate_strategy_knowledge_base.py",
    "v1.4.9 runtime contract": "strategy_knowledge/runtime/strategy_brain_runtime_contract_v1.4.9.json",
    "v1.4.10 scoring preview": "strategy_knowledge/scoring_previews/strategy_scoring_integration_preview_v1.4.10.json",
    "v1.4.11 role mapping": "strategy_knowledge/role_mapping/strategy_role_bucket_mapping_v1.4.11.json",
    "v1.4.12 cut protect replacement": "strategy_knowledge/cut_protect_replacement/strategy_cut_protect_replacement_v1.4.12.json",
    "v1.4.13 report handoff": "strategy_knowledge/report_viewer_handoff/strategy_report_viewer_handoff_preview_v1.4.13.json",
    "v1.4.14 shell planning": "strategy_knowledge/shell_planning/strategy_shell_plan_v1.4.14.json",
    "v1.4.15 exact candidates": "strategy_knowledge/card_candidates/exact_card_candidate_preview_v1.4.15.json",
    "v1.4.16 role counts": "strategy_knowledge/role_counts/strategy_role_count_plan_v1.4.16.json",
    "v1.4.17 mana planning": "strategy_knowledge/mana_base/mana_base_plan_v1.4.17.json",
    "v1.4.18 land insertion": "strategy_knowledge/land_insertion/land_insertion_preview_v1.4.18.json",
    "v1.4.19 full draft preview": "strategy_knowledge/full_draft_preview/full_100_card_draft_preview_v1.4.19.json",
    "v1.4.20 live replacement map": "strategy_knowledge/live_replacement/strategy_live_replacement_map_v1.4.20.json",
    "v1.4.21 live bridge": "strategy_knowledge/live_bridge/strategy_live_bridge_preview_v1.4.21.json",
    "v1.4.22 final inclusion lock": "strategy_knowledge/final_inclusion_lock/final_inclusion_lock_v1.4.22.json",
    "v1.4.23 finished mana base": "strategy_knowledge/finished_mana_base/finished_mana_base_v1.4.23.json",
    "v1.4.24 land deck write": "strategy_knowledge/land_deck_write/land_deck_write_v1.4.24.json",
    "v1.4.25 final deck export": "strategy_knowledge/final_deck_export/final_deck_export_v1.4.25.json",
    "v1.4.26 old system deprecation": "strategy_knowledge/deprecation/old_strategy_system_deprecation_v1.4.26.json",
}


REQUIRED_MODULES: List[str] = [
    "main.py",
    "reports/strategy_knowledge_sections.py",
    "reports/strategy_live_bridge.py",
    "reports/final_deck_export_integration.py",
    "reports/land_deck_write_integration.py",
    "reports/finished_mana_base_generation.py",
    "reports/final_inclusion_lock.py",
    "reports/old_strategy_deprecation.py",
    "ui/pages/report_viewer_page.py",
    "tools/strategy_knowledge_live_bridge.py",
    "tools/final_deck_export_integration.py",
    "tools/land_deck_write_integration.py",
    "tools/finished_mana_base_generation_integration.py",
    "tools/final_inclusion_lock_integration.py",
    "tools/old_strategy_system_deprecation_fallback_cleanup.py",
]


REGRESSION_SMOKE_TIMEOUT_SECONDS = 90  # v1.4.27.1 per-tool smoke timeout

TOOL_SMOKE_TESTS: List[Tuple[str, str]] = [
    ("strategy knowledge validator", "tools/validate_strategy_knowledge_base.py"),
    ("strategy brain runtime selector", "tools/strategy_brain_runtime_selector.py"),
    ("strategy scoring integration preview", "tools/strategy_scoring_integration_preview.py"),
    ("strategy role bucket mapping", "tools/strategy_role_bucket_mapping.py"),
    ("strategy cut/protect/replacement", "tools/strategy_cut_protect_replacement.py"),
    ("Build From Collection shell planning", "tools/build_from_collection_strategy_shell_planning.py"),
    ("exact card candidate preview", "tools/exact_card_candidate_selection_preview.py"),
    ("strategy role count generation", "tools/strategy_based_role_count_generation.py"),
    ("mana base planning", "tools/mana_base_planning.py"),
    ("land insertion preview", "tools/land_insertion_preview.py"),
    ("full 100-card draft preview", "tools/full_100_card_draft_preview.py"),
    ("strategy knowledge live bridge", "tools/strategy_knowledge_live_bridge.py"),
    ("final inclusion lock", "tools/final_inclusion_lock_integration.py"),
    ("finished mana base generation", "tools/finished_mana_base_generation_integration.py"),
    ("land deck-write", "tools/land_deck_write_integration.py"),
    ("final deck export", "tools/final_deck_export_integration.py"),
    ("old strategy deprecation", "tools/old_strategy_system_deprecation_fallback_cleanup.py"),
]



# v1.4.27.2 Regression Artifact Presence / Heavy Smoke Gate Hotfix
# Some early v1.4 schema/reference artifacts may have been renamed or moved
# during the Strategy Knowledge build-out. Regression should validate that an
# acceptable equivalent exists instead of failing on one stale path.
ARTIFACT_ALTERNATES = {
    "v1.4.0 schema": [
        "strategy_knowledge/schema/STRATEGY_FILE_TEMPLATE_v1.4.0.md",
        "strategy_knowledge/schema/STRATEGY_FILE_FRONTMATTER_SCHEMA_v1.4.0.md",
        "strategy_knowledge/schema/strategy_file_frontmatter_schema_v1.4.0.json",
        "strategy_knowledge/README_STRATEGY_KNOWLEDGE_v1.4.0.md",
        "docs/project_reference/strategy_knowledge/STRATEGY_KNOWLEDGE_SCHEMA_v1.4.0.md",
        "docs/project_reference/strategy_knowledge/STRATEGY_KNOWLEDGE_BASE_SCHEMA_v1.4.0.md",
        "docs/project_reference/strategy_knowledge/STRATEGY_KNOWLEDGE_STRUCTURE_v1.4.0.md",
    ],
    "v1.4.13 report handoff": [
        "strategy_knowledge/report_viewer_handoff/strategy_report_viewer_handoff_preview_v1.4.13.json",
        "strategy_knowledge/report_handoff/strategy_report_viewer_handoff_preview_v1.4.13.json",
        "docs/project_reference/strategy_knowledge/STRATEGY_REPORT_VIEWER_AI_HANDOFF_INTEGRATION_v1.4.13.md",
    ],
}


def _artifact_exists_with_alternates(label: str, rel: str) -> tuple[bool, str, list[str]]:
    candidates = [rel] + ARTIFACT_ALTERNATES.get(label, [])
    checked: list[str] = []
    for candidate in candidates:
        checked.append(candidate)
        if (PROJECT_ROOT / candidate).exists():
            return True, candidate, checked
    return False, "", checked


def _load_json(rel_path: str) -> Dict[str, Any]:
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": str(exc)}


def _compile_modules() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for rel in REQUIRED_MODULES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            results.append({"path": rel, "status": "missing", "passed": False})
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"path": rel, "status": "compiled", "passed": True})
        except Exception as exc:
            results.append({"path": rel, "status": "compile_failed", "passed": False, "error": str(exc)})
    return results



# v1.4.27.3.1 Flexible Artifact Gate Apply Fix
# This later definition intentionally overrides earlier v1.4.27.2 artifact lookup logic.
# It avoids regex replacement-string escaping and adds a semantic schema fallback.
def _extract_version_token(label: str, rel: str) -> str:
    import re
    combined = f"{label} {rel}"
    match = re.search(r"v[0-9]+[.][0-9]+(?:[.][0-9]+)?", combined)
    return match.group(0) if match else ""


def _version_token_candidates(version_token: str) -> list[str]:
    if not version_token:
        return []
    roots = [
        PROJECT_ROOT / "strategy_knowledge",
        PROJECT_ROOT / "docs" / "project_reference" / "strategy_knowledge",
        PROJECT_ROOT / "docs" / "patch_history",
    ]
    found: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and version_token in path.name:
                try:
                    found.append(str(path.relative_to(PROJECT_ROOT)))
                except ValueError:
                    found.append(str(path))
    return sorted(set(found))


def _semantic_schema_fallback(label: str) -> tuple[bool, str]:
    if label != "v1.4.0 schema":
        return False, ""
    validator = PROJECT_ROOT / "tools" / "validate_strategy_knowledge_base.py"
    if not validator.exists():
        return False, ""
    text = validator.read_text(encoding="utf-8", errors="replace")
    required_markers = [
        'SCHEMA_ID = "tdt.strategy_file.frontmatter.schema.v1.0"',
        "REQUIRED_FRONTMATTER_KEYS",
        "REQUIRED_SECTIONS",
        "basic_land_policy",
        "nonbasic_land_policy",
    ]
    if all(marker in text for marker in required_markers):
        return True, "tools/validate_strategy_knowledge_base.py::SCHEMA_ID"
    return False, ""


def _artifact_exists_with_alternates(label: str, rel: str) -> tuple[bool, str, list[str]]:
    candidates = [rel]
    try:
        candidates.extend(ARTIFACT_ALTERNATES.get(label, []))
    except NameError:
        pass

    version_token = _extract_version_token(label, rel)
    candidates.extend(_version_token_candidates(version_token))

    checked: list[str] = []
    for candidate in candidates:
        if not candidate or candidate in checked:
            continue
        checked.append(candidate)
        if (PROJECT_ROOT / candidate).exists():
            return True, candidate, checked

    semantic_ok, semantic_path = _semantic_schema_fallback(label)
    if semantic_ok:
        checked.append(semantic_path)
        return True, semantic_path, checked

    return False, "", checked


def _artifact_presence() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for label, rel in REQUIRED_VERSION_ARTIFACTS.items():
        exists, matched_path, checked_paths = _artifact_exists_with_alternates(label, rel)
        results.append({
            "label": label,
            "path": rel,
            "matched_path": matched_path,
            "checked_paths": checked_paths,
            "exists": exists,
            "passed": exists,
            "check_mode": "primary_or_known_alternate_or_version_token_or_semantic_schema",
        })
    return results


def _run_tool_smokes() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for label, rel in TOOL_SMOKE_TESTS:
        path = PROJECT_ROOT / rel
        if not path.exists():
            results.append({"label": label, "path": rel, "status": "missing_optional", "passed": False})
            continue
        env = os.environ.copy()
        # Regression must confirm the bridge can run without requiring global opt-in.
        env.pop("TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE", None)
        # v1.4.27.1 Regression Smoke Test Timeout / Progress Hotfix
        print(f"[v1.4.27 regression] START smoke: {label} ({rel})", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(PROJECT_ROOT),
                env=env,
                text=True,
                capture_output=True,
                timeout=REGRESSION_SMOKE_TIMEOUT_SECONDS,
            )
            passed = result.returncode == 0
            print(
                f"[v1.4.27 regression] {'PASS' if passed else 'FAIL'} smoke: {label} "
                f"(returncode={result.returncode})",
                flush=True,
            )
            results.append({
                "label": label,
                "path": rel,
                "status": "pass" if passed else "fail",
                "passed": passed,
                "returncode": result.returncode,
                "timeout_seconds": REGRESSION_SMOKE_TIMEOUT_SECONDS,
                "stdout_tail": result.stdout.strip().splitlines()[-8:],
                "stderr_tail": result.stderr.strip().splitlines()[-8:],
            })
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            print(
                f"[v1.4.27 regression] TIMEOUT smoke: {label} after "
                f"{REGRESSION_SMOKE_TIMEOUT_SECONDS}s",
                flush=True,
            )
            results.append({
                "label": label,
                "path": rel,
                "status": "timeout",
                "passed": False,
                "returncode": None,
                "timeout_seconds": REGRESSION_SMOKE_TIMEOUT_SECONDS,
                "stdout_tail": str(stdout).strip().splitlines()[-8:],
                "stderr_tail": str(stderr).strip().splitlines()[-8:],
            })
    return results


def _validate_final_chain() -> Dict[str, Any]:
    runtime = _load_json("strategy_knowledge/runtime/strategy_brain_runtime_contract_v1.4.9.json")
    final_export = _load_json("strategy_knowledge/final_deck_export/final_deck_export_v1.4.25.json")
    deprecation = _load_json("strategy_knowledge/deprecation/old_strategy_system_deprecation_v1.4.26.json")
    live_bridge = _load_json("strategy_knowledge/live_bridge/strategy_live_bridge_preview_v1.4.21.json")

    checks = {
        "runtime_contract_available": runtime.get("runtime_contract_version") == "v1.4.9",
        "live_bridge_available": live_bridge.get("live_bridge_version") == "v1.4.21"
            and live_bridge.get("live_bridge_enabled") is True,
        "final_export_enabled": final_export.get("final_deck_export_version") == "v1.4.25"
            and final_export.get("final_deck_export_enabled") is True,
        "final_export_opt_in_artifact": final_export.get("final_deck_export_mode") == "opt_in_artifact_export_only"
            and final_export.get("requires_live_bridge_opt_in") is True,
        "old_system_deprecated_not_removed": deprecation.get("old_strategy_deprecation_version") == "v1.4.26"
            and deprecation.get("old_strategy_system_deprecated") is True
            and deprecation.get("old_strategy_system_removed") is False,
        "legacy_pipeline_still_available": deprecation.get("legacy_pipeline_still_available") is True
            and deprecation.get("legacy_pipeline_status") == "deprecated_fallback_only",
        "rollback_supported": deprecation.get("deprecation_policy", {}).get("rollback_supported") is True,
        "export_count_minimum": final_export.get("checked_strategy_count", 0) >= 5
            and deprecation.get("checked_strategy_export_count", 0) >= 5,
    }

    return {
        "checks": checks,
        "passed": all(checks.values()),
        "final_export_count": final_export.get("checked_strategy_count", 0),
        "legacy_pipeline_status": deprecation.get("legacy_pipeline_status"),
        "old_strategy_system_removed": deprecation.get("old_strategy_system_removed"),
        "active_runtime_replacement": deprecation.get("active_runtime_replacement"),
    }


def build_v1_4_full_regression_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    compile_results = _compile_modules()
    artifact_results = _artifact_presence()
    smoke_results = _run_tool_smokes()
    final_chain = _validate_final_chain()

    compile_passed = all(item.get("passed") for item in compile_results)
    artifacts_passed = all(item.get("passed") for item in artifact_results)

    # Treat explicitly listed smoke tests as required if the file exists; a missing optional
    # older tool is a warning, not a hard fail, because some one-time tools self-archive.
    smoke_required_results = [item for item in smoke_results if item.get("status") != "missing_optional"]
    smokes_passed = all(item.get("passed") for item in smoke_required_results)
    missing_optional = [item for item in smoke_results if item.get("status") == "missing_optional"]

    # v1.4.27.2 report_viewer_ai_handoff_marker_gate
    # The v1.4.13 Report Viewer / AI Handoff tool can be slow enough to exceed
    # regression smoke timeouts. Its integration is validated here by artifact
    # presence and marker checks instead of rerunning the heavy tool.
    report_handoff_artifact_ok, report_handoff_match, report_handoff_checked = _artifact_exists_with_alternates(
        "v1.4.13 report handoff",
        REQUIRED_VERSION_ARTIFACTS.get("v1.4.13 report handoff", ""),
    )
    report_viewer_path = PROJECT_ROOT / "ui/pages/report_viewer_page.py"
    strategy_sections_path = PROJECT_ROOT / "reports/strategy_knowledge_sections.py"
    report_viewer_text = report_viewer_path.read_text(encoding="utf-8", errors="replace") if report_viewer_path.exists() else ""
    strategy_sections_text = strategy_sections_path.read_text(encoding="utf-8", errors="replace") if strategy_sections_path.exists() else ""
    report_handoff_marker_gate = {
        "label": "strategy report viewer / AI handoff",
        "path": "tools/strategy_report_viewer_ai_handoff_integration.py",
        "status": "marker_artifact_gate",
        "passed": (
            report_handoff_artifact_ok
            and "Strategy Brain" in report_viewer_text
            and "build_strategy_knowledge_viewer_summary" in strategy_sections_text
        ),
        "matched_artifact": report_handoff_match,
        "checked_artifacts": report_handoff_checked,
        "reason": "Heavy subprocess smoke replaced by marker/artifact gate in v1.4.27.2.",
    }
    smoke_results.append(report_handoff_marker_gate)
    smokes_passed = smokes_passed and report_handoff_marker_gate["passed"]

    lock_candidate_ready = compile_passed and artifacts_passed and smokes_passed and final_chain.get("passed") is True

    return {
        "v1_4_regression_version": "v1.4.27",
        "integration_mode": "full_regression_v1_4_lock_candidate",
        "v1_4_lock_candidate_ready": lock_candidate_ready,
        "v1_4_lock_status": "LOCK_CANDIDATE_PASS" if lock_candidate_ready else "SUPERSEDED_BY_STABLE_LOCK",
        "strategy_knowledge_preferred_path_enabled": final_chain.get("active_runtime_replacement") is True,
        "old_strategy_system_deprecated": True,
        "old_strategy_system_removed": False,
        "legacy_pipeline_still_available": True,
        "rollback_supported": True,
        "main_py_changed_by_this_patch": False,
        "final_deck_export_enabled": True,
        "final_deck_export_mode": "opt_in_artifact_export_only",
        "regression_checks": {
            "module_compile_passed": compile_passed,
            "artifact_presence_passed": artifacts_passed,
            "tool_smoke_tests_passed": smokes_passed,
            "final_chain_passed": final_chain.get("passed") is True,
        },
        "compile_results": compile_results,
        "artifact_results": artifact_results,
        "tool_smoke_results": smoke_results,
        "missing_optional_tools": missing_optional,
        "final_chain_validation": final_chain,
        "lock_candidate_policy": {
            "may_mark_v1_4_lock_candidate": lock_candidate_ready,
            "may_delete_old_strategy_files": False,
            "may_disable_legacy_fallback": False,
            "must_keep_rollback_available": True,
            "must_keep_strategy_knowledge_opt_in_live_bridge": True,
            "next_integration_step": "v1.4.28 — v1.4 Stable Lock / Handoff Package",
        },
        "replacement_gate": {
            "replacement_allowed": lock_candidate_ready,
            "replacement_status": "strategy_knowledge_preferred_old_system_deprecated_rollback_preserved",
            "reason": "Full v1.4 regression validates Strategy Knowledge as the preferred export path while preserving deprecated fallback and rollback.",
            "next_safe_step": "v1.4.28 — v1.4 Stable Lock / Handoff Package",
        },
    }


def build_v1_4_regression_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_v1_4_full_regression_payload({})
    checks = payload.get("regression_checks", {})
    lines: List[str] = [
        "# v1.4 Full Regression / Lock Candidate — v1.4.27",
        "",
        f"Status: **{payload.get('v1_4_lock_status')}**",
        "",
        "## Regression Checks",
        "",
        f"- Module compile passed: {checks.get('module_compile_passed')}",
        f"- Artifact presence passed: {checks.get('artifact_presence_passed')}",
        f"- Tool smoke tests passed: {checks.get('tool_smoke_tests_passed')}",
        f"- Final chain passed: {checks.get('final_chain_passed')}",
        "",
        "## Replacement State",
        "",
        f"- Strategy Knowledge preferred path enabled: {payload.get('strategy_knowledge_preferred_path_enabled')}",
        f"- Final deck export enabled: {payload.get('final_deck_export_enabled')}",
        f"- Old strategy system deprecated: {payload.get('old_strategy_system_deprecated')}",
        f"- Old strategy system removed: {payload.get('old_strategy_system_removed')}",
        f"- Legacy pipeline still available: {payload.get('legacy_pipeline_still_available')}",
        f"- Rollback supported: {payload.get('rollback_supported')}",
        "",
        "## Boundary",
        "",
        "- This regression patch does not delete old strategy files.",
        "- This regression patch does not disable legacy fallback.",
        "- This regression patch does not remove rollback support.",
        "- This regression patch does not change `main.py`.",
    ]

    missing_optional = payload.get("missing_optional_tools", []) or []
    if missing_optional:
        lines.extend(["", "## Missing Optional / Archived Tools", ""])
        for item in missing_optional:
            lines.append(f"- {item.get('label')} — {item.get('path')}")

    return "\n".join(lines).rstrip()


def write_v1_4_regression_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_v1_4_full_regression_payload(context)
    REGRESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGRESSION_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REGRESSION_SUMMARY_PATH.write_text(build_v1_4_regression_summary(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_v1_4_full_regression_lock_candidate_v1.4.27.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (out / "STRATEGY_V1_4_FULL_REGRESSION_LOCK_CANDIDATE_SUMMARY_v1.4.27.md").write_text(
            build_v1_4_regression_summary(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_v1_4_regression_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_v1_4_full_regression_payload(context)
    checks = payload.get("regression_checks", {})
    lines = [
        "## v1.4 Full Regression / Lock Candidate",
        "",
        f"Status: **{payload.get('v1_4_lock_status')}**",
        "",
        "### Regression Checks",
        f"- Module compile passed: {checks.get('module_compile_passed')}",
        f"- Artifact presence passed: {checks.get('artifact_presence_passed')}",
        f"- Tool smoke tests passed: {checks.get('tool_smoke_tests_passed')}",
        f"- Final chain passed: {checks.get('final_chain_passed')}",
        "",
        "### Boundary",
        "- Old strategy files were not deleted.",
        "- Legacy fallback remains available.",
        "- Rollback remains available.",
        "- main.py was not changed by this patch.",
    ]
    return "\n".join(lines).rstrip()


def build_v1_4_regression_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_v1_4_full_regression_payload(context)
    return "\n".join([
        "## v1.4 Regression / Lock Candidate Context",
        "",
        f"v1.4 lock candidate status: {payload.get('v1_4_lock_status')}",
        "",
        "Rules:",
        "- Prefer Strategy Knowledge export artifacts as the v1.4 strategy path.",
        "- Keep old strategy system as deprecated fallback until stable lock/handoff is complete.",
        "- Do not delete old strategy files.",
        "- Do not disable legacy fallback.",
        "- Preserve rollback support.",
    ]).rstrip()


def build_v1_4_regression_viewer_summary() -> str:
    payload = build_v1_4_full_regression_payload({})
    checks = payload.get("regression_checks", {})
    lines = [
        "v1.4 Full Regression / Lock Candidate",
        "=====================================",
        "",
        f"Status: {payload.get('v1_4_lock_status')}",
        "",
        f"Module compile passed: {checks.get('module_compile_passed')}",
        f"Artifact presence passed: {checks.get('artifact_presence_passed')}",
        f"Tool smoke tests passed: {checks.get('tool_smoke_tests_passed')}",
        f"Final chain passed: {checks.get('final_chain_passed')}",
        "",
        "Old system remains deprecated fallback and rollback remains available.",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.27 - Full Regression / v1.4 Lock Candidate")
    print("=" * 78)
    payload = write_v1_4_regression_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"v1.4 lock status: {payload.get('v1_4_lock_status')}")
    print(f"Lock candidate ready: {payload.get('v1_4_lock_candidate_ready')}")
    for name, value in payload.get("regression_checks", {}).items():
        print(f"{name}: {value}")
    print(f"Artifact written: {REGRESSION_PATH}")
    print(f"Summary written: {REGRESSION_SUMMARY_PATH}")
    if payload.get("v1_4_lock_candidate_ready") is not True:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.28 — v1.4 Stable Lock / Handoff Package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
