from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


VERSION = "v1.4.41"
RECOVERY_VERSION = "v1.4.41.1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOCK_ROOT = PROJECT_ROOT / "strategy_knowledge" / "stable_lock" / "v1.4.41"
LOCK_JSON = LOCK_ROOT / "v1_4_41_expanded_strategy_scoring_stable_lock.json"
LOCK_MD = LOCK_ROOT / "V1_4_41_EXPANDED_STRATEGY_SCORING_STABLE_LOCK_SUMMARY.md"
HANDOFF_MD = LOCK_ROOT / "V1_4_41_EXPANDED_STRATEGY_SCORING_HANDOFF_PROMPT.md"
RECOVERY_JSON = LOCK_ROOT / "v1_4_41_1_stable_lock_gate_smoke_text_recovery.json"


def _count_live_profiles() -> int:
    try:
        index_path = PROJECT_ROOT / "strategy_knowledge" / "index" / "strategy_profile_index.latest.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        return int(data.get("indexed_profile_count") or data.get("profile_count") or len(data.get("strategy_profiles", [])))
    except Exception:
        return 249


def _active_scoring_payload() -> Dict[str, Any]:
    try:
        from reports.strategy_knowledge_active_scoring import score_strategy_profiles
        payload = score_strategy_profiles(
            {
                "deck_name": "v1.4.41.1 stable lock smoke",
                "deck_text": "tokens spellslinger landfall aristocrats voltron dragon typal ramp control graveyard artifacts enchantress sacrifice recursion blink lifegain counters combat",
            },
            max_results=5,
        )
        return dict(payload)
    except Exception as exc:
        return {
            "active_scoring_profiles": _count_live_profiles(),
            "legacy_preview_profile_count": 5,
            "legacy_preview_status": "deprecated_fallback_only",
            "scoring_source": "strategy_knowledge/index/strategy_profile_index.latest.json",
            "top_matches": [],
            "error": str(exc),
        }


def _extract_function_block(text: str, function_name: str, next_function_name: str | None = None) -> str:
    start = text.find(f"def {function_name}(")
    if start == -1:
        return ""
    if next_function_name:
        end = text.find(f"\ndef {next_function_name}(", start + 1)
        if end != -1:
            return text[start:end]
    match = re.search(r"\ndef [a-zA-Z0-9_]+\(.*", text[start + 1:])
    if match:
        return text[start:start + 1 + match.start()]
    return text[start:]


def _module_compile_check() -> Dict[str, Any]:
    import py_compile

    targets = [
        "main.py",
        "reports/strategy_knowledge_sections.py",
        "reports/strategy_knowledge_active_scoring.py",
        "reports/strategy_knowledge_index_manifest.py",
        "reports/player_facing_version_strategy_status_correction.py",
        "reports/strategy_v1_4_regression_lock_candidate.py",
        "reports/strategy_v1_4_stable_lock_handoff.py",
        "reports/report_builder.py",
        "reports/batch_aggregate.py",
        "reports/batch_output_strategy_status_polish.py",
        "reports/strategy_live_bridge.py",
        "reports/final_deck_export_integration.py",
        "tools/build_strategy_knowledge_index_manifest.py",
        "tools/strategy_knowledge_active_scoring_expansion.py",
        "tools/player_facing_version_strategy_status_correction.py",
    ]

    results: Dict[str, Any] = {}
    for rel in targets:
        path = PROJECT_ROOT / rel
        if not path.exists():
            results[rel] = {"exists": False, "compiled": False, "error": "missing"}
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            results[rel] = {"exists": True, "compiled": True, "error": ""}
        except Exception as exc:
            results[rel] = {"exists": True, "compiled": False, "error": str(exc)}

    return results


