from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

RUNTIME_CONTRACT_PATH = STRATEGY_ROOT / "runtime" / "strategy_brain_runtime_contract_v1.4.9.json"
SCORING_PREVIEW_PATH = STRATEGY_ROOT / "scoring_previews" / "strategy_scoring_integration_preview_v1.4.10.json"
ROLE_MAPPING_PATH = STRATEGY_ROOT / "role_mapping" / "strategy_role_bucket_mapping_v1.4.11.json"
CUT_PROTECT_PATH = STRATEGY_ROOT / "cut_protect_replacement" / "strategy_cut_protect_replacement_v1.4.12.json"
HANDOFF_PREVIEW_PATH = STRATEGY_ROOT / "report_viewer_handoff" / "strategy_report_viewer_handoff_preview_v1.4.13.json"
SHELL_PLAN_PATH = STRATEGY_ROOT / "shell_planning" / "strategy_shell_plan_v1.4.14.json"

CANDIDATE_PLAN_PATH = STRATEGY_ROOT / "card_candidates" / "exact_card_candidate_preview_v1.4.15.json"
CANDIDATE_SUMMARY_PATH = STRATEGY_ROOT / "card_candidates" / "EXACT_CARD_CANDIDATE_PREVIEW_SUMMARY_v1.4.15.md"


SAMPLE_CARD_POOL: List[Dict[str, Any]] = [
    {
        "card_name": "Viscera Seer",
        "owned": True,
        "card_tags": ["free_sacrifice_outlet", "sacrifice_outlet", "strategy_enabler", "creature"],
        "candidate_strategies": ["aristocrats"],
        "candidate_roles": ["strategy_enablers"],
    },
    {
        "card_name": "Blood Artist",
        "owned": True,
        "card_tags": ["death_trigger_payoff", "drain_payoff", "strategy_payoff", "creature"],
        "candidate_strategies": ["aristocrats"],
        "candidate_roles": ["strategy_payoffs", "finishers_win_conditions"],
    },
    {
        "card_name": "Secure the Wastes",
        "owned": True,
        "card_tags": ["token_engine", "creature_tokens", "instant", "strategy_enabler"],
        "candidate_strategies": ["tokens"],
        "candidate_roles": ["strategy_enablers"],
    },
    {
        "card_name": "Impact Tremors",
        "owned": True,
        "card_tags": ["token_payoff", "creature_entry_payoff", "strategy_payoff"],
        "candidate_strategies": ["tokens"],
        "candidate_roles": ["strategy_payoffs", "finishers_win_conditions"],
    },
    {
        "card_name": "Young Pyromancer",
        "owned": True,
        "card_tags": ["spell_payoff", "instant", "sorcery", "token_engine", "strategy_payoff"],
        "candidate_strategies": ["spellslinger"],
        "candidate_roles": ["strategy_payoffs", "strategy_enablers"],
    },
    {
        "card_name": "Solve the Equation",
        "owned": True,
        "card_tags": ["instant", "sorcery", "spell_support", "card_selection", "strategy_enabler"],
        "candidate_strategies": ["spellslinger"],
        "candidate_roles": ["card_draw_card_advantage", "strategy_enablers"],
    },
    {
        "card_name": "Cultivate",
        "owned": True,
        "card_tags": ["ramp", "land_search", "ramp_mana_development", "land_engine"],
        "candidate_strategies": ["landfall_lands_matter"],
        "candidate_roles": ["ramp_mana_development", "mana_base_support"],
    },
    {
        "card_name": "Evolving Wilds",
        "owned": True,
        "card_tags": ["fetchland", "landfall", "mana_base_support", "land_entry"],
        "candidate_strategies": ["landfall_lands_matter"],
        "candidate_roles": ["mana_base_support", "strategy_enablers"],
    },
    {
        "card_name": "Swiftfoot Boots",
        "owned": True,
        "card_tags": ["commander_protection", "protection", "equipment", "haste"],
        "candidate_strategies": ["voltron"],
        "candidate_roles": ["protection", "strategy_enablers"],
    },
    {
        "card_name": "All That Glitters",
        "owned": True,
        "card_tags": ["aura", "equipment_payoff", "voltron", "commander_damage_support"],
        "candidate_strategies": ["voltron"],
        "candidate_roles": ["strategy_payoffs", "finishers_win_conditions"],
    },
    {
        "card_name": "Generic Seven-Mana Dragon",
        "owned": True,
        "card_tags": ["generic_goodstuff", "high_mv", "off_plan", "low_synergy"],
        "candidate_strategies": [],
        "candidate_roles": [],
    },
]


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalize(values: Any) -> Set[str]:
    out: Set[str] = set()
    if isinstance(values, str):
        lowered = values.lower()
        out.add(lowered)
        out.update(part for part in lowered.replace("-", "_").replace("/", "_").split("_") if part)
        out.update(part for part in lowered.replace("-", " ").replace("/", " ").split() if part)
    elif isinstance(values, list):
        for value in values:
            out.update(_normalize(value))
    elif isinstance(values, dict):
        for value in values.values():
            out.update(_normalize(value))
    return out


