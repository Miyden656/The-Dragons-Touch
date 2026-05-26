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
MANA_SUMMARY_PATH = STRATEGY_ROOT / "mana_base" / "MANA_BASE_PLAN_SUMMARY_v1.4.17.md"


MANA_BASE_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "aristocrats": {
        "land_target_adjustment": "normal",
        "recommended_land_band": {"min": 35, "target": 37, "max": 38},
        "basic_land_policy": "Assume needed basics are available; use them to stabilize colors after owned nonbasic review.",
        "nonbasic_priorities": [
            "untapped duals/fixing lands from collection",
            "sacrifice-friendly utility lands if already owned",
            "graveyard/recursion utility lands only if color consistency remains stable",
        ],
        "mana_notes": [
            "Do not overload colorless utility lands if early sacrifice outlets and payoffs have colored costs.",
            "Prefer early untapped sources for engine setup.",
        ],
    },
    "tokens": {
        "land_target_adjustment": "normal",
        "recommended_land_band": {"min": 35, "target": 37, "max": 38},
        "basic_land_policy": "Assume needed basics are available; use basics to support stable early token production.",
        "nonbasic_priorities": [
            "owned fixing lands that enter untapped early",
            "utility lands that produce tokens only if they do not weaken color access",
            "go-wide support lands if already owned and on-plan",
        ],
        "mana_notes": [
            "Token decks often need early colored mana to start building board presence.",
            "Avoid too many tapped lands if the strategy needs to curve out.",
        ],
    },
    "spellslinger": {
        "land_target_adjustment": "slightly_lower_if_curve_low",
        "recommended_land_band": {"min": 34, "target": 36, "max": 37},
        "basic_land_policy": "Assume needed basics are available; use basics to keep colors stable after owned spell-support lands.",
        "nonbasic_priorities": [
            "owned untapped fixing lands",
            "spell-support lands only if color consistency remains strong",
            "utility lands that copy/rebuy spells only when not slowing early interaction",
        ],
        "mana_notes": [
            "Spellslinger decks need reliable colored mana for cheap interaction and draw.",
            "Tapped lands are more punishing when the deck wants to double-spell early.",
        ],
    },
    "landfall_lands_matter": {
        "land_target_adjustment": "higher_land_density",
        "recommended_land_band": {"min": 37, "target": 39, "max": 42},
        "basic_land_policy": "Assume needed basics are available; basics are especially important because many landfall enablers search for basic lands.",
        "nonbasic_priorities": [
            "owned fetch-style lands and evolving/wilds effects",
            "lands that enter and sacrifice or recur",
            "utility lands that produce landfall value without damaging color consistency",
        ],
        "mana_notes": [
            "Higher land count is normal for landfall and should not be treated as a problem by itself.",
            "Nonbasic lands are valuable, but basics remain important for search effects.",
        ],
    },
    "voltron": {
        "land_target_adjustment": "normal_to_slightly_lower_if_curve_low",
        "recommended_land_band": {"min": 34, "target": 36, "max": 38},
        "basic_land_policy": "Assume needed basics are available; use basics to support reliable commander casting.",
        "nonbasic_priorities": [
            "owned untapped fixing lands",
            "utility lands that protect or give evasion only if colors remain stable",
            "equipment-support lands if already owned and not too slow",
        ],
        "mana_notes": [
            "Voltron decks need reliable early commander mana.",
            "Too many tapped or colorless utility lands can delay the commander and weaken the plan.",
        ],
    },
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _role_land_band(role_plan: Dict[str, Any]) -> Dict[str, int]:
    bands = role_plan.get("target_role_bands", {}) or {}
    land_band = bands.get("lands", {})
    return {
        "min": int(land_band.get("min", 35)),
        "target": int(land_band.get("target", 37)),
        "max": int(land_band.get("max", 38)),
    }


def _build_mana_plan(role_plan: Dict[str, Any]) -> Dict[str, Any]:
    strategy_id = role_plan.get("strategy_id", "")
    guidance = MANA_BASE_GUIDANCE.get(strategy_id, {})
    role_band = _role_land_band(role_plan)
    guidance_band = guidance.get("recommended_land_band", role_band)

    return {
        "strategy_id": strategy_id,
        "display_name": role_plan.get("display_name", ""),
        "mana_base_plan_mode": "planning_guidance_only",
        "recommended_land_band": guidance_band,
        "role_count_land_band": role_band,
        "basic_lands_assumed_available": True,
        "basic_land_policy": guidance.get(
            "basic_land_policy",
            "Assume needed basics are available; use them to stabilize the mana base after owned nonbasic review.",
        ),
        "nonbasic_lands_collection_first": True,
        "outside_nonbasic_upgrades_allowed_only_if_user_allows": True,
        "nonbasic_priorities": guidance.get("nonbasic_priorities", [
            "owned fixing lands first",
            "owned utility lands only when they support the plan",
            "outside upgrades only if the user allows them",
        ]),
        "land_target_adjustment": guidance.get("land_target_adjustment", "normal"),
        "mana_notes": guidance.get("mana_notes", []),
        "planning_guidance": [
            "Use this as a mana-base plan, not a final land list.",
            "Basic lands are assumed available and do not need to be counted from the collection.",
            "Nonbasic lands remain collection-first unless outside upgrades are explicitly allowed.",
            "Do not insert lands in this stage.",
            "Do not generate a finished mana base in this stage.",
        ],
        "mana_base_boundaries": {
            "mana_base_planning_enabled": True,
            "mana_base_generation_enabled": False,
            "land_insertion_enabled": False,
            "final_deck_inclusion_enabled": False,
            "deck_generation_enabled": False,
            "full_100_card_draft_generation_enabled": False,
        },
    }


