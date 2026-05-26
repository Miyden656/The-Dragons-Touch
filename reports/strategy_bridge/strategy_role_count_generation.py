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
ROLE_COUNT_SUMMARY_PATH = STRATEGY_ROOT / "role_counts" / "STRATEGY_ROLE_COUNT_PLAN_SUMMARY_v1.4.16.md"


ROLE_COUNT_BANDS: Dict[str, Dict[str, Dict[str, int]]] = {
    "aristocrats": {
        "ramp_mana_development": {"min": 8, "target": 10, "max": 12},
        "card_draw_card_advantage": {"min": 8, "target": 10, "max": 12},
        "targeted_removal": {"min": 5, "target": 7, "max": 9},
        "board_wipes": {"min": 2, "target": 3, "max": 4},
        "strategy_enablers": {"min": 10, "target": 13, "max": 16},
        "strategy_payoffs": {"min": 8, "target": 10, "max": 12},
        "recursion": {"min": 5, "target": 7, "max": 9},
        "finishers_win_conditions": {"min": 3, "target": 4, "max": 6},
        "protection": {"min": 3, "target": 4, "max": 6},
        "lands": {"min": 35, "target": 37, "max": 38},
    },
    "tokens": {
        "ramp_mana_development": {"min": 8, "target": 10, "max": 12},
        "card_draw_card_advantage": {"min": 8, "target": 10, "max": 12},
        "targeted_removal": {"min": 5, "target": 7, "max": 9},
        "board_wipes": {"min": 2, "target": 3, "max": 4},
        "strategy_enablers": {"min": 10, "target": 13, "max": 16},
        "strategy_payoffs": {"min": 8, "target": 10, "max": 12},
        "finishers_win_conditions": {"min": 3, "target": 5, "max": 6},
        "protection": {"min": 3, "target": 5, "max": 6},
        "lands": {"min": 35, "target": 37, "max": 38},
    },
    "spellslinger": {
        "ramp_mana_development": {"min": 7, "target": 9, "max": 11},
        "card_draw_card_advantage": {"min": 10, "target": 13, "max": 16},
        "targeted_removal": {"min": 5, "target": 7, "max": 9},
        "board_wipes": {"min": 1, "target": 2, "max": 4},
        "strategy_enablers": {"min": 10, "target": 13, "max": 16},
        "strategy_payoffs": {"min": 8, "target": 10, "max": 12},
        "finishers_win_conditions": {"min": 3, "target": 4, "max": 6},
        "protection": {"min": 2, "target": 4, "max": 6},
        "lands": {"min": 34, "target": 36, "max": 37},
    },
    "landfall_lands_matter": {
        "ramp_mana_development": {"min": 10, "target": 13, "max": 16},
        "card_draw_card_advantage": {"min": 7, "target": 9, "max": 11},
        "targeted_removal": {"min": 4, "target": 6, "max": 8},
        "board_wipes": {"min": 1, "target": 2, "max": 4},
        "strategy_enablers": {"min": 8, "target": 11, "max": 14},
        "strategy_payoffs": {"min": 8, "target": 10, "max": 12},
        "mana_base_support": {"min": 8, "target": 11, "max": 14},
        "finishers_win_conditions": {"min": 3, "target": 4, "max": 6},
        "lands": {"min": 37, "target": 39, "max": 42},
    },
    "voltron": {
        "ramp_mana_development": {"min": 7, "target": 9, "max": 11},
        "card_draw_card_advantage": {"min": 7, "target": 9, "max": 11},
        "targeted_removal": {"min": 5, "target": 7, "max": 9},
        "board_wipes": {"min": 1, "target": 2, "max": 3},
        "strategy_enablers": {"min": 10, "target": 13, "max": 16},
        "strategy_payoffs": {"min": 5, "target": 7, "max": 9},
        "finishers_win_conditions": {"min": 2, "target": 3, "max": 5},
        "protection": {"min": 8, "target": 11, "max": 14},
        "lands": {"min": 34, "target": 36, "max": 38},
    },
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _build_role_count_plan(shell: Dict[str, Any], candidate_set: Dict[str, Any] | None = None) -> Dict[str, Any]:
    strategy_id = shell.get("strategy_id", "")
    bands = ROLE_COUNT_BANDS.get(strategy_id, {})
    candidate_set = candidate_set or {}

    return {
        "strategy_id": strategy_id,
        "display_name": shell.get("display_name", ""),
        "role_count_mode": "strategy_based_target_bands",
        "role_count_status": "generated_target_bands_not_final_deck_counts",
        "collection_first": True,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "candidate_count_available": candidate_set.get("candidate_count", 0),
        "target_role_bands": bands,
        "role_count_guidance": [
            "Use target bands to evaluate balance, not to force exact final counts.",
            "Treat overlapping cards as satisfying more than one role during review.",
            "Do not cut protected synergy pieces only because one broad role appears over target.",
            "Use commander intent, bracket, and philosophy to adjust bands in future patches.",
            "Lands are represented as a planning target only; mana-base generation and land insertion remain disabled.",
        ],
        "role_count_boundaries": {
            "role_count_generation_enabled": True,
            "role_count_generation_mode": "target_bands_only",
            "exact_card_selection_enabled": True,
            "exact_card_selection_mode": "preview_candidates_only",
            "final_deck_inclusion_enabled": False,
            "deck_generation_enabled": False,
            "mana_base_generation_enabled": False,
            "land_insertion_enabled": False,
            "full_100_card_draft_generation_enabled": False,
        },
    }


def build_strategy_role_count_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)
    handoff = _load_json(HANDOFF_PREVIEW_PATH)
    shell_plan = _load_json(SHELL_PLAN_PATH)
    candidates = _load_json(CANDIDATE_PREVIEW_PATH)

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
    }

    candidate_by_strategy = {
        item.get("strategy_id"): item
        for item in candidates.get("candidate_sets", []) or []
    }
    plans = [
        _build_role_count_plan(shell, candidate_by_strategy.get(shell.get("strategy_id", "")))
        for shell in shell_plan.get("shell_plans", []) or []
    ]

    return {
        "role_count_generation_version": "v1.4.16",
        "integration_mode": "strategy_based_role_count_generation",
        "strategy_role_count_generation_enabled": True,
        "role_count_generation_enabled": True,
        "role_count_generation_mode": "target_bands_only",
        "runtime_behavior_changed": True,
        "report_output_changed": True,
        "prompt_output_changed": True,
        "report_viewer_changed": True,
        "main_py_changed": False,
        "legacy_fallback_required": True,
        "active_runtime_replacement": False,
        "exact_card_selection_enabled": True,
        "exact_card_selection_mode": "preview_candidates_only",
        "final_deck_inclusion_enabled": False,
        "deck_generation_enabled": False,
        "mana_base_generation_enabled": False,
        "land_insertion_enabled": False,
        "shell_generation_enabled": True,
        "full_100_card_draft_generation_enabled": False,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(plans),
        "role_count_plans": plans,
        "integration_contract": {
            "may_generate_strategy_based_role_count_target_bands": True,
            "may_generate_final_role_counts": False,
            "may_select_final_deck_cards": False,
            "may_make_final_deck_inclusion_decisions": False,
            "may_generate_full_deck": False,
            "may_generate_mana_base": False,
            "may_insert_lands": False,
            "must_label_counts_as_target_bands": True,
            "must_keep_collection_first": True,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "next_integration_step": "v1.4.17 — Mana Base Planning",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.16 generates strategy-based role target bands only. It does not make final deck inclusions, generate a mana base, insert lands, or create a full deck.",
            "next_safe_step": "v1.4.17 — Mana Base Planning",
        },
    }


