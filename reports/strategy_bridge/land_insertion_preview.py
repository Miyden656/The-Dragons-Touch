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
LAND_INSERTION_SUMMARY_PATH = STRATEGY_ROOT / "land_insertion" / "LAND_INSERTION_PREVIEW_SUMMARY_v1.4.18.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _preview_land_slots(mana_plan: Dict[str, Any]) -> Dict[str, Any]:
    band = mana_plan.get("recommended_land_band", {}) or {}
    target_lands = int(band.get("target", 37))
    strategy_id = mana_plan.get("strategy_id", "")

    # Preview-only split. This is intentionally not a final mana-base generator.
    # Basics are assumed available, while nonbasics stay collection-first.
    if strategy_id == "landfall_lands_matter":
        basic_min = max(14, target_lands - 20)
        nonbasic_review = target_lands - basic_min
        priority_notes = [
            "Preview more land slots than normal because landfall wants higher land density.",
            "Preserve basics for basic-search effects.",
            "Review owned fetch-style lands, sacrifice lands, and land-recursion utility lands first.",
        ]
    elif strategy_id == "voltron":
        basic_min = max(12, target_lands - 18)
        nonbasic_review = target_lands - basic_min
        priority_notes = [
            "Prioritize early untapped sources for reliable commander casting.",
            "Review utility lands only if they do not delay the commander.",
            "Protection/evasion lands are review candidates, not automatic insertions.",
        ]
    elif strategy_id == "spellslinger":
        basic_min = max(11, target_lands - 18)
        nonbasic_review = target_lands - basic_min
        priority_notes = [
            "Prioritize untapped colored sources for cheap spells and interaction.",
            "Spell-support utility lands should not crowd out color consistency.",
            "Tapped lands are previewed cautiously because double-spelling matters.",
        ]
    else:
        basic_min = max(13, target_lands - 19)
        nonbasic_review = target_lands - basic_min
        priority_notes = [
            "Start from owned fixing lands, then use basics to stabilize colors.",
            "Utility lands remain review-only and should support the main strategy.",
            "Tapped lands should be limited if the deck needs early setup.",
        ]

    return {
        "strategy_id": strategy_id,
        "display_name": mana_plan.get("display_name", ""),
        "land_insertion_mode": "preview_recommendations_only",
        "target_land_slots": target_lands,
        "recommended_land_band": band,
        "preview_basic_land_floor": basic_min,
        "preview_nonbasic_review_slots": nonbasic_review,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "outside_nonbasic_upgrades_allowed_only_if_user_allows": True,
        "preview_land_slot_guidance": {
            "basic_slots": {
                "preview_minimum": basic_min,
                "status": "assumed_available_not_collection_required",
                "note": mana_plan.get("basic_land_policy", "Basic lands are assumed available."),
            },
            "nonbasic_slots": {
                "preview_review_slots": nonbasic_review,
                "status": "collection_first_review_only",
                "priorities": mana_plan.get("nonbasic_priorities", []),
            },
        },
        "priority_notes": priority_notes,
        "land_insertion_boundaries": {
            "land_insertion_preview_enabled": True,
            "land_insertion_enabled": True,
            "land_insertion_mode": "preview_only_no_deck_write",
            "mana_base_generation_enabled": False,
            "final_land_list_generation_enabled": False,
            "final_deck_inclusion_enabled": False,
            "deck_generation_enabled": False,
            "full_100_card_draft_generation_enabled": False,
        },
    }


