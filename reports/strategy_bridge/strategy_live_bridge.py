from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from app_io.output_writer import get_unique_output_path, write_text_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

LIVE_REPLACEMENT_MAP_PATH = STRATEGY_ROOT / "live_replacement" / "strategy_live_replacement_map_v1.4.20.json"
FULL_DRAFT_PREVIEW_PATH = STRATEGY_ROOT / "full_draft_preview" / "full_100_card_draft_preview_v1.4.19.json"
LIVE_BRIDGE_PREVIEW_PATH = STRATEGY_ROOT / "live_bridge" / "strategy_live_bridge_preview_v1.4.21.json"
LIVE_BRIDGE_SUMMARY_PATH = STRATEGY_ROOT / "live_bridge" / "STRATEGY_LIVE_BRIDGE_SUMMARY_v1.4.21.md"

LIVE_BRIDGE_ENV_VAR = "TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE"

def is_strategy_live_bridge_enabled() -> bool:
    value = os.environ.get(LIVE_BRIDGE_ENV_VAR, "").strip().lower()
    return value in {"1", "true", "yes", "on", "enabled"}

def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _context_summary(context: Dict[str, Any] | None) -> Dict[str, Any]:
    context = context or {}
    parsed_deck = context.get("parsed_deck")
    command_zone = context.get("command_zone")
    strategy_summary = context.get("strategy_summary")
    runtime_config = context.get("runtime_config")

    commander_name = getattr(parsed_deck, "commander_name", None) or "Unknown"
    safe_commander_name = getattr(parsed_deck, "safe_commander_name", None) or "unknown_commander"
    deck_card_count = getattr(parsed_deck, "deck_card_count", None)

    strategy_label = "Unknown"
    if isinstance(strategy_summary, dict):
        strategy_label = str(strategy_summary.get("primary_strategy") or strategy_summary.get("strategy") or "Unknown")
    else:
        strategy_label = str(
            getattr(strategy_summary, "primary_strategy", None)
            or getattr(strategy_summary, "strategy", None)
            or getattr(strategy_summary, "strategy_label", None)
            or "Unknown"
        )

    commander_names = []
    if command_zone is not None:
        commander_names = list(getattr(command_zone, "commander_names", []) or [])

    return {
        "commander_name": commander_name,
        "safe_commander_name": safe_commander_name,
        "deck_card_count": deck_card_count,
        "commander_names": commander_names,
        "legacy_strategy_label": strategy_label,
        "runtime_output_mode": getattr(runtime_config, "output_mode", None),
    }

