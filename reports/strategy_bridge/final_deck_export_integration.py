from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

FINAL_LOCK_PATH = STRATEGY_ROOT / "final_inclusion_lock" / "final_inclusion_lock_v1.4.22.json"
LAND_WRITE_PATH = STRATEGY_ROOT / "land_deck_write" / "land_deck_write_v1.4.24.json"

FINAL_EXPORT_PATH = STRATEGY_ROOT / "final_deck_export" / "final_deck_export_v1.4.25.json"
FINAL_EXPORT_SUMMARY_PATH = STRATEGY_ROOT / "final_deck_export" / "FINAL_DECK_EXPORT_SUMMARY_v1.4.25.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _deck_lines_from_entries(cards: List[Dict[str, Any]], lands: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for item in cards:
        name = item.get("card_name", "")
        if name:
            lines.append(f"1 {name}")
    for item in lands:
        count = int(item.get("count", 0) or 0)
        name = item.get("card_name", "")
        if count > 0 and name:
            lines.append(f"{count} {name}")
    return lines


def _build_export_entry(lock: Dict[str, Any], land_write_by_strategy: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    strategy_id = lock.get("strategy_id", "")
    land_write = land_write_by_strategy.get(strategy_id, {})
    locked_cards = lock.get("locked_card_candidates", []) or []
    land_entries = land_write.get("land_entries_ready_for_write", []) or []
    deck_lines = _deck_lines_from_entries(locked_cards, land_entries)

    return {
        "strategy_id": strategy_id,
        "display_name": lock.get("display_name", ""),
        "final_deck_export_mode": "opt_in_strategy_knowledge_export_artifact",
        "export_format": "plain_text_decklist_lines",
        "locked_nonland_card_count": len(locked_cards),
        "land_entry_total_count": land_write.get("land_entry_total_count", 0),
        "export_line_count": len(deck_lines),
        "decklist_lines": deck_lines,
        "export_warnings": [
            "This is a Strategy Knowledge export artifact.",
            "Old strategy system removal is not enabled in v1.4.25.",
            "Review exported decklist before treating it as a player-ready deck.",
        ],
        "final_export_boundaries": {
            "final_deck_export_enabled": True,
            "final_deck_export_mode": "artifact_export_only",
            "old_strategy_system_removed": False,
            "legacy_pipeline_still_available": True,
            "main_py_changed": False,
        },
    }


def build_final_deck_export_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    final_lock = _load_json(FINAL_LOCK_PATH)
    land_write = _load_json(LAND_WRITE_PATH)

    gate_checks = {
        "final_inclusion_lock_available": final_lock.get("final_inclusion_lock_version") == "v1.4.22"
            and final_lock.get("final_inclusion_lock_enabled") is True,
        "land_deck_write_available": land_write.get("land_deck_write_version") == "v1.4.24"
            and land_write.get("land_deck_write_enabled") is True,
        "land_write_blocks_old_system_removal": land_write.get("old_strategy_system_removed") is False,
        "basic_land_policy_available": land_write.get("basic_lands_assumed_available") is True
            and land_write.get("nonbasic_lands_collection_first") is True,
    }

    land_write_by_strategy = {
        item.get("strategy_id"): item
        for item in land_write.get("land_deck_write_entries", []) or []
    }

    export_entries = [
        _build_export_entry(lock, land_write_by_strategy)
        for lock in final_lock.get("lock_candidates", []) or []
    ]

    return {
        "final_deck_export_version": "v1.4.25",
        "integration_mode": "final_deck_export_integration",
        "final_deck_export_enabled": True,
        "final_deck_export_mode": "opt_in_artifact_export_only",
        "runtime_behavior_changed": True,
        "main_py_changed": False,
        "requires_live_bridge_opt_in": True,
        "opt_in_env_var": "TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE",
        "legacy_pipeline_still_available": True,
        "active_runtime_replacement": False,
        "final_inclusion_lock_enabled": True,
        "finished_mana_base_generation_enabled": True,
        "land_deck_write_enabled": True,
        "old_strategy_system_removed": False,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(export_entries),
        "final_deck_exports": export_entries,
        "integration_contract": {
            "may_export_final_deck_artifact": True,
            "may_remove_old_strategy_system": False,
            "must_require_explicit_opt_in": True,
            "must_keep_legacy_pipeline_available": True,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "next_integration_step": "v1.4.26 — Old Strategy System Deprecation / Fallback Cleanup",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.25 enables opt-in final deck export artifacts only. Old strategy system removal remains disabled until v1.4.26.",
            "next_safe_step": "v1.4.26 — Old Strategy System Deprecation / Fallback Cleanup",
        },
    }


def build_final_deck_export_summary(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_final_deck_export_payload({})
    lines: List[str] = [
        "# Final Deck Export Integration — v1.4.25",
        "",
        "Strategy Knowledge can now produce opt-in final deck export artifacts.",
        "",
        "## Boundary",
        "",
        "- Final deck export: enabled as an opt-in artifact.",
        "- Old strategy system removal: disabled.",
        "- Legacy pipeline: still available.",
        "- main.py behavior changed in this patch: no.",
        "",
        "## Final Deck Export Entries",
    ]

    for entry in payload.get("final_deck_exports", []):
        lines.append("")
        lines.append(f"### {entry.get('display_name')} (`{entry.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Locked nonland cards: {entry.get('locked_nonland_card_count')}")
        lines.append(f"- Land entries total count: {entry.get('land_entry_total_count')}")
        lines.append(f"- Export line count: {entry.get('export_line_count')}")
        lines.append("- Export is artifact-only until old strategy system cleanup is explicitly performed.")

    return "\n".join(lines).rstrip()


def write_final_deck_export_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_final_deck_export_payload(context)
    FINAL_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINAL_EXPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    FINAL_EXPORT_SUMMARY_PATH.write_text(build_final_deck_export_summary(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_final_deck_export_v1.4.25.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_FINAL_DECK_EXPORT_SUMMARY_v1.4.25.md").write_text(
            build_final_deck_export_summary(payload) + "\n",
            encoding="utf-8",
        )
        for entry in payload.get("final_deck_exports", []):
            slug = str(entry.get("strategy_id", "strategy")).replace("/", "_").replace(" ", "_")
            deck_lines = entry.get("decklist_lines", []) or []
            (out / f"STRATEGY_FINAL_DECK_EXPORT_{slug}_v1.4.25.txt").write_text(
                "\n".join(deck_lines).rstrip() + "\n",
                encoding="utf-8",
            )

    return payload


def build_final_deck_export_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_final_deck_export_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines = [
        "## Final Deck Export Integration",
        "",
        "Strategy Knowledge can now produce opt-in final deck export artifacts.",
        "",
        "### Boundary",
        "- Final deck export is enabled as an artifact.",
        "- This does not remove the old strategy system.",
        "- Legacy fallback remains available.",
        "",
        "### Final Deck Export Summary",
        f"- Strategy exports generated: {payload.get('checked_strategy_count')}",
        f"- Requires opt-in: {payload.get('requires_live_bridge_opt_in')}",
        f"- Opt-in environment variable: `{payload.get('opt_in_env_var')}`",
    ]
    return "\n".join(lines).rstrip()


def build_final_deck_export_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_final_deck_export_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Final Deck Export Context",
        "",
        "Strategy Knowledge may now produce final deck export artifacts when the live bridge is explicitly enabled.",
        "",
        "Rules:",
        "- Treat final deck export as an opt-in artifact layer.",
        "- Do not remove the old strategy system in this stage.",
        "- Keep legacy fallback available.",
        "- Review exported decklists before treating them as player-ready decks.",
    ]).rstrip()


def build_final_deck_export_viewer_summary() -> str:
    payload = build_final_deck_export_payload({})
    lines = [
        "Final Deck Export",
        "=================",
        "",
        "Strategy Knowledge can now produce opt-in final deck export artifacts.",
        "",
        f"Final deck exports available: {payload.get('checked_strategy_count')}",
        "Old strategy system removal: disabled",
        "Legacy pipeline: still available",
        "",
        "This is the final deck export artifact layer, not old system removal.",
    ]
    return "\n".join(lines).rstrip()


def main() -> int:
    print("v1.4.25 - Final Deck Export Integration")
    print("=" * 78)
    payload = write_final_deck_export_artifacts()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Final deck export enabled: {payload.get('final_deck_export_enabled')}")
    print(f"Final deck export mode: {payload.get('final_deck_export_mode')}")
    print(f"Old strategy system removed: {payload.get('old_strategy_system_removed')}")
    print(f"Final deck exports available: {payload.get('checked_strategy_count')}")
    print(f"Preview written: {FINAL_EXPORT_PATH}")
    print(f"Summary written: {FINAL_EXPORT_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    for entry in payload.get("final_deck_exports", []):
        if entry.get("export_line_count", 0) <= 0:
            print("Status: FAIL")
            return 1
    print("Status: PASS")
    print("Next safe step: v1.4.26 — Old Strategy System Deprecation / Fallback Cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