def build_land_insertion_preview_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)
    handoff = _load_json(HANDOFF_PREVIEW_PATH)
    shell_plan = _load_json(SHELL_PLAN_PATH)
    candidates = _load_json(CANDIDATE_PREVIEW_PATH)
    role_counts = _load_json(ROLE_COUNT_PLAN_PATH)
    mana_base = _load_json(MANA_PLAN_PATH)

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
    }

    previews = [_preview_land_slots(plan) for plan in mana_base.get("mana_base_plans", []) or []]

    return {
        "land_insertion_preview_version": "v1.4.18",
        "integration_mode": "land_insertion_preview",
        "land_insertion_preview_enabled": True,
        "land_insertion_enabled": True,
        "land_insertion_mode": "preview_only_no_deck_write",
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
        "final_land_list_generation_enabled": False,
        "final_deck_inclusion_enabled": False,
        "deck_generation_enabled": False,
        "full_100_card_draft_generation_enabled": False,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(previews),
        "land_insertion_previews": previews,
        "integration_contract": {
            "may_preview_land_slot_insertion": True,
            "may_write_lands_into_deck": False,
            "may_generate_finished_mana_base": False,
            "may_generate_final_land_list": False,
            "may_select_final_deck_cards": False,
            "may_make_final_deck_inclusion_decisions": False,
            "may_generate_full_deck": False,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "must_label_output_as_preview_only": True,
            "next_integration_step": "v1.4.19 — Full 100-Card Draft Preview",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.18 previews land slot insertion only. It does not write lands into a deck, generate a finished mana base, or create a final deck.",
            "next_safe_step": "v1.4.19 — Full 100-Card Draft Preview",
        },
    }


def build_land_insertion_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_land_insertion_preview_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Land Insertion Preview",
        "",
        "Strategy Knowledge can now preview land-slot insertion recommendations.",
        "",
        "### Boundary",
        "- This is a preview only.",
        "- This does not write lands into a deck.",
        "- This does not generate a finished mana base.",
        "- This does not make final deck inclusion decisions or generate a full deck.",
        "",
        "### Global Land Rules",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless outside upgrades are allowed.",
        "",
        "### Strategy Land Slot Previews",
    ]

    for preview in payload.get("land_insertion_previews", []):
        band = preview.get("recommended_land_band", {})
        lines.append("")
        lines.append(f"#### {preview.get('display_name')} (`{preview.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Target land slots: {preview.get('target_land_slots')} within {band.get('min')}–{band.get('max')} land band")
        lines.append(f"- Preview basic land floor: {preview.get('preview_basic_land_floor')}")
        lines.append(f"- Preview nonbasic review slots: {preview.get('preview_nonbasic_review_slots')}")
        lines.append("- Notes:")
        for note in preview.get("priority_notes", []):
            lines.append(f"  - {note}")

    return "\n".join(lines).rstrip()


def build_land_insertion_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_land_insertion_preview_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Land Insertion Preview Context",
        "",
        "Strategy Knowledge may preview land-slot insertion recommendations.",
        "",
        "Rules:",
        "- Treat land insertion as preview-only.",
        "- Do not write lands into the final deck in this stage.",
        "- Do not generate a finished mana base in this stage.",
        "- Do not generate a complete final deck list in this stage.",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless the user allows outside upgrades.",
    ]).rstrip()


def build_land_insertion_viewer_summary() -> str:
    payload = build_land_insertion_preview_payload({})
    lines = [
        "Land Insertion Preview",
        "======================",
        "",
        "Strategy Knowledge now previews land-slot insertion recommendations.",
        "",
        f"Land insertion previews available: {payload.get('checked_strategy_count')}",
        "Land insertion mode: preview only, no deck write",
        "Finished mana-base generation: disabled",
        "Final deck inclusion: disabled",
        "Deck generation: disabled",
        "Full 100-card draft generation: disabled",
        "",
        "Basic lands are assumed available. Nonbasic lands remain collection-first unless outside upgrades are allowed.",
    ]
    return "\n".join(lines).rstrip()


def write_land_insertion_preview() -> Dict[str, Any]:
    payload = build_land_insertion_preview_payload({})
    LAND_INSERTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAND_INSERTION_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LAND_INSERTION_SUMMARY_PATH.write_text(build_land_insertion_report_section({}) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("v1.4.18 - Land Insertion Preview")
    print("=" * 78)
    payload = write_land_insertion_preview()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Land insertion mode: {payload.get('land_insertion_mode')}")
    print(f"Land insertion previews available: {payload.get('checked_strategy_count')}")
    print(f"Mana-base generation enabled: {payload.get('mana_base_generation_enabled')}")
    print(f"Final land list generation enabled: {payload.get('final_land_list_generation_enabled')}")
    print(f"Final deck inclusion enabled: {payload.get('final_deck_inclusion_enabled')}")
    print(f"Preview written: {LAND_INSERTION_PATH}")
    print(f"Summary written: {LAND_INSERTION_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.19 — Full 100-Card Draft Preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