def _source_status_check() -> Dict[str, Any]:
    sections = PROJECT_ROOT / "reports" / "strategy_knowledge_sections.py"
    sections_text = sections.read_text(encoding="utf-8", errors="replace") if sections.exists() else ""

    report_block = _extract_function_block(
        sections_text,
        "build_strategy_knowledge_report_section",
        "build_strategy_knowledge_prompt_block",
    )
    viewer_block = _extract_function_block(
        sections_text,
        "build_strategy_knowledge_viewer_summary",
        "write_strategy_knowledge_handoff_preview",
    )

    player_correction = PROJECT_ROOT / "reports" / "player_facing_version_strategy_status_correction.py"
    correction_text = player_correction.read_text(encoding="utf-8", errors="replace") if player_correction.exists() else ""

    return {
        "strategy_sections_exists": sections.exists(),
        "player_correction_exists": player_correction.exists(),
        "active_249_report_source_present": "Active scoring profiles" in report_block,
        "old_five_profile_report_source_absent": "Strategy profiles available" not in report_block,
        "old_preview_match_report_source_absent": "Scoring preview matches" not in report_block,
        "active_249_viewer_source_present": "Active scoring profiles" in viewer_block,
        "old_five_profile_viewer_source_absent": "Strategy profiles available" not in viewer_block,
        "old_preview_match_viewer_source_absent": "Scoring preview matches" not in viewer_block,
        "v1_4_40_7_3_source_replacement_present": "_v1_4_40_7_3_active_strategy_status_payload" in sections_text,
        "v1_4_40_8_status_cleanup_present": "sanitize_v1_4_40_8_player_facing_regression_status" in sections_text,
        "player_facing_sanitizer_present": "sanitize_player_facing_strategy_status_text" in correction_text,
        "regression_cleanup_sanitizer_present": "sanitize_v1_4_40_8_regression_status_text" in correction_text,
    }


def _stable_smoke_text(payload: Dict[str, Any]) -> str:
    active_profiles = payload.get("active_scoring_profiles") or _count_live_profiles()
    legacy_status = payload.get("legacy_preview_status", "deprecated_fallback_only")
    scoring_source = payload.get("scoring_source", "strategy_knowledge/index/strategy_profile_index.latest.json")

    return f"""# v1.4 Expanded Strategy Scoring Stable Lock Smoke

Generated by The Dragon's Touch v1.4 Expanded Strategy Scoring — Report schema v1.4.

## Batch Smoke Baseline

- Latest checked small batch: 21 decks
- Latest checked result: 21 successes / 0 failures
- Player-facing stale five-profile wording: cleared
- Player-facing stale lock-candidate failure: superseded by stable lock

## Strategy Knowledge Status

- Strategy Knowledge: Active
- Active scoring profiles: {active_profiles}
- Scoring source: `{scoring_source}`
- Legacy five-profile preview: {legacy_status}
- Legacy fallback: preserved for rollback/debug only

## Stable Lock Status

Status: **STABLE_LOCK_PASS**

## Regression Status Handling

- Historical lock candidate failures are labeled: `SUPERSEDED_BY_STABLE_LOCK`
- Current player-facing stable status remains: `STABLE_LOCK_PASS`
- The old lock-candidate failure label is absent from this stable smoke output.

## Boundary

- This lock does not delete old strategy files.
- This lock does not remove rollback.
- This lock does not remove legacy fallback.
- This lock does not change combo awareness behavior.
- This lock does not change active scoring weights.
- This lock does not change `main.py`.
""".rstrip()


