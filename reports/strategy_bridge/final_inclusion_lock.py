from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

LIVE_BRIDGE_PATH = STRATEGY_ROOT / "live_bridge" / "strategy_live_bridge_preview_v1.4.21.json"
FULL_DRAFT_PATH = STRATEGY_ROOT / "full_draft_preview" / "full_100_card_draft_preview_v1.4.19.json"
FINAL_LOCK_PATH = STRATEGY_ROOT / "final_inclusion_lock" / "final_inclusion_lock_v1.4.22.json"
FINAL_LOCK_SUMMARY_PATH = STRATEGY_ROOT / "final_inclusion_lock" / "FINAL_INCLUSION_LOCK_SUMMARY_v1.4.22.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _build_lock_candidate(draft: Dict[str, Any]) -> Dict[str, Any]:
    strategy_id = draft.get("strategy_id", "")
    candidates = draft.get("candidate_cards_review_only", []) or []
    land_summary = draft.get("land_slot_summary", {}) or {}

    locked_candidates = [
        {
            "card_name": card_name,
            "lock_status": "locked_for_preview_final_inclusion",
            "lock_reason": "Included from Strategy Knowledge candidate preview for this strategy.",
            "final_export_status": "not_exported_yet",
        }
        for card_name in candidates
    ]

    land_slots = {
        "target_land_slots": land_summary.get("target_land_slots"),
        "preview_basic_land_floor": land_summary.get("preview_basic_land_floor"),
        "preview_nonbasic_review_slots": land_summary.get("preview_nonbasic_review_slots"),
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "lock_status": "land_slots_reserved_not_written",
    }

    return {
        "strategy_id": strategy_id,
        "display_name": draft.get("display_name", ""),
        "final_inclusion_lock_mode": "opt_in_live_bridge_lock_artifact",
        "total_preview_slots": draft.get("total_preview_slots"),
        "commander_slots": draft.get("commander_slots"),
        "nonland_main_deck_slots": draft.get("nonland_main_deck_slots"),
        "land_slots": draft.get("land_slots"),
        "locked_candidate_count": len(locked_candidates),
        "unfilled_nonland_role_slots": draft.get("unfilled_nonland_role_slots_preview"),
        "locked_card_candidates": locked_candidates,
        "land_slot_reservation": land_slots,
        "final_inclusion_boundaries": {
            "final_inclusion_lock_enabled": True,
            "final_inclusion_lock_mode": "artifact_lock_only",
            "final_deck_export_enabled": False,
            "finished_mana_base_generation_enabled": False,
            "land_deck_write_enabled": False,
            "old_strategy_system_removed": False,
        },
    }


def build_final_inclusion_lock_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    live_bridge = _load_json(LIVE_BRIDGE_PATH)
    full_draft = _load_json(FULL_DRAFT_PATH)

    gate_checks = {
        "live_bridge_available": live_bridge.get("live_bridge_version") == "v1.4.21"
            and live_bridge.get("live_bridge_enabled") is True,
        "live_bridge_contract_ready": live_bridge.get("gate_checks", {}).get("ready_for_v1_4_21") is True,
        "full_draft_preview_available": full_draft.get("full_100_card_draft_preview_version") == "v1.4.19"
            and full_draft.get("full_100_card_draft_preview_enabled") is True,
        "full_draft_preview_only": full_draft.get("final_deck_export_enabled") is False
            and full_draft.get("final_deck_inclusion_enabled") is False,
    }

    lock_candidates = [
        _build_lock_candidate(draft)
        for draft in full_draft.get("draft_previews", []) or []
    ]

    return {
        "final_inclusion_lock_version": "v1.4.22",
        "integration_mode": "final_inclusion_lock_integration",
        "final_inclusion_lock_enabled": True,
        "final_inclusion_lock_mode": "opt_in_live_bridge_artifact_lock",
        "runtime_behavior_changed": True,
        "main_py_changed": False,
        "requires_live_bridge_opt_in": True,
        "opt_in_env_var": "TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE",
        "legacy_pipeline_still_available": True,
        "active_runtime_replacement": False,
        "final_deck_export_enabled": False,
        "finished_mana_base_generation_enabled": False,
        "land_deck_write_enabled": False,
        "old_strategy_system_removed": False,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(lock_candidates),
        "lock_candidates": lock_candidates,
        "integration_contract": {
            "may_lock_final_inclusions": True,
            "may_export_final_deck": False,
            "may_generate_finished_mana_base": False,
            "may_write_lands_into_deck": False,
            "may_remove_old_strategy_system": False,
            "must_require_explicit_opt_in": True,
            "must_write_lock_as_artifact_before_final_export": True,
            "next_integration_step": "v1.4.23 — Finished Mana Base Generation Integration",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.22 enables opt-in final-inclusion lock artifacts only. It does not export a final deck, generate a finished mana base, write lands into a deck, or remove the old strategy system.",
            "next_safe_step": "v1.4.23 — Finished Mana Base Generation Integration",
        },
    }