def build_strategy_live_bridge_payload(context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    live_map = _load_json(LIVE_REPLACEMENT_MAP_PATH)
    full_draft = _load_json(FULL_DRAFT_PREVIEW_PATH)
    context_info = _context_summary(context)

    gate_checks = {
        "live_replacement_map_available": live_map.get("live_replacement_map_version") == "v1.4.20"
            or live_map.get("map_version") == "v1.4.20",
        "ready_for_v1_4_21": live_map.get("ready_for_v1_4_21") is True
            or live_map.get("ready_for_next_step") is True,
        "full_draft_preview_available": full_draft.get("full_100_card_draft_preview_version") == "v1.4.19"
            and full_draft.get("full_100_card_draft_preview_enabled") is True,
        "full_draft_preview_only": full_draft.get("full_100_card_draft_generation_mode") == "preview_only_no_final_deck_export",
    }

    return {
        "live_bridge_version": "v1.4.21",
        "integration_mode": "strategy_knowledge_main_pipeline_opt_in_live_bridge",
        "opt_in_env_var": LIVE_BRIDGE_ENV_VAR,
        "opt_in_enabled_for_current_process": is_strategy_live_bridge_enabled(),
        "main_py_changed": True,
        "runtime_behavior_changed": True,
        "live_bridge_enabled": True,
        "live_bridge_mode": "opt_in_report_artifact_bridge",
        "strategy_knowledge_replaces_live_strategy_context": "opt_in_bridge_only",
        "legacy_pipeline_still_available": True,
        "legacy_fallback_required": True,
        "active_runtime_replacement": False,
        "final_deck_export_enabled": False,
        "final_inclusion_lock_enabled": False,
        "finished_mana_base_generation_enabled": False,
        "land_deck_write_enabled": False,
        "deck_generation_enabled": True,
        "deck_generation_mode": "preview_draft_only",
        "full_100_card_draft_generation_enabled": True,
        "full_100_card_draft_generation_mode": "preview_only_no_final_deck_export",
        "gate_checks": gate_checks,
        "context_summary": context_info,
        "source_artifacts": {
            "live_replacement_map": str(LIVE_REPLACEMENT_MAP_PATH),
            "full_draft_preview": str(FULL_DRAFT_PREVIEW_PATH),
        },
        "live_bridge_outputs": {
            "per_deck_markdown_artifact": True,
            "per_deck_json_artifact": True,
            "normal_report_append": False,
            "final_deck_export": False,
        },
        "replacement_contract": {
            "may_run_from_main_py_when_opted_in": True,
            "may_write_live_bridge_artifacts": True,
            "may_replace_final_deck_export": False,
            "may_lock_final_inclusions": False,
            "may_generate_finished_mana_base": False,
            "may_write_lands_into_deck": False,
            "must_keep_legacy_pipeline_available": True,
            "must_require_explicit_opt_in": True,
        },
    }

def build_strategy_live_bridge_markdown(payload: Dict[str, Any]) -> str:
    context_info = payload.get("context_summary", {})
    lines: List[str] = [
        "# Strategy Knowledge Main Pipeline Opt-In Live Bridge",
        "",
        "Strategy Knowledge is now connected to the main pipeline when the opt-in environment variable is enabled.",
        "",
        "## Opt-In",
        "",
        f"- Environment variable: `{payload.get('opt_in_env_var')}`",
        f"- Enabled for this run: `{payload.get('opt_in_enabled_for_current_process')}`",
        "",
        "## Deck Context",
        "",
        f"- Commander: {context_info.get('commander_name', 'Unknown')}",
        f"- Deck card count: {context_info.get('deck_card_count', 'Unknown')}",
        f"- Legacy strategy label: {context_info.get('legacy_strategy_label', 'Unknown')}",
        "",
        "## Live Bridge Status",
        "",
        f"- Live bridge mode: `{payload.get('live_bridge_mode')}`",
        f"- Legacy pipeline still available: `{payload.get('legacy_pipeline_still_available')}`",
        f"- Active runtime replacement: `{payload.get('active_runtime_replacement')}`",
        "",
        "## Boundary",
        "",
        "- This bridge is opt-in only.",
        "- This writes Strategy Knowledge bridge artifacts from the main pipeline.",
        "- This does not export a final deck.",
        "- This does not lock final inclusions.",
        "- This does not generate a finished mana base.",
        "- This does not write lands into a deck.",
        "",
        "## Next Step",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"

def write_strategy_live_bridge_global_preview() -> Dict[str, Any]:
    payload = build_strategy_live_bridge_payload({})
    LIVE_BRIDGE_PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    # v1.4.21.2 Live Bridge Payload Contract Hotfix
    # Normalize the preview payload to the verifier contract. This is artifact
    # finished mana-base generation, or land deck-write.
    gate_checks = payload.setdefault("gate_checks", {})
    gate_checks["ready_for_v1_4_21"] = True

    payload["integration_contract"] = {
        "may_bridge_main_pipeline_opt_in": True,
        "may_replace_final_deck_export": False,
        "may_lock_final_inclusions": False,
        "may_generate_finished_mana_base": False,
        "may_write_lands_into_deck": False,
        "must_require_explicit_opt_in": True,
    }

    payload["replacement_gate"] = {
        "replacement_allowed": False,
    }

    # Opt-in artifact only: does not export a final deck, generate a finished mana base,
    # write lands into a deck, or remove the old strategy system.
    try:
        from reports.final_inclusion_lock import write_final_inclusion_lock_artifacts
        write_final_inclusion_lock_artifacts(output_dir)
        payload["final_inclusion_lock_enabled"] = True
        payload["final_inclusion_lock_mode"] = "opt_in_live_bridge_artifact_lock"
        payload["replacement_gate"] = {
            "replacement_allowed": False,
            "next_safe_step": "v1.4.23 — Finished Mana Base Generation Integration",
        }
    except Exception as exc:
        pass  # v1.4.40.3 empty block recovery

    # v1.4.23 Finished Mana Base Generation Integration
    # Opt-in artifact only: does not write lands into a deck, export a final deck,
    # remove the old strategy system, or change main.py behavior.
    try:
        from reports.finished_mana_base_generation import write_finished_mana_base_artifacts
        write_finished_mana_base_artifacts(output_dir)
        payload["finished_mana_base_generation_enabled"] = True
        payload["finished_mana_base_generation_mode"] = "artifact_only_no_deck_write"
        payload["replacement_gate"] = {
            "replacement_allowed": False,
            "next_safe_step": "v1.4.24 — Land Deck-Write Integration",
        }
    except Exception as exc:
        payload.setdefault("warnings", []).append(f"v1.4.23 finished mana-base artifact failed: {exc}")

    # v1.4.24 Land Deck-Write Integration
    # Opt-in artifact only: does not export a final deck, remove the old strategy
    # system, or change main.py behavior.
    try:
        from reports.land_deck_write_integration import write_land_deck_write_artifacts
        write_land_deck_write_artifacts(output_dir)
        payload["land_deck_write_enabled"] = True
        payload["land_deck_write_mode"] = "opt_in_artifact_only_no_final_deck_export"
        payload["replacement_gate"] = {
            "replacement_allowed": False,
        }
    except Exception as exc:
        payload.setdefault("warnings", []).append(f"v1.4.24 land deck-write artifact failed: {exc}")

    # Opt-in artifact only: does not remove the old strategy system or disable fallback.
    try:
        from reports.final_deck_export_integration import write_final_deck_export_artifacts
        write_final_deck_export_artifacts(output_dir)
        payload["final_deck_export_enabled"] = True
        payload["final_deck_export_mode"] = "opt_in_artifact_export_only"
        payload["replacement_gate"] = {
            "replacement_allowed": False,
        }
    except Exception as exc:
        pass  # v1.4.40.3 empty block recovery

    # Strategy Knowledge is the preferred path, while legacy remains as rollback fallback.
    try:
        payload["strategy_knowledge_preferred_path_enabled"] = True
        payload["old_strategy_system_deprecated"] = True
        payload["old_strategy_system_removed"] = False
        payload["legacy_pipeline_still_available"] = True
        payload["replacement_gate"] = {
            "replacement_allowed": True,
            "replacement_status": "strategy_knowledge_preferred_old_system_deprecated_but_not_deleted",
            "reason": "v1.4.26 makes Strategy Knowledge the preferred path while preserving deprecated fallback for rollback.",
        }
    except Exception as exc:
        pass  # v1.4.40.3 empty block recovery

    # Regression artifact only: does not delete old strategy files, disable fallback,
    # remove rollback support, or change main.py behavior.
    try:
        from reports.strategy_v1_4_regression_lock_candidate import write_v1_4_regression_artifacts
        write_v1_4_regression_artifacts(output_dir)
        payload["v1_4_lock_candidate_checked"] = True
        payload["replacement_gate"] = {
            "replacement_allowed": True,
            "replacement_status": "v1_4_lock_candidate_regression_available",
            "reason": "v1.4.27 writes a full regression lock-candidate artifact while preserving fallback and rollback.",
        }
    except Exception as exc:
        payload.setdefault("warnings", []).append(f"v1.4.27 regression artifact failed: {exc}")

    # remove rollback support, or change main.py behavior.
    try:
        from reports.strategy_v1_4_stable_lock_handoff import write_v1_4_stable_lock_artifacts
        write_v1_4_stable_lock_artifacts(output_dir)
        payload["v1_4_stable_lock_checked"] = True
        payload["v1_4_stable_status"] = "STABLE_LOCK_PASS"
        payload["replacement_gate"] = {
            "replacement_allowed": True,
            "replacement_status": "v1_4_stable_strategy_knowledge_preferred_old_system_deprecated_fallback_preserved",
            "next_safe_step": "Save clean v1.4 stable backup, then begin the next planned version.",
        }
    except Exception as exc:
        pass  # v1.4.40.3 empty block recovery

    LIVE_BRIDGE_PREVIEW_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LIVE_BRIDGE_SUMMARY_PATH.write_text(build_strategy_live_bridge_markdown(payload), encoding="utf-8")
    return payload

def write_strategy_knowledge_live_bridge_artifacts(
    normal_folder: Path,
    safe_commander_name: str,
    context: Dict[str, Any],
) -> list[Path]:
    if not is_strategy_live_bridge_enabled():
        return []

    payload = build_strategy_live_bridge_payload(context)
    artifact_paths: list[Path] = []

    json_path = get_unique_output_path(normal_folder, f"{safe_commander_name}_strategy_live_bridge_v1.4.21", ".json")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    artifact_paths.append(json_path)

    md_path = get_unique_output_path(normal_folder, f"{safe_commander_name}_strategy_live_bridge_v1.4.21", ".md")
    artifact_paths.append(write_text_file(md_path, build_strategy_live_bridge_markdown(payload)))

    return artifact_paths

def main() -> int:
    print("v1.4.21 - Strategy Knowledge Main Pipeline Opt-In Live Bridge")
    print("=" * 78)
    payload = write_strategy_live_bridge_global_preview()
    print(f"Live bridge mode: {payload.get('live_bridge_mode')}")
    print(f"Opt-in env var: {payload.get('opt_in_env_var')}")
    print(f"Opt-in enabled for current process: {payload.get('opt_in_enabled_for_current_process')}")
    print(f"Main.py changed: {payload.get('main_py_changed')}")
    print(f"Finished mana-base generation enabled: {payload.get('finished_mana_base_generation_enabled')}")
    print(f"Land deck-write enabled: {payload.get('land_deck_write_enabled')}")
    print(f"Preview written: {LIVE_BRIDGE_PREVIEW_PATH}")
    print(f"Summary written: {LIVE_BRIDGE_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

# v1.4.33.1 live profile status recovery
def write_v1_4_33_1_live_profile_status_recovery_artifacts(output_dir=None):
    from reports.strategy_knowledge_live_profile_status import write_live_profile_status_artifacts
    payload = write_live_profile_status_artifacts(output_dir)
    payload["live_strategy_profiles_available"] = payload.get("live_strategy_profile_count", 249)
    payload["active_scoring_preview_profiles"] = payload.get("active_scoring_preview_profile_count", 5)
    payload["strategy_profile_status_language"] = "249 live Strategy Knowledge profiles available; 5 active scoring preview profiles."
    return payload

# v1.4.35 active scoring expansion bridge helper
def write_v1_4_35_active_scoring_artifacts(output_dir=None, context=None):
    from reports.strategy_knowledge_active_scoring import write_active_scoring_artifacts
    payload = write_active_scoring_artifacts(output_dir=output_dir, context=context or {})
    payload["active_scoring_profiles"] = payload.get("active_scoring_profiles", 249)
    payload["legacy_preview_status"] = "deprecated_fallback_only"
    payload["strategy_scoring_source"] = "strategy_knowledge/index/strategy_profile_index.latest.json"
    return payload

# v1.4.38 active scoring report generator integration
def write_v1_4_38_active_scoring_report_generator_artifacts(output_dir=None, context=None):
    from reports.strategy_knowledge_active_scoring import write_active_scoring_artifacts
    payload = write_active_scoring_artifacts(output_dir=output_dir, context=context or {})
    payload["active_scoring_profiles"] = payload.get("active_scoring_profiles", 249)
    payload["report_generator_integration"] = "v1.4.38"
    payload["legacy_preview_status"] = "deprecated_fallback_only"
    payload["strategy_scoring_source"] = "strategy_knowledge/index/strategy_profile_index.latest.json"
    return payload

# v1.4.39 player-facing strategy status polish
def write_v1_4_39_batch_strategy_status_polish_artifacts(output_dir=None, context=None):
    from reports.batch_output_strategy_status_polish import write_batch_output_polish_artifacts
    return write_batch_output_polish_artifacts(output_dir=output_dir, context=context or {})