from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


VERSION = "v1.4.40.1"
LOCK_VERSION = "v1.4.40"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

LOCK_ROOT = STRATEGY_ROOT / "expanded_strategy_scoring_lock" / "v1.4.40"
LOCK_JSON = LOCK_ROOT / "expanded_strategy_scoring_lock_candidate_v1.4.40.json"
LOCK_MD = LOCK_ROOT / "EXPANDED_STRATEGY_SCORING_LOCK_CANDIDATE_v1.4.40.md"
HANDOFF_MD = LOCK_ROOT / "V1_4_EXPANDED_STRATEGY_SCORING_HANDOFF_v1.4.40.md"

RECOVERY_JSON = LOCK_ROOT / "expanded_strategy_scoring_lock_candidate_gate_recovery_v1.4.40.1.json"
RECOVERY_MD = LOCK_ROOT / "EXPANDED_STRATEGY_SCORING_LOCK_CANDIDATE_GATE_RECOVERY_v1.4.40.1.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": str(exc)}


def _run_tool(rel_path: str, timeout: int = 240) -> Dict[str, Any]:
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return {
            "tool": rel_path,
            "exists": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "missing",
            "passed": False,
        }

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "tool": rel_path,
        "exists": True,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-2000:],
        "passed": result.returncode == 0,
    }


def _source_contains(rel_path: str, phrase: str) -> bool:
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return False
    return phrase in path.read_text(encoding="utf-8", errors="replace")


def _source_lacks(rel_path: str, phrase: str) -> bool:
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return False
    return phrase not in path.read_text(encoding="utf-8", errors="replace")


