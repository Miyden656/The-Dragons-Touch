from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from reports.strategy_bridge.strategy_v1_4_regression_lock_candidate import build_v1_4_regression_report_section, build_v1_4_regression_prompt_block, build_v1_4_regression_viewer_summary  # v1.4.27 full regression
from reports.strategy_bridge.land_deck_write_integration import build_land_deck_write_report_section, build_land_deck_write_prompt_block, build_land_deck_write_viewer_summary  # v1.4.24 land deck-write
from reports.strategy_bridge.finished_mana_base_generation import build_finished_mana_base_report_section, build_finished_mana_base_prompt_block, build_finished_mana_base_viewer_summary  # v1.4.23 finished mana base
from reports.strategy_bridge.full_100_card_draft_preview import build_full_100_card_draft_report_section, build_full_100_card_draft_prompt_block, build_full_100_card_draft_viewer_summary  # v1.4.19 full 100-card draft preview
from reports.strategy_bridge.exact_card_candidate_preview import build_exact_card_candidate_report_section, build_exact_card_candidate_prompt_block, build_exact_card_candidate_viewer_summary  # v1.4.15 exact card candidate preview
from reports.strategy_bridge.strategy_shell_planning import build_strategy_shell_report_section, build_strategy_shell_prompt_block, build_strategy_shell_viewer_summary  # v1.4.14 shell planning

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

RUNTIME_CONTRACT_PATH = STRATEGY_ROOT / "runtime" / "strategy_brain_runtime_contract_v1.4.9.json"
SCORING_PREVIEW_PATH = STRATEGY_ROOT / "scoring_previews" / "strategy_scoring_integration_preview_v1.4.10.json"
ROLE_MAPPING_PATH = STRATEGY_ROOT / "role_mapping" / "strategy_role_bucket_mapping_v1.4.11.json"
CUT_PROTECT_PATH = STRATEGY_ROOT / "cut_protect_replacement" / "strategy_cut_protect_replacement_v1.4.12.json"

PREVIEW_PATH = STRATEGY_ROOT / "report_viewer_handoff" / "strategy_report_viewer_handoff_preview_v1.4.13.json"
SUMMARY_PATH = STRATEGY_ROOT / "report_viewer_handoff" / "STRATEGY_REPORT_VIEWER_HANDOFF_SUMMARY_v1.4.13.md"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"
RUNTIME_CONTRACT_PATH = STRATEGY_ROOT / "runtime" / "strategy_brain_runtime_contract_v1.4.9.json"
SCORING_PREVIEW_PATH = STRATEGY_ROOT / "scoring_previews" / "strategy_scoring_integration_preview_v1.4.10.json"
ROLE_MAPPING_PATH = STRATEGY_ROOT / "role_mapping" / "strategy_role_bucket_mapping_v1.4.11.json"
CUT_PROTECT_PATH = STRATEGY_ROOT / "cut_protect_replacement" / "strategy_cut_protect_replacement_v1.4.12.json"
PREVIEW_PATH = STRATEGY_ROOT / "report_viewer_handoff" / "strategy_report_viewer_handoff_preview_v1.4.13.json"
SUMMARY_PATH = STRATEGY_ROOT / "report_viewer_handoff" / "STRATEGY_REPORT_VIEWER_HANDOFF_SUMMARY_v1.4.13.md"

def _v1_4_40_6_context_text(context=None, *args, **kwargs):
    parts = []
    for item in (context, args, kwargs):
        if isinstance(item, dict):
            for key in (
                "deck_text", "decklist_text", "raw_deck_text", "commander",
                "commander_name", "deck_name", "name", "colors",
                "color_identity", "review_direction", "collection_mode",
            ):
                value = item.get(key)
                if value:
                    parts.append(str(value))
        elif item:
            parts.append(str(item))
    return "\n".join(parts).strip()

def _v1_4_40_6_context_key(context=None, *args, **kwargs):
    if isinstance(context, dict):
        deck_name = str(context.get("deck_name") or context.get("name") or "")
        commander = str(context.get("commander") or context.get("commander_name") or "")
        deck_text = str(context.get("deck_text") or context.get("decklist_text") or context.get("raw_deck_text") or "")
        return (deck_name, commander, len(deck_text), deck_text[:160])
    return ("non_dict", id(context), len(args), tuple(sorted(str(k) for k in kwargs.keys())))

