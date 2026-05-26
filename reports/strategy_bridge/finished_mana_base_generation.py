from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

FINAL_LOCK_PATH = STRATEGY_ROOT / "final_inclusion_lock" / "final_inclusion_lock_v1.4.22.json"
MANA_PLAN_PATH = STRATEGY_ROOT / "mana_base" / "mana_base_plan_v1.4.17.json"
LAND_INSERTION_PATH = STRATEGY_ROOT / "land_insertion" / "land_insertion_preview_v1.4.18.json"
FINISHED_MANA_PATH = STRATEGY_ROOT / "finished_mana_base" / "finished_mana_base_v1.4.23.json"
FINISHED_MANA_SUMMARY_PATH = STRATEGY_ROOT / "finished_mana_base" / "FINISHED_MANA_BASE_SUMMARY_v1.4.23.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _basic_land_mix(target_basic_count: int, strategy_id: str) -> List[Dict[str, Any]]:
    # This is intentionally conservative and color-agnostic until commander color parsing is wired into this layer.
    # The point of v1.4.23 is to cross finished mana-base artifact generation, not to overwrite a deck file.
    if target_basic_count <= 0:
        return []

    if strategy_id == "landfall_lands_matter":
        split = [("Forest", max(1, target_basic_count // 2)), ("Island", max(0, target_basic_count // 4))]
    elif strategy_id == "spellslinger":
        split = [("Island", max(1, target_basic_count // 2)), ("Mountain", max(0, target_basic_count // 4))]
    elif strategy_id == "voltron":
        split = [("Plains", max(1, target_basic_count // 2)), ("Mountain", max(0, target_basic_count // 4))]
    elif strategy_id == "aristocrats":
        split = [("Swamp", max(1, target_basic_count // 2)), ("Plains", max(0, target_basic_count // 4))]
    else:
        split = [("Forest", max(1, target_basic_count // 3)), ("Plains", max(0, target_basic_count // 3))]

    used = sum(count for _, count in split)
    if used < target_basic_count:
        split.append(("Basic Land Placeholder", target_basic_count - used))
    elif used > target_basic_count:
        name, count = split[-1]
        split[-1] = (name, max(0, count - (used - target_basic_count)))

    return [
        {
            "card_name": name,
            "count": count,
            "source": "assumed_available_basic_land",
            "final_mana_base_status": "generated_artifact_entry",
        }
        for name, count in split
        if count > 0
    ]


def _build_finished_mana_entry(lock: Dict[str, Any], land_preview_by_strategy: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    strategy_id = lock.get("strategy_id", "")
    land_reservation = lock.get("land_slot_reservation", {}) or {}
    land_preview = land_preview_by_strategy.get(strategy_id, {})
    target_lands = int(land_reservation.get("target_land_slots") or land_preview.get("target_land_slots") or 37)
    basic_floor = int(land_reservation.get("preview_basic_land_floor") or land_preview.get("preview_basic_land_floor") or max(12, target_lands - 20))
    nonbasic_slots = max(0, target_lands - basic_floor)

    basics = _basic_land_mix(basic_floor, strategy_id)
    nonbasic_placeholders = [
        {
            "card_name": "Owned Nonbasic Land Review Slot",
            "count": nonbasic_slots,
            "source": "collection_first_nonbasic_slot",
            "final_mana_base_status": "generated_artifact_slot_not_deck_write",
            "note": "Fill from owned nonbasic lands first; outside upgrades only if user allows them.",
        }
    ] if nonbasic_slots > 0 else []

    generated_entries = basics + nonbasic_placeholders
    generated_count = sum(int(item.get("count", 0)) for item in generated_entries)

    return {
        "strategy_id": strategy_id,
        "display_name": lock.get("display_name", ""),
        "finished_mana_base_mode": "artifact_generation_only",
        "target_land_slots": target_lands,
        "generated_land_entry_count": generated_count,
        "basic_land_count": basic_floor,
        "nonbasic_review_slot_count": nonbasic_slots,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "outside_nonbasic_upgrades_allowed_only_if_user_allows": True,
        "finished_mana_base_entries": generated_entries,
        "mana_base_boundaries": {
            "finished_mana_base_generation_enabled": True,
            "finished_mana_base_generation_mode": "artifact_only_no_deck_write",
            "land_deck_write_enabled": False,
            "final_deck_export_enabled": False,
            "old_strategy_system_removed": False,
        },
    }


def build_finished_mana_base_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    final_lock = _load_json(FINAL_LOCK_PATH)
    mana_plan = _load_json(MANA_PLAN_PATH)
    land_insertion = _load_json(LAND_INSERTION_PATH)

    gate_checks = {
        "final_inclusion_lock_available": final_lock.get("final_inclusion_lock_version") == "v1.4.22"
            and final_lock.get("final_inclusion_lock_enabled") is True,
        "final_lock_blocks_export": final_lock.get("final_deck_export_enabled") is False
            and final_lock.get("land_deck_write_enabled") is False,
        "mana_base_planning_available": mana_plan.get("mana_base_planning_version") == "v1.4.17"
            and mana_plan.get("mana_base_planning_enabled") is True,
        "land_insertion_preview_available": land_insertion.get("land_insertion_preview_version") == "v1.4.18"
            and land_insertion.get("land_insertion_preview_enabled") is True,
    }

    land_preview_by_strategy = {
        item.get("strategy_id"): item
        for item in land_insertion.get("land_insertion_previews", []) or []
    }

    finished_entries = [
        _build_finished_mana_entry(lock, land_preview_by_strategy)
        for lock in final_lock.get("lock_candidates", []) or []
    ]

    return {
        "finished_mana_base_generation_version": "v1.4.23",
        "integration_mode": "finished_mana_base_generation_integration",
        "finished_mana_base_generation_enabled": True,
        "finished_mana_base_generation_mode": "artifact_only_no_deck_write",
        "runtime_behavior_changed": True,
        "main_py_changed": False,
        "requires_live_bridge_opt_in": True,
        "opt_in_env_var": "TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE",
        "legacy_pipeline_still_available": True,
        "active_runtime_replacement": False,
        "final_inclusion_lock_enabled": True,
        "final_deck_export_enabled": False,
        "land_deck_write_enabled": False,
        "old_strategy_system_removed": False,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(finished_entries),
        "finished_mana_bases": finished_entries,
        "integration_contract": {
            "may_generate_finished_mana_base": True,
            "may_write_lands_into_deck": False,
            "may_export_final_deck": False,
            "may_remove_old_strategy_system": False,
            "must_require_explicit_opt_in": True,
            "must_generate_mana_base_as_artifact_before_deck_write": True,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "next_integration_step": "v1.4.24 — Land Deck-Write Integration",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.23 enables opt-in finished mana-base artifacts only. It does not write lands into a deck, export a final deck, or remove the old strategy system.",
            "next_safe_step": "v1.4.24 — Land Deck-Write Integration",
        },
    }


def build_finished_mana_base_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_finished_mana_base_payload({})
    lines: List[str] = [
        "# Finished Mana Base Generation Integration — v1.4.23",
        "",
        "Strategy Knowledge can now generate opt-in finished mana-base artifacts.",
        "",
        "## Boundary",
        "",
        "- Finished mana-base generation: enabled as an artifact.",
        "- Land deck-write: disabled.",
        "- Final deck export: disabled.",
        "- Old strategy system removal: disabled.",
        "",
        "## Finished Mana Bases",
    ]

    for entry in payload.get("finished_mana_bases", []):
        lines.append("")
        lines.append(f"### {entry.get('display_name')} (`{entry.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Target land slots: {entry.get('target_land_slots')}")
        lines.append(f"- Generated land entry count: {entry.get('generated_land_entry_count')}")
        lines.append(f"- Basic land count: {entry.get('basic_land_count')}")
        lines.append(f"- Nonbasic review slots: {entry.get('nonbasic_review_slot_count')}")
        lines.append("- Finished mana base is artifact-only until land deck-write is enabled.")

    return "\n".join(lines).rstrip()


def write_finished_mana_base_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_finished_mana_base_payload(context)
    FINISHED_MANA_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINISHED_MANA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    FINISHED_MANA_SUMMARY_PATH.write_text(build_finished_mana_base_summary(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_finished_mana_base_v1.4.23.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_FINISHED_MANA_BASE_SUMMARY_v1.4.23.md").write_text(
            build_finished_mana_base_summary(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_finished_mana_base_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_finished_mana_base_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines = [
        "## Finished Mana Base Generation Integration",
        "",
        "Strategy Knowledge can now generate opt-in finished mana-base artifacts.",
        "",
        "### Boundary",
        "- Finished mana-base generation is enabled as an artifact.",
        "- This does not write lands into a deck.",
        "- This does not export a final deck.",
        "- This does not remove the old strategy system.",
        "",
        "### Mana Base Summary",
        f"- Strategy mana bases generated: {payload.get('checked_strategy_count')}",
        f"- Requires opt-in: {payload.get('requires_live_bridge_opt_in')}",
        f"- Opt-in environment variable: `{payload.get('opt_in_env_var')}`",
    ]
    return "\n".join(lines).rstrip()


def build_finished_mana_base_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_finished_mana_base_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Finished Mana Base Context",
        "",
        "Strategy Knowledge may now generate finished mana-base artifacts when the live bridge is explicitly enabled.",
        "",
        "Rules:",
        "- Treat finished mana bases as artifacts until land deck-write is enabled.",
        "- Do not write lands into a deck in this stage.",
        "- Do not export a final deck in this stage.",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless the user allows outside upgrades.",
    ]).rstrip()


def build_finished_mana_base_viewer_summary() -> str:
    payload = build_finished_mana_base_payload({})
    lines = [
        "Finished Mana Base",
        "==================",
        "",
        "Strategy Knowledge can now generate opt-in finished mana-base artifacts.",
        "",
        f"Finished mana bases available: {payload.get('checked_strategy_count')}",
        "Land deck-write: disabled",
        "Final deck export: disabled",
        "Old strategy system removal: disabled",
        "",
        "This is the finished mana-base artifact layer, not deck-write/export.",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.23 - Finished Mana Base Generation Integration")
    print("=" * 78)
    payload = write_finished_mana_base_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Finished mana-base generation enabled: {payload.get('finished_mana_base_generation_enabled')}")
    print(f"Finished mana-base generation mode: {payload.get('finished_mana_base_generation_mode')}")
    print(f"Land deck-write enabled: {payload.get('land_deck_write_enabled')}")
    print(f"Final deck export enabled: {payload.get('final_deck_export_enabled')}")
    print(f"Finished mana bases available: {payload.get('checked_strategy_count')}")
    print(f"Preview written: {FINISHED_MANA_PATH}")
    print(f"Summary written: {FINISHED_MANA_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.24 — Land Deck-Write Integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
