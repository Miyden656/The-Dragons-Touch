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

def build_strategy_role_count_report_section(context=None, *args, **kwargs):
    """v1.4.40.4 compatibility recovery for older report paths.

    Older report-generation code still calls this role-count helper. Recent
    Strategy Knowledge integration work moved the active role/strategy scoring
    surface to the 249-profile scorer, so this shim preserves the old call name
    while reporting through the current active scoring path.
    """
    payload = _v1_4_40_4_score_context(context, *args, **kwargs)

    lines = [
        "## Strategy Role Count / Strategy Knowledge Status",
        "",
        "- Strategy Knowledge: Active",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles', 249)}",
        f"- Scoring source: `{payload.get('scoring_source', 'strategy_knowledge/index/strategy_profile_index.latest.json')}`",
        f"- Legacy five-profile preview: {payload.get('legacy_preview_status', 'deprecated_fallback_only')}",
        "- Role-count guidance: derived from top strategy matches and active Strategy Knowledge context.",
        "",
        "### Top Strategy Matches for Role Guidance",
    ]

    matches = payload.get("top_matches") or []
    if matches:
        for item in matches[:8]:
            display = item.get("display_name") or item.get("strategy_id") or "Unknown Strategy"
            sid = item.get("strategy_id") or "unknown"
            score = item.get("score", item.get("raw_score", "n/a"))
            hits = item.get("phrase_hits") or item.get("keyword_hits") or item.get("role_hits") or []
            hit_text = f" — hits: {', '.join(str(hit) for hit in hits[:5])}" if hits else ""
            lines.append(f"- **{display}** (`{sid}`), score {score}{hit_text}")
    else:
        lines.append("- No top strategy matches were available from the active scorer during recovery.")

    if payload.get("recovery_error"):
        lines.extend([
            "",
            "### Recovery Note",
            f"- Active scorer fallback note: `{payload.get('recovery_error')}`",
        ])

    return "\n".join(lines).rstrip()

def build_strategy_role_count_prompt_block(context=None, *args, **kwargs):
    payload = _v1_4_40_4_score_context(context, *args, **kwargs)
    matches = payload.get("top_matches") or []
    lines = [
        "Strategy Role Count / Strategy Knowledge Context:",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles', 249)}",
        f"- Legacy preview status: {payload.get('legacy_preview_status', 'deprecated_fallback_only')}",
        "- Use top strategy matches to guide role-count expectations, cuts, protection, and replacements.",
    ]
    for item in matches[:8]:
        lines.append(f"- {item.get('display_name') or item.get('strategy_id')}: score {item.get('score', item.get('raw_score', 'n/a'))}")
    return "\n".join(lines).rstrip()

def build_strategy_role_count_viewer_summary(context=None, *args, **kwargs):
    payload = _v1_4_40_4_score_context(context, *args, **kwargs)
    return {
        "title": "Strategy Role Count / Strategy Knowledge",
        "active_scoring_profiles": payload.get("active_scoring_profiles", 249),
        "legacy_preview_status": payload.get("legacy_preview_status", "deprecated_fallback_only"),
        "top_match_count": len(payload.get("top_matches") or []),
        "status": "recovered_v1.4.40.4",
    }