def build_strategy_role_count_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_role_count_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Strategy-Based Role Count Generation",
        "",
        "Strategy Knowledge can now generate strategy-based role target bands.",
        "",
        "### Boundary",
        "- These are target bands, not final deck counts.",
        "- This does not make final deck inclusion decisions.",
        "- This does not generate a final deck, mana base, land insertion, or full 100-card draft.",
        "- Overlapping cards may satisfy multiple roles during review.",
        "",
        "### Role Count Plans",
    ]

    for plan in payload.get("role_count_plans", []):
        lines.append("")
        lines.append(f"#### {plan.get('display_name')} (`{plan.get('strategy_id')}`)")
        lines.append("")
        for role, band in (plan.get("target_role_bands", {}) or {}).items():
            lines.append(f"- **{role}**: {band.get('min')}–{band.get('max')} cards; target {band.get('target')}")

    return "\n".join(lines).rstrip()


def build_strategy_role_count_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_role_count_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Strategy-Based Role Count Context",
        "",
        "Strategy Knowledge may generate target role bands for the recognized strategy.",
        "",
        "Rules:",
        "- Treat target role counts as planning bands, not final locked counts.",
        "- Do not force cuts only because a broad role is above target.",
        "- Overlapping cards may satisfy multiple roles.",
        "- Do not make final deck inclusion decisions in this stage.",
        "- Do not generate a mana base, insert lands, or produce a full 100-card draft in this stage.",
        "- Basic lands are assumed available; nonbasic lands remain collection-first unless upgrades are allowed.",
    ]).rstrip()


def build_strategy_role_count_viewer_summary() -> str:
    payload = build_strategy_role_count_payload({})
    lines = [
        "Strategy Role Count Generation",
        "==============================",
        "",
        "Strategy Knowledge now provides target role bands for planning.",
        "",
        f"Role count plans available: {payload.get('checked_strategy_count')}",
        "Role count mode: target bands only",
        "Final deck inclusion: disabled",
        "Deck generation: disabled",
        "Mana-base generation: disabled",
        "Land insertion: disabled",
        "Full 100-card draft generation: disabled",
        "",
        "Use these as planning bands, not final locked deck counts.",
    ]
    return "\n".join(lines).rstrip()


def write_strategy_role_count_preview() -> Dict[str, Any]:
    payload = build_strategy_role_count_payload({})
    ROLE_COUNT_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROLE_COUNT_PLAN_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    ROLE_COUNT_SUMMARY_PATH.write_text(build_strategy_role_count_report_section({}) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("v1.4.16 - Strategy-Based Role Count Generation")
    print("=" * 78)
    payload = write_strategy_role_count_preview()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Role count generation mode: {payload.get('role_count_generation_mode')}")
    print(f"Role count plans available: {payload.get('checked_strategy_count')}")
    print(f"Final deck inclusion enabled: {payload.get('final_deck_inclusion_enabled')}")
    print(f"Deck generation enabled: {payload.get('deck_generation_enabled')}")
    print(f"Mana-base generation enabled: {payload.get('mana_base_generation_enabled')}")
    print(f"Plan written: {ROLE_COUNT_PLAN_PATH}")
    print(f"Summary written: {ROLE_COUNT_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.17 — Mana Base Planning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