def _candidate_for_strategy(card: Dict[str, Any], shell: Dict[str, Any]) -> Dict[str, Any]:
    strategy_id = shell.get("strategy_id", "")
    owned = card.get("owned") is True
    intended = strategy_id in (card.get("candidate_strategies", []) or [])

    role_tags = set(card.get("candidate_roles", []) or [])
    shell_roles = set(shell.get("primary_role_buckets", []) or []) | set(shell.get("secondary_role_buckets", []) or [])
    role_hits = sorted(role_tags & shell_roles)

    shell_specific = _normalize(shell.get("strategy_specific_roles", []) or [])
    card_tags = _normalize(card.get("card_tags", []) or [])
    tag_hits = sorted(card_tags & shell_specific)

    off_plan = bool(card_tags & {"off_plan", "low_synergy", "wrong_shell"})
    candidate_score = 0
    if owned:
        candidate_score += 2
    if intended:
        candidate_score += 4
    candidate_score += len(role_hits) * 2
    candidate_score += len(tag_hits)
    if off_plan:
        candidate_score -= 5

    preview_status = "candidate" if candidate_score > 0 and not off_plan else "not_recommended_preview"
    if off_plan:
        reason = "Card carries off-plan / low-synergy pressure and should not be promoted as a candidate for this strategy."
    elif preview_status == "candidate":
        reason = "Owned card matches strategy and role tags; review as an exact-card candidate, not a final inclusion."
    else:
        reason = "No strong strategy or role match found in preview tags."

    return {
        "card_name": card.get("card_name", ""),
        "owned": owned,
        "candidate_status": preview_status,
        "candidate_score": candidate_score,
        "candidate_roles": sorted(role_hits),
        "strategy_tag_hits": tag_hits,
        "off_plan_pressure": off_plan,
        "reason": reason,
        "final_inclusion": False,
    }


def _build_candidates_for_shell(shell: Dict[str, Any]) -> Dict[str, Any]:
    evaluated = [_candidate_for_strategy(card, shell) for card in SAMPLE_CARD_POOL]
    candidates = [item for item in evaluated if item.get("candidate_status") == "candidate"]
    candidates.sort(key=lambda item: (item.get("candidate_score", 0), item.get("card_name", "")), reverse=True)

    return {
        "strategy_id": shell.get("strategy_id", ""),
        "display_name": shell.get("display_name", ""),
        "candidate_selection_mode": "exact_card_candidates_preview_only",
        "owned_cards_preferred": True,
        "outside_upgrades_allowed": False,
        "candidate_count": len(candidates),
        "candidate_cards": candidates,
        "not_recommended_preview": [item for item in evaluated if item.get("candidate_status") != "candidate"],
        "candidate_boundaries": {
            "exact_card_candidate_preview_enabled": True,
            "final_deck_inclusion_enabled": False,
            "deck_generation_enabled": False,
            "role_count_generation_enabled": False,
            "mana_base_generation_enabled": False,
            "land_insertion_enabled": False,
            "full_100_card_draft_generation_enabled": False,
        },
    }


def build_exact_card_candidate_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)
    handoff = _load_json(HANDOFF_PREVIEW_PATH)
    shell_plan = _load_json(SHELL_PLAN_PATH)

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
    }

    shells = shell_plan.get("shell_plans", []) or []
    candidate_sets = [_build_candidates_for_shell(shell) for shell in shells]
    total_candidates = sum(item.get("candidate_count", 0) for item in candidate_sets)

    return {
        "candidate_preview_version": "v1.4.15",
        "integration_mode": "exact_card_candidate_selection_preview",
        "exact_card_candidate_preview_enabled": True,
        "exact_card_selection_enabled": True,
        "exact_card_selection_mode": "preview_candidates_only",
        "runtime_behavior_changed": True,
        "report_output_changed": True,
        "prompt_output_changed": True,
        "report_viewer_changed": True,
        "main_py_changed": False,
        "legacy_fallback_required": True,
        "active_runtime_replacement": False,
        "deck_generation_enabled": False,
        "final_deck_inclusion_enabled": False,
        "role_count_generation_enabled": False,
        "mana_base_generation_enabled": False,
        "land_insertion_enabled": False,
        "shell_generation_enabled": True,
        "full_100_card_draft_generation_enabled": False,
        "gate_checks": gate_checks,
        "checked_strategy_count": len(candidate_sets),
        "total_candidate_count": total_candidates,
        "candidate_sets": candidate_sets,
        "integration_contract": {
            "may_nominate_exact_card_candidates": True,
            "may_select_final_deck_cards": False,
            "may_make_final_deck_inclusion_decisions": False,
            "may_generate_full_deck": False,
            "may_generate_final_role_counts": False,
            "may_generate_mana_base": False,
            "may_insert_lands": False,
            "must_label_candidates_as_review_only": True,
            "must_keep_collection_first": True,
            "must_not_promote_off_plan_cards": True,
            "next_integration_step": "v1.4.16 — Strategy-Based Role Count Generation",
        },
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.15 enables exact-card candidate nomination only. Candidates are review-only and are not final deck inclusions.",
            "next_safe_step": "v1.4.16 — Strategy-Based Role Count Generation",
        },
    }


