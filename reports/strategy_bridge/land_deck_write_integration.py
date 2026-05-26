from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

FINAL_LOCK_PATH = STRATEGY_ROOT / "final_inclusion_lock" / "final_inclusion_lock_v1.4.22.json"
FINISHED_MANA_PATH = STRATEGY_ROOT / "finished_mana_base" / "finished_mana_base_v1.4.23.json"

LAND_WRITE_PATH = STRATEGY_ROOT / "land_deck_write" / "land_deck_write_v1.4.24.json"
LAND_WRITE_SUMMARY_PATH = STRATEGY_ROOT / "land_deck_write" / "LAND_DECK_WRITE_SUMMARY_v1.4.24.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _flatten_mana_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for entry in entries:
        count = int(entry.get("count", 0) or 0)
        if count <= 0:
            continue
        flattened.append({
            "card_name": entry.get("card_name", ""),
            "count": count,
            "source": entry.get("source", ""),
            "deck_write_status": "ready_for_opt_in_land_write_artifact",
            "note": entry.get("note", ""),
        })
    return flattened


def _build_land_write_entry(mana_base: Dict[str, Any], lock_by_strategy: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    strategy_id = mana_base.get("strategy_id", "")
    lock = lock_by_strategy.get(strategy_id, {})
    land_entries = _flatten_mana_entries(mana_base.get("finished_mana_base_entries", []) or [])
    land_count = sum(int(item.get("count", 0)) for item in land_entries)

    return {
        "strategy_id": strategy_id,
        "display_name": mana_base.get("display_name", ""),
        "land_deck_write_mode": "opt_in_land_write_artifact",
        "target_land_slots": mana_base.get("target_land_slots"),
        "land_entries_ready_for_write": land_entries,
        "land_entry_total_count": land_count,
        "locked_candidate_count": lock.get("locked_candidate_count", 0),
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "outside_nonbasic_upgrades_allowed_only_if_user_allows": True,
        "deck_write_validation": {
            "target_land_slots": mana_base.get("target_land_slots"),
            "generated_land_entry_count": mana_base.get("generated_land_entry_count"),
            "land_entry_total_count": land_count,
            "matches_target_land_slots": land_count == int(mana_base.get("target_land_slots", 0) or 0),
        },
        "land_deck_write_boundaries": {
            "land_deck_write_enabled": True,
            "land_deck_write_mode": "artifact_only_no_final_deck_export",
            "final_deck_export_enabled": False,
            "old_strategy_system_removed": False,
            "main_py_changed": False,
        },
    }


def build_land_deck_write_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    final_lock = _load_json(FINAL_LOCK_PATH)
    finished_mana = _load_json(FINISHED_MANA_PATH)

    gate_checks = {
        "final_inclusion_lock_available": final_lock.get("final_inclusion_lock_version") == "v1.4.22"
            and final_lock.get("final_inclusion_lock_enabled") is True,
        "finished_mana_base_available": finished_mana.get("finished_mana_base_generation_version") == "v1.4.23"
            and finished_mana.get("finished_mana_base_generation_enabled") is True,
        "finished_mana_blocks_export": finished_mana.get("final_deck_export_enabled") is False
            and finished_mana.get("land_deck_write_enabled") is False,
        "basic_land_policy_available": finished_mana.get("basic_lands_assumed_available") is True
            and finished_mana.get("nonbasic_lands_collection_first") is True,
    }

    lock_by_strategy = {
        item.get("strategy_id"): item
        for item in final_lock.get("lock_candidates", []) or []
    }

    write_entries = [
        _build_land_write_entry(mana, lock_by_strategy)
        for mana in finished_mana.get("finished_mana_bases", []) or []
    ]

    return {
        "land_deck_write_version": "v1.4.24",
        "integration_mode": "land_deck_write_integration",
        "land_deck_write_enabled": True,
        "land_deck_write_mode": "opt_in_artifact_only_no_final_deck_export",
        "runtime_behavior_changed": True,
        "main_py_changed": False,
        "requires_live_bridge_opt_in": True,
        "opt_in_env_var": "TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE",
        "legacy_pipeline_still_available": True,
        "active_runtime_replacement": False,
        "final_inclusion_lock_enabled": True,
        "finished_mana_base_generation_enabled": True,
        "final_deck_export_enabled": False,
        "old_strategy_system_removed": False,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(write_entries),
        "land_deck_write_entries": write_entries,
        "integration_contract": {
            "may_write_lands_into_deck_artifact": True,
            "may_export_final_deck": False,
            "may_remove_old_strategy_system": False,
            "must_require_explicit_opt_in": True,
            "must_write_lands_as_artifact_before_final_export": True,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "next_integration_step": "v1.4.25 — Final Deck Export Integration",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.24 enables opt-in land deck-write artifacts only. It does not export a final deck or remove the old strategy system.",
            "next_safe_step": "v1.4.25 — Final Deck Export Integration",
        },
    }


def build_land_deck_write_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_land_deck_write_payload({})
    lines: List[str] = [
        "# Land Deck-Write Integration — v1.4.24",
        "",
        "Strategy Knowledge can now produce opt-in land deck-write artifacts from the finished mana-base layer.",
        "",
        "## Boundary",
        "",
        "- Land deck-write: enabled as an opt-in artifact.",
        "- Final deck export: disabled.",
        "- Old strategy system removal: disabled.",
        "- main.py behavior changed in this patch: no.",
        "",
        "## Land Deck-Write Entries",
    ]

    for entry in payload.get("land_deck_write_entries", []):
        validation = entry.get("deck_write_validation", {}) or {}
        lines.append("")
        lines.append(f"### {entry.get('display_name')} (`{entry.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Target land slots: {entry.get('target_land_slots')}")
        lines.append(f"- Land entry total count: {entry.get('land_entry_total_count')}")
        lines.append(f"- Matches target land slots: {validation.get('matches_target_land_slots')}")
        lines.append("- Land deck-write is artifact-only until final deck export is enabled.")

    return "\n".join(lines).rstrip()


def write_land_deck_write_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_land_deck_write_payload(context)
    LAND_WRITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAND_WRITE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LAND_WRITE_SUMMARY_PATH.write_text(build_land_deck_write_summary(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_land_deck_write_v1.4.24.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_LAND_DECK_WRITE_SUMMARY_v1.4.24.md").write_text(
            build_land_deck_write_summary(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_land_deck_write_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_land_deck_write_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines = [
        "## Land Deck-Write Integration",
        "",
        "Strategy Knowledge can now produce opt-in land deck-write artifacts.",
        "",
        "### Boundary",
        "- Land deck-write is enabled as an artifact.",
        "- This does not export a final deck.",
        "- This does not remove the old strategy system.",
        "",
        "### Land Deck-Write Summary",
        f"- Strategy land-write entries generated: {payload.get('checked_strategy_count')}",
        f"- Requires opt-in: {payload.get('requires_live_bridge_opt_in')}",
        f"- Opt-in environment variable: `{payload.get('opt_in_env_var')}`",
    ]
    return "\n".join(lines).rstrip()


def build_land_deck_write_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_land_deck_write_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Land Deck-Write Context",
        "",
        "Strategy Knowledge may now produce land deck-write artifacts when the live bridge is explicitly enabled.",
        "",
        "Rules:",
        "- Treat land deck-write as an artifact layer until final deck export is enabled.",
        "- Do not export a final deck in this stage.",
        "- Do not remove the old strategy system in this stage.",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless the user allows outside upgrades.",
    ]).rstrip()


def build_land_deck_write_viewer_summary() -> str:
    payload = build_land_deck_write_payload({})
    lines = [
        "Land Deck-Write",
        "===============",
        "",
        "Strategy Knowledge can now produce opt-in land deck-write artifacts.",
        "",
        f"Land deck-write entries available: {payload.get('checked_strategy_count')}",
        "Final deck export: disabled",
        "Old strategy system removal: disabled",
        "",
        "This is the land deck-write artifact layer, not final deck export.",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.24 - Land Deck-Write Integration")
    print("=" * 78)
    payload = write_land_deck_write_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Land deck-write enabled: {payload.get('land_deck_write_enabled')}")
    print(f"Land deck-write mode: {payload.get('land_deck_write_mode')}")
    print(f"Final deck export enabled: {payload.get('final_deck_export_enabled')}")
    print(f"Old strategy system removed: {payload.get('old_strategy_system_removed')}")
    print(f"Land deck-write entries available: {payload.get('checked_strategy_count')}")
    print(f"Preview written: {LAND_WRITE_PATH}")
    print(f"Summary written: {LAND_WRITE_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    for entry in payload.get("land_deck_write_entries", []):
        if not entry.get("deck_write_validation", {}).get("matches_target_land_slots"):
            print("Status: FAIL")
            return 1
    print("Status: PASS")
    print("Next safe step: v1.4.25 — Final Deck Export Integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
