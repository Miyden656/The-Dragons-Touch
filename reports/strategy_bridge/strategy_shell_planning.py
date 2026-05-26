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
SHELL_SUMMARY_PATH = STRATEGY_ROOT / "shell_planning" / "STRATEGY_SHELL_PLAN_SUMMARY_v1.4.14.md"


DEFAULT_ROLE_BANDS: Dict[str, Dict[str, str]] = {
    "aristocrats": {
        "strategy_enablers": "10-16 sacrifice outlets, fodder engines, and repeatable death-enablers",
        "strategy_payoffs": "8-12 death triggers, drain payoffs, and sacrifice rewards",
        "recursion": "5-9 recursion pieces that rebuy creatures or engines",
        "card_draw_card_advantage": "8-12 draw/value pieces, preferably tied to death or sacrifice",
        "finishers_win_conditions": "3-6 finishers that convert death loops or wide boards into wins",
        "protection": "3-6 ways to protect engine pieces or recover from wipes",
    },
    "tokens": {
        "strategy_enablers": "10-16 repeatable token makers and go-wide engines",
        "strategy_payoffs": "8-12 anthem, drain, convoke, or attack-scaling payoffs",
        "card_draw_card_advantage": "8-12 draw/value pieces that reward creature count or tokens",
        "finishers_win_conditions": "3-6 overrun, aristocrat, impact-damage, or mass-pump finishers",
        "protection": "3-6 protection or rebuild tools for board wipes",
    },
    "spellslinger": {
        "strategy_enablers": "10-16 cheap instants/sorceries, cost reducers, copy engines, or spell-density enablers",
        "strategy_payoffs": "8-12 magecraft, storm-like, copy, token, or damage payoffs",
        "card_draw_card_advantage": "10-16 draw/selection pieces to keep spells flowing",
        "targeted_removal": "5-9 efficient interaction spells that also support spell count",
        "finishers_win_conditions": "3-6 spell-copy, storm, X-spell, or spell-damage finishers",
        "protection": "2-5 protection/countermagic pieces depending on bracket",
    },
    "landfall_lands_matter": {
        "ramp_mana_development": "10-16 ramp, extra land drops, land search, and land recursion pieces",
        "strategy_enablers": "8-14 landfall triggers, land-recursion engines, and land-entry enablers",
        "strategy_payoffs": "8-12 landfall or lands-matter payoff cards",
        "mana_base_support": "8-14 lands/nonlands that support land entries, fixing, or utility",
        "card_draw_card_advantage": "7-11 draw/value pieces tied to lands or ramp",
        "finishers_win_conditions": "3-6 landfall finishers, big mana closers, or token-overrun wins",
    },
    "voltron": {
        "strategy_enablers": "10-16 equipment, auras, evasion, power boosts, or commander-damage support",
        "strategy_payoffs": "5-9 cards that reward suiting up, attacking alone, or commander combat",
        "protection": "8-14 protection, recursion, hexproof, indestructible, or anti-removal tools",
        "targeted_removal": "5-9 cheap interaction pieces to clear blockers or stop removal",
        "card_draw_card_advantage": "7-11 draw/value pieces tied to combat, equipment, or commander connection",
        "finishers_win_conditions": "2-5 commander-damage closers, extra combat, or lethal pump lines",
    },
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _profile_to_shell(profile: Dict[str, Any]) -> Dict[str, Any]:
    strategy_id = profile.get("strategy_id", "")
    role_bands = DEFAULT_ROLE_BANDS.get(strategy_id, {})
    return {
        "strategy_id": strategy_id,
        "display_name": profile.get("display_name", ""),
        "shell_plan_type": "rough_strategy_shell",
        "collection_first": True,
        "basic_lands_assumed_available": True,
        "nonbasic_lands_collection_first": True,
        "outside_upgrades_allowed_only_if_user_allows": True,
        "primary_role_buckets": profile.get("primary_role_buckets", []) or [],
        "secondary_role_buckets": profile.get("secondary_role_buckets", []) or [],
        "strategy_specific_roles": profile.get("strategy_specific_roles", []) or [],
        "rough_role_bands": role_bands,
        "build_from_collection_guidance": [
            "Start by filling commander-critical enablers and payoffs from owned cards.",
            "Prefer owned cards that satisfy multiple role buckets.",
            "Protect weak-looking cards if they are engine-critical for the selected strategy.",
            "Treat generically powerful off-plan cards as replaceable before cutting high-synergy pieces.",
            "Keep nonbasic lands collection-first unless outside upgrades are explicitly allowed.",
            "Assume basic lands are available during planning; do not require scanned basic land counts.",
        ],
        "shell_boundaries": {
            "rough_shell_guidance_enabled": True,
            "role_count_generation_enabled": False,
            "exact_card_selection_enabled": False,
            "final_deck_inclusion_enabled": False,
            "mana_base_generation_enabled": False,
            "land_insertion_enabled": False,
            "full_100_card_draft_generation_enabled": False,
        },
    }


def build_strategy_shell_plan_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)
    handoff = _load_json(HANDOFF_PREVIEW_PATH)

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
    }

    profiles = role_mapping.get("strategy_role_profiles", []) or []
    shell_plans = [_profile_to_shell(profile) for profile in profiles]

    return {
        "shell_planning_version": "v1.4.14",
        "integration_mode": "build_from_collection_strategy_shell_planning",
        "strategy_shell_planning_enabled": True,
        "rough_shell_guidance_enabled": True,
        "shell_generation_enabled": True,
        "shell_generation_mode": "rough_strategy_shell_planning_only",
        "runtime_behavior_changed": True,
        "report_output_changed": True,
        "prompt_output_changed": True,
        "report_viewer_changed": True,
        "main_py_changed": False,
        "legacy_fallback_required": True,
        "active_runtime_replacement": False,
        "deck_generation_enabled": False,
        "exact_card_selection_enabled": False,
        "final_deck_inclusion_enabled": False,
        "role_count_generation_enabled": False,
        "mana_base_generation_enabled": False,
        "land_insertion_enabled": False,
        "full_100_card_draft_generation_enabled": False,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(shell_plans),
        "shell_plans": shell_plans,
        "integration_contract": {
            "may_generate_rough_strategy_shell_guidance": True,
            "may_generate_final_role_counts": False,
            "may_select_exact_cards": False,
            "may_make_final_deck_inclusion_decisions": False,
            "may_generate_mana_base": False,
            "may_insert_lands": False,
            "may_generate_full_100_card_draft": False,
            "must_keep_collection_first": True,
            "must_assume_basic_lands_available": True,
            "must_keep_nonbasic_lands_collection_first_unless_upgrades_allowed": True,
            "next_integration_step": "v1.4.15 — Exact Card Candidate Selection Preview",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.14 enables rough strategy shell planning only. It does not select exact cards, make final inclusions, generate a mana base, insert lands, or create a full deck.",
            "next_safe_step": "v1.4.15 — Exact Card Candidate Selection Preview",
        },
    }