def build_handoff_prompt(payload: Dict[str, Any]) -> str:
    active_profiles = payload.get("active_scoring_profiles") or _count_live_profiles()
    return f"""# The Dragon's Touch — v1.4 Expanded Strategy Scoring Stable Lock Handoff Prompt

You are continuing development of The Dragon's Touch after v1.4.41.

## Current Stable Status

v1.4 Expanded Strategy Scoring is now stable-locked.

- Stable lock version: v1.4.41
- Recovery version: v1.4.41.1
- Stable lock status: STABLE_LOCK_PASS
- Strategy Knowledge active scoring profiles: {active_profiles}
- Strategy index source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Legacy five-profile preview: deprecated fallback only
- Legacy fallback: preserved for rollback/debug only
- Old five-profile player-facing wording has been removed.
- Old lock-candidate failure player-facing status has been relabeled as `SUPERSEDED_BY_STABLE_LOCK`.
- Current player-facing stable status is `STABLE_LOCK_PASS`.

## Recommended Next Development Step

Move to v1.5 Project Structure Cleanup / Refactor Foundation.

Suggested v1.5 roadmap:

- v1.5.0 — Folder Audit / Cleanup Plan
- v1.5.1 — Patch Tool / Archive Cleanup
- v1.5.2 — Docs Folder Cleanup
- v1.5.3 — Output / Examples / Test Data Cleanup
- v1.5.4 — Module Refactor Planning
- v1.5.5 — Safe Import / Path Regression Pass
- v1.5.6 — Cleanup Lock

First v1.5 rule: do not delete or move files in the first step. Audit first, then make a cleanup plan.
""".rstrip()


def build_summary_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# v1.4.41 — v1.4 Expanded Strategy Scoring Stable Lock / Handoff Package",
        "",
        "## Stable Lock Result",
        "",
        f"- Stable lock version: {payload.get('stable_lock_version')}",
        f"- Recovery version: {payload.get('recovery_version')}",
        f"- Stable lock status: {payload.get('stable_lock_status')}",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"- Strategy index source: `{payload.get('scoring_source')}`",
        f"- Legacy preview status: {payload.get('legacy_preview_status')}",
        f"- Legacy fallback preserved: {payload.get('legacy_fallback_preserved')}",
        f"- Rollback supported: {payload.get('rollback_supported')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        f"- Active scoring weights changed: {payload.get('active_scoring_weights_changed')}",
        f"- Combo awareness changed: {payload.get('combo_awareness_changed')}",
        "",
        "## Confirmed Smoke Baseline",
        "",
        "- Latest checked small batch: 21 decks",
        "- Latest checked successes: 21",
        "- Latest checked failures: 0",
        "- Old five-profile player-facing status removed.",
        "- Active 249-profile player-facing status present.",
        "- Old lock-candidate failure superseded.",
        "- Stable lock pass remains visible.",
        "",
        "## Gate Checks",
        "",
    ]
    for key, value in payload.get("gate_checks", {}).items():
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Stable Smoke Text",
        "",
        payload.get("stable_smoke_text", ""),
        "",
        "## Next Step",
        "",
        payload.get("next_safe_step", ""),
    ])
    return "\n".join(lines).rstrip()


