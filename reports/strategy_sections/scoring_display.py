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

def _v1_4_40_4_score_context(context=None, *args, **kwargs):
    try:
        from reports.strategy_bridge.strategy_knowledge_active_scoring import score_strategy_profiles
        score_context = context if isinstance(context, dict) else {
            "deck_name": kwargs.get("deck_name", "Strategy role count recovery context"),
            "deck_text": _v1_4_40_4_context_to_text(context, *args, **kwargs),
        }
        if not score_context.get("deck_text"):
            score_context = dict(score_context)
            score_context["deck_text"] = _v1_4_40_4_context_to_text(context, *args, **kwargs)
        return score_strategy_profiles(score_context, max_results=8)
    except Exception as exc:
        return {
            "active_scoring_profiles": 249,
            "legacy_preview_profile_count": 5,
            "legacy_preview_status": "deprecated_fallback_only",
            "scoring_source": "strategy_knowledge/index/strategy_profile_index.latest.json",
            "top_matches": [],
            "recovery_error": str(exc),
        }

def _v1_4_40_5_score_context(context=None, *args, **kwargs):
    try:
        from reports.strategy_bridge.strategy_knowledge_active_scoring import score_strategy_profiles
        score_context = context if isinstance(context, dict) else {
            "deck_name": kwargs.get("deck_name", "Mana base recovery context"),
            "deck_text": _v1_4_40_5_context_to_text(context, *args, **kwargs),
        }
        if not score_context.get("deck_text"):
            score_context = dict(score_context)
            score_context["deck_text"] = _v1_4_40_5_context_to_text(context, *args, **kwargs)
        return score_strategy_profiles(score_context, max_results=6)
    except Exception as exc:
        return {
            "active_scoring_profiles": 249,
            "legacy_preview_profile_count": 5,
            "legacy_preview_status": "deprecated_fallback_only",
            "scoring_source": "strategy_knowledge/index/strategy_profile_index.latest.json",
            "top_matches": [],
            "recovery_error": str(exc),
        }

def _v1_4_40_6_score_context(context=None, *args, **kwargs):
    key = _v1_4_40_6_context_key(context, *args, **kwargs)
    if key in _V1_4_40_6_SCORING_CACHE:
        return _V1_4_40_6_SCORING_CACHE[key]

    try:
        from reports.strategy_bridge.strategy_knowledge_active_scoring import score_strategy_profiles
        if isinstance(context, dict):
            score_context = dict(context)
        else:
            score_context = {
                "deck_name": kwargs.get("deck_name", "Strategy Knowledge compatibility context"),
                "deck_text": _v1_4_40_6_context_text(context, *args, **kwargs),
            }
        if not score_context.get("deck_text"):
            score_context["deck_text"] = _v1_4_40_6_context_text(context, *args, **kwargs)
        payload = score_strategy_profiles(score_context, max_results=8)
    except Exception as exc:
        payload = {
            "active_scoring_profiles": 249,
            "legacy_preview_profile_count": 5,
            "legacy_preview_status": "deprecated_fallback_only",
            "scoring_source": "strategy_knowledge/index/strategy_profile_index.latest.json",
            "top_matches": [],
            "compatibility_error": str(exc),
        }

    _V1_4_40_6_SCORING_CACHE[key] = payload
    return payload