def build_exact_card_candidate_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_exact_card_candidate_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Exact Card Candidate Selection Preview",
        "",
        "Strategy Knowledge can now nominate exact-card candidates for review.",
        "",
        "### Boundary",
        "- These are candidates, not final deck inclusions.",
        "- This does not generate a deck.",
        "- This does not generate final role counts, a mana base, land insertion, or a full 100-card draft.",
        "- Off-plan / low-synergy cards should not be promoted just because they are generically strong.",
        "",
        "### Candidate Sets",
    ]

    for candidate_set in payload.get("candidate_sets", []):
        lines.append("")
        lines.append(f"#### {candidate_set.get('display_name')} (`{candidate_set.get('strategy_id')}`)")
        lines.append("")
        candidates = candidate_set.get("candidate_cards", [])[:8]
        if not candidates:
            lines.append("- No exact-card candidates nominated in this preview.")
            continue
        for card in candidates:
            roles = ", ".join(card.get("candidate_roles", []) or ["role review needed"])
            lines.append(f"- **{card.get('card_name')}** — candidate roles: {roles}; score: {card.get('candidate_score')}; final inclusion: No")

    return "\n".join(lines).rstrip()


def build_exact_card_candidate_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_exact_card_candidate_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    return "\n".join([
        "## Exact Card Candidate Selection Preview Context",
        "",
        "Strategy Knowledge may nominate exact-card candidates for review.",
        "",
        "Rules:",
        "- Treat candidates as review-only suggestions.",
        "- Do not treat candidates as final deck inclusions.",
        "- Prefer owned cards first.",
        "- Do not promote off-plan cards just because they are generically strong.",
        "- Do not generate a full deck list from candidate nominations.",
        "- Do not generate final role counts, mana bases, land insertion, or full 100-card drafts in this stage.",
    ]).rstrip()


def build_exact_card_candidate_viewer_summary() -> str:
    payload = build_exact_card_candidate_payload({})
    lines = [
        "Exact Card Candidate Preview",
        "============================",
        "",
        "Strategy Knowledge can now nominate exact-card candidates for review.",
        "",
        f"Candidate sets available: {payload.get('checked_strategy_count')}",
        f"Total candidates nominated: {payload.get('total_candidate_count')}",
        "Final deck inclusion: disabled",
        "Deck generation: disabled",
        "Mana-base generation: disabled",
        "Land insertion: disabled",
        "Full 100-card draft generation: disabled",
        "",
        "Use these as review candidates, not as locked deck inclusions.",
    ]
    return "\n".join(lines).rstrip()


def write_exact_card_candidate_preview() -> Dict[str, Any]:
    payload = build_exact_card_candidate_payload({})
    CANDIDATE_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_PLAN_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    CANDIDATE_SUMMARY_PATH.write_text(build_exact_card_candidate_report_section({}) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("v1.4.15 - Exact Card Candidate Selection Preview")
    print("=" * 78)
    payload = write_exact_card_candidate_preview()
    print(f"Integration mode: {payload.get('integration_mode')}")
    print(f"Exact card selection mode: {payload.get('exact_card_selection_mode')}")
    print(f"Candidate sets available: {payload.get('checked_strategy_count')}")
    print(f"Total candidates nominated: {payload.get('total_candidate_count')}")
    print(f"Final deck inclusion enabled: {payload.get('final_deck_inclusion_enabled')}")
    print(f"Deck generation enabled: {payload.get('deck_generation_enabled')}")
    print(f"Preview written: {CANDIDATE_PLAN_PATH}")
    print(f"Summary written: {CANDIDATE_SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    if payload.get("total_candidate_count", 0) < 10:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.16 — Strategy-Based Role Count Generation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
