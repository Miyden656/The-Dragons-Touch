from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

RUNTIME_CONTRACT_PATH = STRATEGY_ROOT / "runtime" / "strategy_brain_runtime_contract_v1.4.9.json"
SCORING_PREVIEW_PATH = STRATEGY_ROOT / "scoring_previews" / "strategy_scoring_integration_preview_v1.4.10.json"
ROLE_MAPPING_PATH = STRATEGY_ROOT / "role_mapping" / "strategy_role_bucket_mapping_v1.4.11.json"
CUT_PROTECT_PATH = STRATEGY_ROOT / "cut_protect_replacement" / "strategy_cut_protect_replacement_v1.4.12.json"
HANDOFF_PREVIEW_PATH = STRATEGY_ROOT / "report_viewer_handoff" / "strategy_report_viewer_handoff_preview_v1.4.13.json"
SHELL_PLAN_PATH = STRATEGY_ROOT / "shell_planning" / "strategy_shell_plan_v1.4.14.json"
CANDIDATE_PREVIEW_PATH = STRATEGY_ROOT / "card_candidates" / "exact_card_candidate_preview_v1.4.15.json"
ROLE_COUNT_PLAN_PATH = STRATEGY_ROOT / "role_counts" / "strategy_role_count_plan_v1.4.16.json"
MANA_PLAN_PATH = STRATEGY_ROOT / "mana_base" / "mana_base_plan_v1.4.17.json"
LAND_INSERTION_PATH = STRATEGY_ROOT / "land_insertion" / "land_insertion_preview_v1.4.18.json"

FULL_DRAFT_PATH = STRATEGY_ROOT / "full_draft_preview" / "full_100_card_draft_preview_v1.4.19.json"
FULL_DRAFT_SUMMARY_PATH = STRATEGY_ROOT / "full_draft_preview" / "FULL_100_CARD_DRAFT_PREVIEW_SUMMARY_v1.4.19.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _candidate_names(candidate_set: Dict[str, Any]) -> List[str]:
    return [card.get("card_name", "") for card in candidate_set.get("candidate_cards", []) if card.get("card_name")]