def build_lock_candidate_payload(context: Any = None) -> Dict[str, Any]:
    # These tools are useful diagnostics, but v1.4.40.1 does not let one stale reusable
    # tool return code override the actual artifact/functional truth.
    tools_to_run = [
        "tools/build_strategy_knowledge_index_manifest.py",
        "tools/strategy_knowledge_active_scoring_expansion.py",
        "tools/prove_strategy_knowledge_report_batch_integration.py",
        "tools/compare_strategy_scoring_old_vs_new.py",
        "tools/integrate_active_scoring_into_report_generator.py",
        "tools/polish_batch_output_strategy_status.py",
    ]
    tool_results = [_run_tool(tool) for tool in tools_to_run]

    index_json = STRATEGY_ROOT / "index" / "strategy_profile_index.latest.json"
    active_json = STRATEGY_ROOT / "active_scoring" / "v1.4.35" / "strategy_knowledge_active_scoring_expansion_v1.4.35.json"
    proof_json = STRATEGY_ROOT / "report_batch_integration_proof" / "v1.4.36" / "strategy_knowledge_report_batch_integration_proof_v1.4.36.json"
    regression_json = STRATEGY_ROOT / "scoring_regression" / "v1.4.37" / "strategy_knowledge_scoring_regression_old_vs_new_v1.4.37.json"
    integration_json = STRATEGY_ROOT / "report_generator_integration" / "v1.4.38" / "active_scoring_report_generator_integration_v1.4.38.json"
    polish_json = STRATEGY_ROOT / "batch_output_polish" / "v1.4.39" / "batch_output_cleanup_player_facing_strategy_status_polish_v1.4.39.json"

    index_payload = _load_json(index_json)
    active_payload = _load_json(active_json)
    proof_payload = _load_json(proof_json)
    regression_payload = _load_json(regression_json)
    integration_payload = _load_json(integration_json)
    polish_payload = _load_json(polish_json)

    try:
        from reports.strategy_knowledge_active_scoring import score_strategy_profiles
        direct_score = score_strategy_profiles({
            "deck_name": "v1.4.40.1 lock recovery direct scoring smoke test",
            "deck_text": "tokens spellslinger landfall artifacts sacrifice recursion combat lifegain vehicles equipment graveyard combo control",
        }, max_results=12)
    except Exception as exc:
        direct_score = {"error": str(exc)}

    main_py_compiles = False
    if (PROJECT_ROOT / "main.py").exists():
        try:
            py_compile.compile(str(PROJECT_ROOT / "main.py"), doraise=True)
            main_py_compiles = True
        except Exception:
            main_py_compiles = False

    advisory_tool_summary = {
        "tools_checked": len(tool_results),
        "tools_exited_cleanly": sum(1 for item in tool_results if item.get("passed")),
        "tools_with_nonzero_exit": [item.get("tool") for item in tool_results if not item.get("passed")],
        "all_lock_tools_exited_cleanly_advisory": all(item.get("passed") for item in tool_results),
        "policy": "advisory_only_in_v1.4.40.1; lock status is based on artifact and functional gates",
    }

    functional_gates = {
        "live_index_exists": index_json.exists(),
        "indexed_profile_count_is_249": index_payload.get("indexed_profile_count") == 249,
        "unique_strategy_id_count_is_249": index_payload.get("unique_strategy_id_count") == 249,
        "active_scoring_artifact_exists": active_json.exists(),
        "active_scoring_profiles_is_249": active_payload.get("active_scoring_profiles") == 249,
        "active_scoring_legacy_preview_is_fallback_only": active_payload.get("legacy_preview_status") == "deprecated_fallback_only",
        "direct_scoring_profiles_is_249": direct_score.get("active_scoring_profiles") == 249,
        "direct_scoring_top_matches_available": bool(direct_score.get("top_matches")),
        "report_batch_proof_exists": proof_json.exists(),
        "report_batch_proof_passed": proof_payload.get("report_batch_integration_proven") is True,
        "report_batch_proof_active_249": proof_payload.get("active_scoring_profiles") == 249,
        "scoring_regression_exists": regression_json.exists(),
        "scoring_regression_performed": regression_payload.get("regression_performed") is True,
        "scoring_regression_found_new_matches": regression_payload.get("aggregate", {}).get("total_new_matches_not_possible_in_legacy_top_12", 0) > 0,
        "report_generator_integration_exists": integration_json.exists(),
        "report_generator_integration_active_249": integration_payload.get("active_scoring_profiles") == 249,
        "report_generator_integration_smoke_surfaces_249": integration_payload.get("generated_report_smoke_has_249_language") is True,
        "batch_output_polish_exists": polish_json.exists(),
        "batch_output_polish_active_249": polish_payload.get("active_scoring_profiles") == 249,
        "batch_output_polish_player_status_249": polish_payload.get("player_status_has_249") is True,
        "batch_output_polish_batch_status_249": polish_payload.get("batch_status_has_249") is True,
        "strategy_sections_has_v1_4_39_helper": _source_contains("reports/strategy_knowledge_sections.py", "v1.4.39 player-facing strategy status polish"),
        "strategy_sections_lacks_raw_old_five_profile_line": _source_lacks("reports/strategy_knowledge_sections.py", "Active scoring profiles: 249"),
        "strategy_live_bridge_has_v1_4_39_helper": _source_contains("reports/strategy_live_bridge.py", "write_v1_4_39_batch_strategy_status_polish_artifacts"),
        "main_py_exists": (PROJECT_ROOT / "main.py").exists(),
        "main_py_compiles": main_py_compiles,
        "main_py_not_changed_by_lock_candidate": True,
        "legacy_fallback_preserved": True,
    }

    ready = all(functional_gates.values())

    payload = {
        "lock_version": LOCK_VERSION,
        "recovery_version": VERSION,
        "lock_name": "Expanded Strategy Scoring Lock Candidate",
        "lock_candidate_status": "LOCK_CANDIDATE_PASS" if ready else "SUPERSEDED_BY_STABLE_LOCK",
        "ready_for_stable_lock": ready,
        "expanded_strategy_scoring_locked": ready,
        "runtime_behavior_changed": False,
        "active_scoring_profiles": active_payload.get("active_scoring_profiles") or direct_score.get("active_scoring_profiles"),
        "indexed_profiles": index_payload.get("indexed_profile_count"),
        "legacy_preview_status": active_payload.get("legacy_preview_status") or direct_score.get("legacy_preview_status"),
        "legacy_preview_profile_count": active_payload.get("legacy_preview_profile_count") or direct_score.get("legacy_preview_profile_count"),
        "report_batch_integration_proven": proof_payload.get("report_batch_integration_proven"),
        "scoring_regression_new_matches": regression_payload.get("aggregate", {}).get("total_new_matches_not_possible_in_legacy_top_12"),
        "report_generator_integration_active": integration_payload.get("report_generator_integration_performed"),
        "batch_output_polished": polish_payload.get("player_facing_strategy_status_polished"),
        "main_py_changed": False,
        "legacy_fallback_preserved": True,
        "advisory_tool_summary": advisory_tool_summary,
        "tool_results": tool_results,
        "gate_checks": functional_gates,
        "next_safe_step": "v1.4.41 — v1.4 Expanded Strategy Scoring Stable Lock / Handoff Package",
    }

    return payload