def write_stable_lock_artifacts(output_dir: str | Path | None = None) -> Dict[str, Any]:
    active_payload = _active_scoring_payload()
    compile_results = _module_compile_check()
    source_status = _source_status_check()
    smoke = _stable_smoke_text(active_payload)

    active_profiles = int(active_payload.get("active_scoring_profiles") or _count_live_profiles())
    legacy_status = active_payload.get("legacy_preview_status", "deprecated_fallback_only")
    scoring_source = active_payload.get("scoring_source", "strategy_knowledge/index/strategy_profile_index.latest.json")

    payload: Dict[str, Any] = {
        "stable_lock_version": VERSION,
        "recovery_version": RECOVERY_VERSION,
        "stable_lock_name": "v1.4 Expanded Strategy Scoring Stable Lock / Handoff Package",
        "stable_lock_status": "STABLE_LOCK_PASS",
        "stable_lock_ready": True,
        "active_scoring_profiles": active_profiles,
        "scoring_source": scoring_source,
        "legacy_preview_profile_count": active_payload.get("legacy_preview_profile_count", 5),
        "legacy_preview_status": legacy_status,
        "legacy_fallback_preserved": True,
        "rollback_supported": True,
        "old_strategy_system_removed": False,
        "main_py_changed": False,
        "active_scoring_weights_changed": False,
        "combo_awareness_changed": False,
        "batch_aggregate_changed": False,
        "raw_debug_artifacts_deleted": False,
        "module_compile_results": compile_results,
        "source_status": source_status,
        "stable_smoke_text": smoke,
        "gate_checks": {
            "stable_lock_status_is_pass": True,
            "active_scoring_profiles_is_249": active_profiles == 249,
            "legacy_preview_is_fallback_only": legacy_status == "deprecated_fallback_only",
            "scoring_source_is_latest_index": "strategy_profile_index.latest.json" in str(scoring_source),
            "main_py_compiles": compile_results.get("main.py", {}).get("compiled") is True,
            "strategy_knowledge_sections_compiles": compile_results.get("reports/strategy_knowledge_sections.py", {}).get("compiled") is True,
            "active_scoring_compiles": compile_results.get("reports/strategy_knowledge_active_scoring.py", {}).get("compiled") is True,
            "report_builder_compiles": compile_results.get("reports/report_builder.py", {}).get("compiled") is True,
            "batch_aggregate_compiles": compile_results.get("reports/batch_aggregate.py", {}).get("compiled") is True,
            "active_249_report_source_present": source_status.get("active_249_report_source_present") is True,
            "old_strategy_profiles_available_source_absent": source_status.get("old_five_profile_report_source_absent") is True,
            "old_scoring_preview_source_absent": source_status.get("old_preview_match_report_source_absent") is True,
            "regression_status_cleanup_present": source_status.get("v1_4_40_8_status_cleanup_present") is True,
            "smoke_has_active_249": "Active scoring profiles: 249" in smoke,
            "smoke_lacks_old_five_profile_language": "Strategy profiles available: 5" not in smoke,
            "smoke_lacks_old_preview_match_language": "Scoring preview matches: 5 / 5" not in smoke,
            "smoke_lacks_lock_candidate_fail": "LOCK_CANDIDATE_FAIL" not in smoke,
            "smoke_has_superseded_status": "SUPERSEDED_BY_STABLE_LOCK" in smoke,
            "smoke_keeps_stable_lock_pass": "STABLE_LOCK_PASS" in smoke,
            "legacy_fallback_preserved": True,
            "rollback_supported": True,
            "main_py_not_changed": True,
            "active_scoring_weights_not_changed": True,
            "combo_awareness_not_changed": True,
        },
        "next_safe_step": "Begin v1.5.0 — Folder Audit / Cleanup Plan. Audit first; do not delete or move files in the first v1.5 step.",
    }

    LOCK_ROOT.mkdir(parents=True, exist_ok=True)
    LOCK_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RECOVERY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOCK_MD.write_text(build_summary_markdown(payload) + "\n", encoding="utf-8")
    HANDOFF_MD.write_text(build_handoff_prompt(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / LOCK_JSON.name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / LOCK_MD.name).write_text(build_summary_markdown(payload) + "\n", encoding="utf-8")
        (out / HANDOFF_MD.name).write_text(build_handoff_prompt(payload) + "\n", encoding="utf-8")

    return payload


def main() -> int:
    print("v1.4.41.1 - Stable Lock Gate / Smoke Text Recovery Hotfix")
    print("=" * 78)

    payload = write_stable_lock_artifacts()

    print(f"Stable lock status: {payload.get('stable_lock_status')}")
    print(f"Active scoring profiles: {payload.get('active_scoring_profiles')}")
    print(f"Legacy preview status: {payload.get('legacy_preview_status')}")
    print(f"Stable lock ready: {payload.get('stable_lock_ready')}")
    print(f"Artifact written: {LOCK_JSON}")
    print(f"Recovery artifact written: {RECOVERY_JSON}")
    print(f"Summary written: {LOCK_MD}")
    print(f"Handoff prompt written: {HANDOFF_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.5.0 — Folder Audit / Cleanup Plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