def build_mana_base_report_section(context=None, *args, **kwargs):
    """v1.4.40.5 compatibility recovery for older report paths.

    Older report-generation code still calls this mana-base helper. This shim
    preserves the old call name and returns safe guidance/status text without
    performing final mana-base generation or land insertion.
    """
    basic = _v1_4_40_5_extract_basic_context(context, *args, **kwargs)
    payload = _v1_4_40_5_score_context(context, *args, **kwargs)

    lines = [
        "## Mana Base Planning Status",
        "",
        "- Mana-base report helper: compatibility recovery active",
        "- Mana-base generation: not executed by this helper",
        "- Land insertion/write: not executed by this helper",
        f"- Deck size context: {basic.get('deck_size')}",
        f"- Commander context: {basic.get('commander')}",
        f"- Color identity context: {basic.get('colors')}",
        f"- Strategy Knowledge active scoring profiles: {payload.get('active_scoring_profiles', 249)}",
        f"- Legacy five-profile preview: {payload.get('legacy_preview_status', 'deprecated_fallback_only')}",
        "",
        "### Mana Base Review Guidance",
        "- Check land count against deck speed, color intensity, and average mana value.",
        "- Protect color fixing before cutting utility lands.",
        "- Treat basic lands as broadly available unless the user has chosen collection-only restrictions.",
        "- Use the deck's top strategy matches to bias utility lands, ramp, and fixing choices.",
    ]

    matches = payload.get("top_matches") or []
    if matches:
        lines.extend(["", "### Strategy Context for Mana Base"])
        for item in matches[:5]:
            display = item.get("display_name") or item.get("strategy_id") or "Unknown Strategy"
            sid = item.get("strategy_id") or "unknown"
            score = item.get("score", item.get("raw_score", "n/a"))
            lines.append(f"- **{display}** (`{sid}`), score {score}")

    if payload.get("recovery_error"):
        lines.extend([
            "",
            "### Recovery Note",
            f"- Active scorer fallback note: `{payload.get('recovery_error')}`",
        ])

    return "\n".join(lines).rstrip()

def build_mana_base_prompt_block(context=None, *args, **kwargs):
    basic = _v1_4_40_5_extract_basic_context(context, *args, **kwargs)
    payload = _v1_4_40_5_score_context(context, *args, **kwargs)
    lines = [
        "Mana Base Planning Context:",
        "- Compatibility helper active; do not assume final land insertion happened here.",
        f"- Deck size context: {basic.get('deck_size')}",
        f"- Commander context: {basic.get('commander')}",
        f"- Color identity context: {basic.get('colors')}",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles', 249)}",
        f"- Legacy preview status: {payload.get('legacy_preview_status', 'deprecated_fallback_only')}",
        "- Review land count, fixing, ramp/fixing overlap, and utility lands according to the deck's strategy.",
    ]
    for item in (payload.get("top_matches") or [])[:5]:
        lines.append(f"- Strategy context: {item.get('display_name') or item.get('strategy_id')} score {item.get('score', item.get('raw_score', 'n/a'))}")
    return "\n".join(lines).rstrip()

def build_mana_base_viewer_summary(context=None, *args, **kwargs):
    basic = _v1_4_40_5_extract_basic_context(context, *args, **kwargs)
    payload = _v1_4_40_5_score_context(context, *args, **kwargs)
    return {
        "title": "Mana Base Planning Status",
        "status": "recovered_v1.4.40.5",
        "mana_base_generation_executed": False,
        "land_write_executed": False,
        "deck_size": basic.get("deck_size"),
        "commander": basic.get("commander"),
        "colors": basic.get("colors"),
        "active_scoring_profiles": payload.get("active_scoring_profiles", 249),
        "legacy_preview_status": payload.get("legacy_preview_status", "deprecated_fallback_only"),
        "top_match_count": len(payload.get("top_matches") or []),
    }

def build_strategy_shell_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("strategy_shell", "reports.strategy_bridge.strategy_shell_planning", "build_strategy_shell_report_section", context, *args, **kwargs)

def build_strategy_shell_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("strategy_shell", "reports.strategy_bridge.strategy_shell_planning", "build_strategy_shell_prompt_block", context, *args, **kwargs)

def build_strategy_shell_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("strategy_shell", "reports.strategy_bridge.strategy_shell_planning", "build_strategy_shell_viewer_summary", context, *args, **kwargs)

def build_exact_card_candidate_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("exact_card_candidate", "reports.strategy_bridge.exact_card_candidate_preview", "build_exact_card_candidate_report_section", context, *args, **kwargs)

def build_exact_card_candidate_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("exact_card_candidate", "reports.strategy_bridge.exact_card_candidate_preview", "build_exact_card_candidate_prompt_block", context, *args, **kwargs)

def build_exact_card_candidate_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("exact_card_candidate", "reports.strategy_bridge.exact_card_candidate_preview", "build_exact_card_candidate_viewer_summary", context, *args, **kwargs)