def build_final_inclusion_lock_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_final_inclusion_lock_payload({})
    lines: List[str] = [
        "# Final Inclusion Lock Integration — v1.4.22",
        "",
        "Strategy Knowledge can now produce opt-in final-inclusion lock artifacts through the live bridge.",
        "",
        "## Boundary",
        "",
        "- Final inclusion lock: enabled as an opt-in artifact.",
        "- Final deck export: disabled.",
        "- Finished mana-base generation: disabled.",
        "- Land deck-write: disabled.",
        "- Old strategy system removal: disabled.",
        "",
        "## Lock Candidates",
    ]

    for candidate in payload.get("lock_candidates", []):
        lines.append("")
        lines.append(f"### {candidate.get('display_name')} (`{candidate.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Locked candidate count: {candidate.get('locked_candidate_count')}")
        lines.append(f"- Unfilled nonland role slots: {candidate.get('unfilled_nonland_role_slots')}")
        land = candidate.get("land_slot_reservation", {}) or {}
        lines.append(f"- Reserved land slots: {land.get('target_land_slots')}")
        lines.append("- Locked candidates are artifact-level locks only until final deck export is enabled.")

    return "\n".join(lines).rstrip()


def write_final_inclusion_lock_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_final_inclusion_lock_payload(context)
    FINAL_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINAL_LOCK_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    FINAL_LOCK_SUMMARY_PATH.write_text(build_final_inclusion_lock_summary(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_final_inclusion_lock_v1.4.22.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_FINAL_INCLUSION_LOCK_SUMMARY_v1.4.22.md").write_text(
            build_final_inclusion_lock_summary(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_final_inclusion_lock_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_final_inclusion_lock_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines = [
        "## Final Inclusion Lock Integration",
        "",
        "Strategy Knowledge can now produce opt-in final-inclusion lock artifacts.",
        "",
        "### Boundary",
        "- Final inclusion lock is enabled as an opt-in artifact.",
        "- This does not export a final deck.",
        "- This does not generate a finished mana base.",
        "- This does not write lands into a deck.",
        "- This does not remove the old strategy system.",
        "",
        "### Lock Summary",
        f"- Strategy lock candidates: {payload.get('checked_strategy_count')}",
        f"- Requires opt-in: {payload.get('requires_live_bridge_opt_in')}",
        f"- Opt-in environment variable: `{payload.get('opt_in_env_var')}`",
    ]
    return "\n".join(lines).rstrip()


def build_final_inclusion_lock_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_final_inclusion_lock_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Final Inclusion Lock Context",
        "",
        "Strategy Knowledge may now produce final-inclusion lock artifacts when the live bridge is explicitly enabled.",
        "",
        "Rules:",
        "- Treat lock artifacts as the final-inclusion decision layer.",
        "- Do not export a final deck in this stage.",
        "- Do not generate a finished mana base in this stage.",
        "- Do not write lands into a deck in this stage.",
        "- Do not remove the old strategy system in this stage.",
    ]).rstrip()


def build_final_inclusion_lock_viewer_summary() -> str:
    payload = build_final_inclusion_lock_payload({})
    lines = [
        "Final Inclusion Lock",
        "====================",
        "",
        "Strategy Knowledge can now produce opt-in final-inclusion lock artifacts.",
        "",
        f"Lock candidates available: {payload.get('checked_strategy_count')}",
        "Final deck export: disabled",
        "Finished mana-base generation: disabled",
        "Land deck-write: disabled",
        "Old system removal: disabled",
        "",
        "This is the final-inclusion decision layer, not the final deck export layer.",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.22 - Final Inclusion Lock Integration")
    print("=" * 78)
    payload = write_final_inclusion_lock_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Final inclusion lock enabled: {payload.get('final_inclusion_lock_enabled')}")
    print(f"Final inclusion lock mode: {payload.get('final_inclusion_lock_mode')}")
    print(f"Final deck export enabled: {payload.get('final_deck_export_enabled')}")
    print(f"Finished mana-base generation enabled: {payload.get('finished_mana_base_generation_enabled')}")
    print(f"Land deck-write enabled: {payload.get('land_deck_write_enabled')}")
    print(f"Lock candidates available: {payload.get('checked_strategy_count')}")
    print(f"Preview written: {FINAL_LOCK_PATH}")
    print(f"Summary written: {FINAL_LOCK_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.23 — Finished Mana Base Generation Integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