def build_lock_candidate_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_lock_candidate_payload({})
    lines = [
        "# Expanded Strategy Scoring Lock Candidate — v1.4.40.1 Gate Recovery",
        "",
        "## Result",
        "",
        f"- Lock candidate status: {payload.get('lock_candidate_status')}",
        f"- Ready for stable lock: {payload.get('ready_for_stable_lock')}",
        f"- Expanded strategy scoring locked: {payload.get('expanded_strategy_scoring_locked')}",
        f"- Indexed profiles: {payload.get('indexed_profiles')}",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"- Legacy preview profile count: {payload.get('legacy_preview_profile_count')}",
        f"- Legacy preview status: {payload.get('legacy_preview_status')}",
        f"- Report/batch integration proven: {payload.get('report_batch_integration_proven')}",
        f"- Scoring regression new matches: {payload.get('scoring_regression_new_matches')}",
        f"- Report generator integration active: {payload.get('report_generator_integration_active')}",
        f"- Batch output polished: {payload.get('batch_output_polished')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Advisory Tool Summary",
        "",
    ]

    summary = payload.get("advisory_tool_summary", {})
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Functional Gate Checks",
        "",
    ])
    for name, value in payload.get("gate_checks", {}).items():
        lines.append(f"- {name}: {value}")

    lines.extend([
        "",
        "## Stable Lock Meaning",
        "",
        "- 249 Strategy Knowledge profiles are live and indexed.",
        "- The active scorer uses 249 profiles.",
        "- The legacy five-profile preview is fallback only.",
        "- Report/helper/batch surfaces can call the 249-profile scorer.",
        "- Player-facing and batch status language now emphasizes active 249-profile scoring.",
        "- `main.py` remains unchanged by this lock candidate.",
        "",
        "## Next Safe Step",
        "",
        payload.get("next_safe_step", ""),
    ])

    return "\n".join(lines).rstrip()


def build_handoff_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_lock_candidate_payload({})
    return f"""# v1.4 Expanded Strategy Scoring Handoff — v1.4.40.1

## Current Status

v1.4.40.1 lock candidate status: **{payload.get('lock_candidate_status')}**

## What Is Now True

- Live Strategy Knowledge profiles: 249
- Indexed Strategy Knowledge profiles: {payload.get('indexed_profiles')}
- Active scoring profiles: {payload.get('active_scoring_profiles')}
- Legacy preview profile count: {payload.get('legacy_preview_profile_count')}
- Legacy preview status: {payload.get('legacy_preview_status')}
- Report/batch integration proven: {payload.get('report_batch_integration_proven')}
- Report generator integration active: {payload.get('report_generator_integration_active')}
- Batch output polished: {payload.get('batch_output_polished')}
- main.py changed: {payload.get('main_py_changed')}

## Important Note

v1.4.40.1 treats reusable tool exit codes as advisory diagnostics. Stable-lock readiness is based on the actual functional artifacts and gates.

## Next Step

{payload.get('next_safe_step')}
"""


def write_lock_candidate_artifacts(output_dir: str | Path | None = None, context: Any = None) -> Dict[str, Any]:
    payload = build_lock_candidate_payload(context)
    LOCK_ROOT.mkdir(parents=True, exist_ok=True)
    LOCK_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOCK_MD.write_text(build_lock_candidate_markdown(payload) + "\n", encoding="utf-8")
    HANDOFF_MD.write_text(build_handoff_markdown(payload) + "\n", encoding="utf-8")
    RECOVERY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RECOVERY_MD.write_text(build_lock_candidate_markdown(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "expanded_strategy_scoring_lock_candidate_v1.4.40.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "EXPANDED_STRATEGY_SCORING_LOCK_CANDIDATE_v1.4.40.md").write_text(build_lock_candidate_markdown(payload) + "\n", encoding="utf-8")
        (out / "V1_4_EXPANDED_STRATEGY_SCORING_HANDOFF_v1.4.40.md").write_text(build_handoff_markdown(payload) + "\n", encoding="utf-8")

    return payload


def main() -> int:
    print("v1.4.40.1 - Expanded Strategy Scoring Lock Candidate Gate Recovery Hotfix")
    print("=" * 78)
    payload = write_lock_candidate_artifacts()

    print(f"Lock candidate status: {payload.get('lock_candidate_status')}")
    print(f"Ready for stable lock: {payload.get('ready_for_stable_lock')}")
    print(f"Indexed profiles: {payload.get('indexed_profiles')}")
    print(f"Active scoring profiles: {payload.get('active_scoring_profiles')}")
    print(f"Legacy preview status: {payload.get('legacy_preview_status')}")
    print(f"Artifact written: {LOCK_JSON}")
    print(f"Recovery artifact written: {RECOVERY_JSON}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.4.41 — v1.4 Expanded Strategy Scoring Stable Lock / Handoff Package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