def _target_role_summary(role_plan: Dict[str, Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for role, band in (role_plan.get("target_role_bands", {}) or {}).items():
        if role == "lands":
            continue
        try:
            out[role] = int(band.get("target", 0))
        except Exception:
            out[role] = 0
    return out


def _build_full_draft_preview(
    role_plan: Dict[str, Any],
    land_preview: Dict[str, Any],
    candidate_set: Dict[str, Any],
) -> Dict[str, Any]:
    target_land_slots = int(land_preview.get("target_land_slots", 37))
    commander_slots = 1
    main_deck_slots = 99
    nonland_main_deck_slots = max(0, main_deck_slots - target_land_slots)
    total_preview_slots = commander_slots + nonland_main_deck_slots + target_land_slots

    candidates = _candidate_names(candidate_set)
    candidate_slots = min(len(candidates), nonland_main_deck_slots)

    return {
        "strategy_id": role_plan.get("strategy_id", ""),
        "display_name": role_plan.get("display_name", ""),
        "draft_preview_mode": "full_100_card_preview_only",
        "total_preview_slots": total_preview_slots,
        "commander_slots": commander_slots,
        "main_deck_slots": main_deck_slots,
        "nonland_main_deck_slots": nonland_main_deck_slots,
        "land_slots": target_land_slots,
        "candidate_slots_previewed": candidate_slots,
        "unfilled_nonland_role_slots_preview": max(0, nonland_main_deck_slots - candidate_slots),
        "candidate_cards_review_only": candidates[:candidate_slots],
        "target_role_summary": _target_role_summary(role_plan),
        "land_slot_summary": {
            "target_land_slots": target_land_slots,
            "preview_basic_land_floor": land_preview.get("preview_basic_land_floor"),
            "preview_nonbasic_review_slots": land_preview.get("preview_nonbasic_review_slots"),
            "basic_lands_assumed_available": True,
            "nonbasic_lands_collection_first": True,
        },
        "draft_guidance": [
            "This is a full 100-card draft preview structure, not a final deck list.",
            "Candidate cards remain review-only until final inclusion is enabled.",
            "Land slots are previewed but not written into a final deck.",
            "Basic lands are assumed available.",
            "Nonbasic lands remain collection-first unless outside upgrades are allowed.",
            "Use role targets as planning bands, not rigid final counts.",
        ],
        "full_draft_boundaries": {
            "full_100_card_draft_preview_enabled": True,
            "full_100_card_draft_generation_enabled": True,
            "full_100_card_draft_generation_mode": "preview_only_no_final_deck_export",
            "final_deck_export_enabled": False,
            "final_deck_inclusion_enabled": False,
            "finished_mana_base_generation_enabled": False,
            "land_insertion_deck_write_enabled": False,
            "main_py_changed": False,
        },
    }


def build_full_100_card_draft_preview_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)
    handoff = _load_json(HANDOFF_PREVIEW_PATH)
    shell_plan = _load_json(SHELL_PLAN_PATH)
    candidates = _load_json(CANDIDATE_PREVIEW_PATH)
    role_counts = _load_json(ROLE_COUNT_PLAN_PATH)
    mana_base = _load_json(MANA_PLAN_PATH)
    land_insertion = _load_json(LAND_INSERTION_PATH)

    gate_checks = {
        "runtime_contract_available": runtime.get("runtime_contract_version") == "v1.4.9",
        "strategy_knowledge_selected_with_fallback": runtime.get("strategy_knowledge_selected_as_default_strategy_brain") is True
            and runtime.get("legacy_fallback_required") is True,
        "scoring_preview_available": scoring.get("scoring_preview_version") == "v1.4.10"
            and scoring.get("scenario_match_count") == scoring.get("scenario_count"),
        "role_mapping_available": role_mapping.get("role_mapping_version") == "v1.4.11"
            and role_mapping.get("sample_mapping_warning_count") == 0,
        "cut_protect_available": cut_protect.get("cut_protect_replacement_version") == "v1.4.12"
            and cut_protect.get("sample_warning_count") == 0,
        "report_handoff_available": handoff.get("integration_version") == "v1.4.13"
            and handoff.get("report_viewer_strategy_section_enabled") is True,
        "shell_planning_available": shell_plan.get("shell_planning_version") == "v1.4.14"
            and shell_plan.get("strategy_shell_planning_enabled") is True,
        "candidate_preview_available": candidates.get("candidate_preview_version") == "v1.4.15"
            and candidates.get("exact_card_candidate_preview_enabled") is True,
        "role_count_generation_available": role_counts.get("role_count_generation_version") == "v1.4.16"
            and role_counts.get("role_count_generation_enabled") is True,
        "mana_base_planning_available": mana_base.get("mana_base_planning_version") == "v1.4.17"
            and mana_base.get("mana_base_planning_enabled") is True,
        "land_insertion_preview_available": land_insertion.get("land_insertion_preview_version") == "v1.4.18"
            and land_insertion.get("land_insertion_preview_enabled") is True,
    }

    candidate_by_strategy = {
        item.get("strategy_id"): item for item in candidates.get("candidate_sets", []) or []
    }
    land_by_strategy = {
        item.get("strategy_id"): item for item in land_insertion.get("land_insertion_previews", []) or []
    }

    draft_previews = []
    for role_plan in role_counts.get("role_count_plans", []) or []:
        strategy_id = role_plan.get("strategy_id", "")
        draft_previews.append(
            _build_full_draft_preview(
                role_plan,
                land_by_strategy.get(strategy_id, {}),
                candidate_by_strategy.get(strategy_id, {}),
            )
        )

    return {
        "full_100_card_draft_preview_version": "v1.4.19",
        "integration_mode": "full_100_card_draft_preview",
        "full_100_card_draft_preview_enabled": True,
        "full_100_card_draft_generation_enabled": True,
        "full_100_card_draft_generation_mode": "preview_only_no_final_deck_export",
        "deck_generation_enabled": True,
        "deck_generation_mode": "preview_draft_only",
        "runtime_behavior_changed": True,
        "report_output_changed": True,
        "prompt_output_changed": True,
        "report_viewer_changed": True,
        "main_py_changed": False,
        "legacy_fallback_required": True,
        "active_runtime_replacement": False,
        "exact_card_selection_enabled": True,
        "exact_card_selection_mode": "preview_candidates_only",
        "role_count_generation_enabled": True,
        "role_count_generation_mode": "target_bands_only",
        "shell_generation_enabled": True,
        "shell_generation_mode": "rough_strategy_shell_planning_only",
        "mana_base_planning_enabled": True,
        "mana_base_generation_enabled": False,
        "land_insertion_enabled": True,
        "land_insertion_mode": "preview_only_no_deck_write",
        "final_land_list_generation_enabled": False,
        "final_deck_inclusion_enabled": False,
        "final_deck_export_enabled": False,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(draft_previews),
        "draft_previews": draft_previews,
        "integration_contract": {
            "may_generate_full_100_card_draft_preview": True,
            "may_export_final_deck": False,
            "may_lock_final_deck_inclusions": False,
            "may_generate_finished_mana_base": False,
            "may_write_lands_into_deck": False,
            "must_label_output_as_preview_only": True,
            "must_keep_collection_first": True,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "next_integration_step": "v1.4.20 — Final Draft Review / Lock Candidate",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.19 creates a full 100-slot draft preview only. It does not export a final deck or lock card inclusions.",
            "next_safe_step": "v1.4.20 — Final Draft Review / Lock Candidate",
        },
    }


def build_full_100_card_draft_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_full_100_card_draft_preview_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Full 100-Card Draft Preview",
        "",
        "Strategy Knowledge can now build a preview-only 100-slot Commander draft structure.",
        "",
        "### Boundary",
        "- This is a preview only.",
        "- This does not export a final deck.",
        "- This does not lock final deck inclusions.",
        "- This does not generate a finished mana base or write lands into a deck.",
        "",
        "### Draft Previews",
    ]

    for draft in payload.get("draft_previews", []):
        lines.append("")
        lines.append(f"#### {draft.get('display_name')} (`{draft.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Total preview slots: {draft.get('total_preview_slots')}")
        lines.append(f"- Commander slots: {draft.get('commander_slots')}")
        lines.append(f"- Nonland main-deck slots: {draft.get('nonland_main_deck_slots')}")
        lines.append(f"- Land slots: {draft.get('land_slots')}")
        lines.append(f"- Candidate cards previewed: {draft.get('candidate_slots_previewed')}")
        lines.append(f"- Unfilled nonland role slots: {draft.get('unfilled_nonland_role_slots_preview')}")

    return "\n".join(lines).rstrip()