def build_mana_base_planning_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)
    handoff = _load_json(HANDOFF_PREVIEW_PATH)
    shell_plan = _load_json(SHELL_PLAN_PATH)
    candidates = _load_json(CANDIDATE_PREVIEW_PATH)
    role_counts = _load_json(ROLE_COUNT_PLAN_PATH)

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
    }

    plans = [_build_mana_plan(plan) for plan in role_counts.get("role_count_plans", []) or []]

    return {
        "mana_base_planning_version": "v1.4.17",
        "integration_mode": "mana_base_planning",
        "mana_base_planning_enabled": True,
        "mana_base_planning_mode": "planning_guidance_only",
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
        "mana_base_generation_enabled": False,
        "land_insertion_enabled": False,
        "final_deck_inclusion_enabled": False,
        "deck_generation_enabled": False,
        "full_100_card_draft_generation_enabled": False,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(plans),
        "mana_base_plans": plans,
        "integration_contract": {
            "may_generate_mana_base_planning_guidance": True,
            "may_generate_finished_mana_base": False,
            "may_insert_lands": False,
            "may_select_final_deck_cards": False,
            "may_make_final_deck_inclusion_decisions": False,
            "may_generate_full_deck": False,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "must_label_output_as_planning_guidance": True,
            "next_integration_step": "v1.4.18 — Land Insertion Preview",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.17 enables mana-base planning guidance only. It does not generate a finished mana base, insert lands, or create a deck.",
            "next_safe_step": "v1.4.18 — Land Insertion Preview",
        },
    }


def build_mana_base_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_mana_base_planning_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Mana Base Planning",
        "",
        "Strategy Knowledge can now provide mana-base planning guidance.",
        "",
        "### Boundary",
        "- This is mana-base planning guidance only.",
        "- This does not generate a finished mana base.",
        "- This does not insert lands.",
        "- This does not make final deck inclusion decisions or generate a full deck.",
        "",
        "### Global Land Rules",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless outside upgrades are allowed.",
        "",
        "### Strategy Mana Plans",
    ]

    for plan in payload.get("mana_base_plans", []):
        band = plan.get("recommended_land_band", {})
        lines.append("")
        lines.append(f"#### {plan.get('display_name')} (`{plan.get('strategy_id')}`)")
        lines.append("")
        lines.append(f"- Recommended land band: {band.get('min')}–{band.get('max')} lands; target {band.get('target')}")
        lines.append(f"- Basic land policy: {plan.get('basic_land_policy')}")
        lines.append("- Nonbasic priorities:")
        for priority in plan.get("nonbasic_priorities", []):
            lines.append(f"  - {priority}")
        notes = plan.get("mana_notes", [])
        if notes:
            lines.append("- Mana notes:")
            for note in notes:
                lines.append(f"  - {note}")

    return "\n".join(lines).rstrip()


def build_mana_base_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_mana_base_planning_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Mana Base Planning Context",
        "",
        "Strategy Knowledge may provide mana-base planning guidance.",
        "",
        "Rules:",
        "- Treat mana guidance as planning guidance, not a finished mana base.",
        "- Do not insert lands in this stage.",
        "- Do not generate a complete final deck list in this stage.",
        "- Basic lands are assumed available.",
        "- Nonbasic lands remain collection-first unless the user allows outside upgrades.",
        "- Use strategy-specific land-count bands as guidance only.",
    ]).rstrip()


def build_mana_base_viewer_summary() -> str:
    payload = build_mana_base_planning_payload({})
    lines = [
        "Mana Base Planning",
        "==================",
        "",
        "Strategy Knowledge now provides mana-base planning guidance.",
        "",
        f"Mana plans available: {payload.get('checked_strategy_count')}",
        "Mana-base generation: disabled",
        "Land insertion: disabled",
        "Final deck inclusion: disabled",
        "Deck generation: disabled",
        "Full 100-card draft generation: disabled",
        "",
        "Basic lands are assumed available. Nonbasic lands remain collection-first unless outside upgrades are allowed.",
    ]
    return "\n".join(lines).rstrip()


def write_mana_base_planning_preview() -> Dict[str, Any]:
    payload = build_mana_base_planning_payload({})
    MANA_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANA_PLAN_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MANA_SUMMARY_PATH.write_text(build_mana_base_report_section({}) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("v1.4.17 - Mana Base Planning")
    print("=" * 78)
    payload = write_mana_base_planning_preview()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Mana-base planning mode: {payload.get('mana_base_planning_mode')}")
    print(f"Mana plans available: {payload.get('checked_strategy_count')}")
    print(f"Mana-base generation enabled: {payload.get('mana_base_generation_enabled')}")
    print(f"Land insertion enabled: {payload.get('land_insertion_enabled')}")
    print(f"Final deck inclusion enabled: {payload.get('final_deck_inclusion_enabled')}")
    print(f"Plan written: {MANA_PLAN_PATH}")
    print(f"Summary written: {MANA_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count", 0) < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.18 — Land Insertion Preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