def _v1_4_40_6_stage_title(stage_id):
    return {
        "active_scoring": "Strategy Knowledge Active Scoring",
        "live_profile_status": "Strategy Knowledge Live Profile Status",
        "strategy_shell": "Build From Collection Strategy Shell Planning",
        "exact_card_candidate": "Exact Card Candidate Selection Preview",
        "strategy_role_count": "Strategy Role Count / Strategy Knowledge Status",
        "mana_base": "Mana Base Planning Status",
        "land_insertion": "Land Insertion Preview Status",
        "full_100_card_draft": "Full 100-Card Draft Preview Status",
        "final_inclusion_lock": "Final Inclusion Lock Status",
        "finished_mana_base": "Finished Mana Base Generation Status",
        "land_deck_write": "Land Deck-Write Status",
        "final_deck_export": "Final Deck Export Status",
        "v1_4_regression": "v1.4 Regression Status",
        "v1_4_stable_lock": "v1.4 Stable Lock Status",
    }.get(stage_id, stage_id.replace("_", " ").title())

def _v1_4_40_6_report_fallback(stage_id, context=None, *args, **kwargs):
    payload = _v1_4_40_6_score_context(context, *args, **kwargs)
    title = _v1_4_40_6_stage_title(stage_id)
    lines = [
        f"## {title}",
        "",
        "- Compatibility helper: active",
        "- Runtime behavior: safe report/status fallback",
        "- Final deck write/generation: not executed by this compatibility helper",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles', 249)}",
        f"- Legacy five-profile preview: {payload.get('legacy_preview_status', 'deprecated_fallback_only')}",
        f"- Scoring source: `{payload.get('scoring_source', 'strategy_knowledge/index/strategy_profile_index.latest.json')}`",
    ]

    matches = payload.get("top_matches") or []
    if matches:
        lines.extend(["", "### Strategy Context"])
        for item in matches[:5]:
            display = item.get("display_name") or item.get("strategy_id") or "Unknown Strategy"
            sid = item.get("strategy_id") or "unknown"
            score = item.get("score", item.get("raw_score", "n/a"))
            lines.append(f"- **{display}** (`{sid}`), score {score}")

    if payload.get("compatibility_error"):
        lines.extend(["", "### Compatibility Note", f"- `{payload.get('compatibility_error')}`"])

    return "\n".join(lines).rstrip()

def _v1_4_40_6_prompt_fallback(stage_id, context=None, *args, **kwargs):
    payload = _v1_4_40_6_score_context(context, *args, **kwargs)
    title = _v1_4_40_6_stage_title(stage_id)
    lines = [
        f"{title}:",
        "- Compatibility helper active.",
        "- Do not assume this helper executed final generation or deck writing.",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles', 249)}",
        f"- Legacy preview status: {payload.get('legacy_preview_status', 'deprecated_fallback_only')}",
    ]
    for item in (payload.get("top_matches") or [])[:5]:
        lines.append(f"- Strategy context: {item.get('display_name') or item.get('strategy_id')} score {item.get('score', item.get('raw_score', 'n/a'))}")
    return "\n".join(lines).rstrip()

def _v1_4_40_6_viewer_fallback(stage_id, context=None, *args, **kwargs):
    payload = _v1_4_40_6_score_context(context, *args, **kwargs)
    return {
        "title": _v1_4_40_6_stage_title(stage_id),
        "status": "recovered_v1.4.40.6",
        "stage_id": stage_id,
        "generation_executed": False,
        "active_scoring_profiles": payload.get("active_scoring_profiles", 249),
        "legacy_preview_status": payload.get("legacy_preview_status", "deprecated_fallback_only"),
        "top_match_count": len(payload.get("top_matches") or []),
    }

def _v1_4_40_6_report(stage_id, module_name, function_name, context=None, *args, **kwargs):
    existing = _v1_4_40_6_call_existing(module_name, function_name, context, *args, **kwargs)
    if existing:
        return existing
    return _v1_4_40_6_report_fallback(stage_id, context, *args, **kwargs)

def _v1_4_40_6_prompt(stage_id, module_name, function_name, context=None, *args, **kwargs):
    existing = _v1_4_40_6_call_existing(module_name, function_name, context, *args, **kwargs)
    if existing:
        return existing
    return _v1_4_40_6_prompt_fallback(stage_id, context, *args, **kwargs)

def _v1_4_40_6_viewer(stage_id, module_name, function_name, context=None, *args, **kwargs):
    existing = _v1_4_40_6_call_existing(module_name, function_name, context, *args, **kwargs)
    if existing:
        return existing
    return _v1_4_40_6_viewer_fallback(stage_id, context, *args, **kwargs)

def build_v1_4_regression_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("v1_4_regression", "reports.strategy_bridge.strategy_v1_4_regression_lock_candidate", "build_v1_4_regression_report_section", context, *args, **kwargs)

def build_v1_4_regression_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("v1_4_regression", "reports.strategy_bridge.strategy_v1_4_regression_lock_candidate", "build_v1_4_regression_prompt_block", context, *args, **kwargs)

def build_v1_4_regression_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("v1_4_regression", "reports.strategy_bridge.strategy_v1_4_regression_lock_candidate", "build_v1_4_regression_viewer_summary", context, *args, **kwargs)