def build_strategy_shell_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_shell_plan_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Build From Collection Strategy Shell Planning",
        "",
        "Strategy Knowledge is now producing rough shell-planning guidance for Build From Collection.",
        "",
        "### Boundary",
        "- This is rough shell guidance only.",
        "- It does not select exact cards.",
        "- It does not make final deck inclusion decisions.",
        "- It does not generate role counts, a mana base, land insertion, or a full 100-card draft.",
        "",
        "### Collection-First Rules",
        "- Prefer owned cards first.",
        "- Assume basic lands are available.",
        "- Keep nonbasic lands collection-first unless outside upgrades are allowed.",
        "",
        "### Strategy Shell Plans",
    ]

    for shell in payload.get("shell_plans", []):
        lines.append("")
        lines.append(f"#### {shell.get('display_name')} (`{shell.get('strategy_id')}`)")
        lines.append("")
        role_bands = shell.get("rough_role_bands", {})
        for role, guidance in role_bands.items():
            lines.append(f"- **{role}**: {guidance}")

    return "\n".join(lines).rstrip()


def build_strategy_shell_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_shell_plan_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Build From Collection Strategy Shell Planning Context",
        "",
        "Use Strategy Knowledge to provide rough shell-planning guidance.",
        "",
        "Allowed in this stage:",
        "- identify important strategy role buckets",
        "- describe rough density bands",
        "- explain collection-first role priorities",
        "- protect synergy cards from being mistaken for bad cards",
        "",
        "Not allowed in this stage:",
        "- exact card selection",
        "- final deck inclusion decisions",
        "- final role-count generation",
        "- mana-base generation",
        "- land insertion",
        "- full 100-card draft generation",
        "",
        "Basic lands are assumed available. Nonbasic lands remain collection-first unless outside upgrades are allowed.",
    ]
    return "\n".join(lines).rstrip()


def build_strategy_shell_viewer_summary() -> str:
    payload = build_strategy_shell_plan_payload({})
    lines = [
        "Strategy Shell Planning",
        "=======================",
        "",
        "Strategy Knowledge now provides rough Build From Collection shell guidance.",
        "",
        f"Shell plans available: {payload.get('checked_strategy_count')}",
        "Exact-card selection: disabled",
        "Final deck inclusion: disabled",
        "Mana-base generation: disabled",
        "Land insertion: disabled",
        "Full 100-card draft generation: disabled",
        "",
        "Use this as role-density guidance, not as a finished deck list.",
    ]
    return "\n".join(lines).rstrip()


def write_strategy_shell_plan_preview() -> Dict[str, Any]:
    payload = build_strategy_shell_plan_payload({})
    SHELL_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SHELL_PLAN_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    SHELL_SUMMARY_PATH.write_text(build_strategy_shell_report_section({}) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("v1.4.14 - Build From Collection Strategy Shell Planning")
    print("=" * 78)
    payload = write_strategy_shell_plan_preview()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Shell planning enabled: {payload.get('strategy_shell_planning_enabled')}")
    print(f"Shell generation mode: {payload.get('shell_generation_mode')}")
    print(f"Shell plans available: {payload.get('checked_strategy_count')}")
    print(f"Exact card selection enabled: {payload.get('exact_card_selection_enabled')}")
    print(f"Final deck inclusion enabled: {payload.get('final_deck_inclusion_enabled')}")
    print(f"Plan written: {SHELL_PLAN_PATH}")
    print(f"Summary written: {SHELL_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("checked_strategy_count") < 5:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.15 — Exact Card Candidate Selection Preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