def build_strategy_role_count_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report_fallback("strategy_role_count", context, *args, **kwargs)

def build_strategy_role_count_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt_fallback("strategy_role_count", context, *args, **kwargs)

def build_strategy_role_count_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer_fallback("strategy_role_count", context, *args, **kwargs)

def build_mana_base_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("mana_base", "reports.strategy_bridge.mana_base_planning", "build_mana_base_report_section", context, *args, **kwargs)

def build_mana_base_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("mana_base", "reports.strategy_bridge.mana_base_planning", "build_mana_base_prompt_block", context, *args, **kwargs)

def build_mana_base_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("mana_base", "reports.strategy_bridge.mana_base_planning", "build_mana_base_viewer_summary", context, *args, **kwargs)

def build_land_insertion_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("land_insertion", "reports.strategy_bridge.land_insertion_preview", "build_land_insertion_report_section", context, *args, **kwargs)

def build_land_insertion_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("land_insertion", "reports.strategy_bridge.land_insertion_preview", "build_land_insertion_prompt_block", context, *args, **kwargs)

def build_land_insertion_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("land_insertion", "reports.strategy_bridge.land_insertion_preview", "build_land_insertion_viewer_summary", context, *args, **kwargs)

def build_full_100_card_draft_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("full_100_card_draft", "reports.strategy_bridge.full_100_card_draft_preview", "build_full_100_card_draft_report_section", context, *args, **kwargs)

def build_full_100_card_draft_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("full_100_card_draft", "reports.strategy_bridge.full_100_card_draft_preview", "build_full_100_card_draft_prompt_block", context, *args, **kwargs)

def build_full_100_card_draft_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("full_100_card_draft", "reports.strategy_bridge.full_100_card_draft_preview", "build_full_100_card_draft_viewer_summary", context, *args, **kwargs)

def build_final_inclusion_lock_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("final_inclusion_lock", "reports.strategy_bridge.final_inclusion_lock", "build_final_inclusion_lock_report_section", context, *args, **kwargs)

def build_final_inclusion_lock_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("final_inclusion_lock", "reports.strategy_bridge.final_inclusion_lock", "build_final_inclusion_lock_prompt_block", context, *args, **kwargs)

def build_final_inclusion_lock_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("final_inclusion_lock", "reports.strategy_bridge.final_inclusion_lock", "build_final_inclusion_lock_viewer_summary", context, *args, **kwargs)

def build_finished_mana_base_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("finished_mana_base", "reports.strategy_bridge.finished_mana_base_generation", "build_finished_mana_base_report_section", context, *args, **kwargs)

def build_finished_mana_base_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("finished_mana_base", "reports.strategy_bridge.finished_mana_base_generation", "build_finished_mana_base_prompt_block", context, *args, **kwargs)

def build_finished_mana_base_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("finished_mana_base", "reports.strategy_bridge.finished_mana_base_generation", "build_finished_mana_base_viewer_summary", context, *args, **kwargs)

def build_land_deck_write_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("land_deck_write", "reports.strategy_bridge.land_deck_write_integration", "build_land_deck_write_report_section", context, *args, **kwargs)

def build_land_deck_write_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("land_deck_write", "reports.strategy_bridge.land_deck_write_integration", "build_land_deck_write_prompt_block", context, *args, **kwargs)

def build_land_deck_write_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("land_deck_write", "reports.strategy_bridge.land_deck_write_integration", "build_land_deck_write_viewer_summary", context, *args, **kwargs)

def build_final_deck_export_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("final_deck_export", "reports.strategy_bridge.final_deck_export_integration", "build_final_deck_export_report_section", context, *args, **kwargs)

def build_final_deck_export_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("final_deck_export", "reports.strategy_bridge.final_deck_export_integration", "build_final_deck_export_prompt_block", context, *args, **kwargs)

def build_final_deck_export_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("final_deck_export", "reports.strategy_bridge.final_deck_export_integration", "build_final_deck_export_viewer_summary", context, *args, **kwargs)