def build_full_100_card_draft_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_full_100_card_draft_preview_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Full 100-Card Draft Preview Context",
        "",
        "Strategy Knowledge may generate a preview-only 100-slot Commander draft structure.",
        "",
        "Rules:",
        "- Treat this as a draft preview, not a final deck export.",
        "- Do not lock final deck inclusions in this stage.",
        "- Do not treat candidate cards as mandatory inclusions.",
        "- Do not generate a finished mana base or write lands into a deck.",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless outside upgrades are allowed.",
    ]).rstrip()


def build_full_100_card_draft_viewer_summary() -> str:
    payload = build_full_100_card_draft_preview_payload({})
    lines = [
        "Full 100-Card Draft Preview",
        "===========================",
        "",
        "Strategy Knowledge can now preview a 100-slot Commander draft structure.",
        "",
        f"Draft previews available: {payload.get('checked_strategy_count')}",
        "Deck generation mode: preview draft only",
        "Final deck export: disabled",
        "Final deck inclusion lock: disabled",
        "Finished mana-base generation: disabled",
        "Land deck-write: disabled",
        "",
        "Use this as a planning draft, not a final deck list.",
    ]
    return "\n".join(lines).rstrip()


def write_full_100_card_draft_preview() -> Dict[str, Any]:
    payload = build_full_100_card_draft_preview_payload({})
    FULL_DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FULL_DRAFT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    FULL_DRAFT_SUMMARY_PATH.write_text(build_full_100_card_draft_report_section({}) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("v1.4.19 - Full 100-Card Draft Preview")
    print("=" * 78)
    payload = write_full_100_card_draft_preview()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Full draft generation mode: {payload.get('full_100_card_draft_generation_mode')}")
    print(f"Draft previews available: {payload.get('checked_strategy_count')}")
    print(f"Deck generation mode: {payload.get('deck_generation_mode')}")
    print(f"Final deck export enabled: {payload.get('final_deck_export_enabled')}")
    print(f"Final deck inclusion enabled: {payload.get('final_deck_inclusion_enabled')}")
    print(f"Preview written: {FULL_DRAFT_PATH}")
    print(f"Summary written: {FULL_DRAFT_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    for draft in payload.get("draft_previews", []):
        if draft.get("total_preview_slots") != 100:
            print("Status: FAIL")
            return 1
    print("Status: PASS")
    print("Next safe step: v1.4.20 — Final Draft Review / Lock Candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
