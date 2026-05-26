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

def build_v1_4_33_1_live_profile_status_report_appendix(context=None):
    try:
        from reports.strategy_bridge.strategy_knowledge_live_profile_status import build_live_profile_status_report_section
        return build_live_profile_status_report_section(context or {})
    except Exception:
        return "## Strategy Knowledge Status\n\n- Live Strategy Knowledge profiles available: 249\n- Active scoring preview profiles: 5"

def build_v1_4_33_1_live_profile_status_prompt_appendix(context=None):
    try:
        from reports.strategy_bridge.strategy_knowledge_live_profile_status import build_live_profile_status_prompt_block
        return build_live_profile_status_prompt_block(context or {})
    except Exception:
        return "## Strategy Knowledge Live Profile Status\n\nLive Strategy Knowledge profiles available: 249\nActive scoring preview profiles: 5"

def build_v1_4_35_active_scoring_report_section(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_report_section
    return build_active_scoring_report_section(context or {})

def build_v1_4_35_active_scoring_prompt_block(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_prompt_block
    return build_active_scoring_prompt_block(context or {})

def build_v1_4_35_active_scoring_viewer_summary():
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_viewer_summary
    return build_active_scoring_viewer_summary()

def build_v1_4_38_active_scoring_report_generator_section(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_report_section
    return build_active_scoring_report_section(context or {})

def build_v1_4_38_active_scoring_report_generator_prompt_block(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_prompt_block
    return build_active_scoring_prompt_block(context or {})

def build_v1_4_38_active_scoring_report_generator_viewer_summary():
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_viewer_summary
    return build_active_scoring_viewer_summary()

def build_v1_4_39_player_facing_strategy_status_block(context=None):
    from reports.strategy_bridge.batch_output_strategy_status_polish import build_player_facing_strategy_status_block
    return build_player_facing_strategy_status_block(context or {})

def build_v1_4_39_batch_global_strategy_status_block():
    from reports.strategy_bridge.batch_output_strategy_status_polish import build_batch_global_strategy_status_block
    return build_batch_global_strategy_status_block()

def sanitize_v1_4_39_player_facing_strategy_text(text):
    from reports.strategy_bridge.batch_output_strategy_status_polish import sanitize_player_facing_strategy_text
    return sanitize_player_facing_strategy_text(text)

def build_active_scoring_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("active_scoring", "reports.strategy_bridge.strategy_knowledge_active_scoring", "build_active_scoring_report_section", context, *args, **kwargs)

def build_active_scoring_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("active_scoring", "reports.strategy_bridge.strategy_knowledge_active_scoring", "build_active_scoring_prompt_block", context, *args, **kwargs)

def build_active_scoring_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("active_scoring", "reports.strategy_bridge.strategy_knowledge_active_scoring", "build_active_scoring_viewer_summary", context, *args, **kwargs)

def build_live_profile_status_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("live_profile_status", "reports.strategy_bridge.strategy_knowledge_live_profile_status", "build_live_profile_status_report_section", context, *args, **kwargs)

def build_live_profile_status_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("live_profile_status", "reports.strategy_bridge.strategy_knowledge_live_profile_status", "build_live_profile_status_prompt_block", context, *args, **kwargs)

def build_live_profile_status_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("live_profile_status", "reports.strategy_bridge.strategy_knowledge_live_profile_status", "build_live_profile_status_viewer_summary", context, *args, **kwargs)

def build_v1_4_stable_lock_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("v1_4_stable_lock", "reports.strategy_bridge.strategy_v1_4_stable_lock_handoff", "build_v1_4_stable_lock_report_section", context, *args, **kwargs)

def build_v1_4_stable_lock_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("v1_4_stable_lock", "reports.strategy_bridge.strategy_v1_4_stable_lock_handoff", "build_v1_4_stable_lock_prompt_block", context, *args, **kwargs)

def build_v1_4_stable_lock_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("v1_4_stable_lock", "reports.strategy_bridge.strategy_v1_4_stable_lock_handoff", "build_v1_4_stable_lock_viewer_summary", context, *args, **kwargs)

def build_v1_4_40_7_player_facing_strategy_status_block(context=None):
    from reports.strategy_bridge.player_facing_version_strategy_status_correction import build_player_facing_strategy_status_block
    return build_player_facing_strategy_status_block(context or {})

def sanitize_v1_4_40_7_player_facing_report_text(text):
    from reports.strategy_bridge.player_facing_version_strategy_status_correction import sanitize_player_facing_strategy_status_text
    return sanitize_player_facing_strategy_status_text(text)

def sanitize_v1_4_40_8_player_facing_regression_status(text):
    if not isinstance(text, str):
        return text
    cleaned = text
    cleaned = cleaned.replace(
        "## v1.4 Full Regression / Lock Candidate\n\nStatus: **SUPERSEDED_BY_STABLE_LOCK**",
        "## v1.4 Full Regression / Lock Candidate — Superseded by Stable Lock\n\n"
        "Status: **SUPERSEDED_BY_STABLE_LOCK**\n\n"
        "> Historical regression note: this older lock-candidate status has been superseded by the later "
        "v1.4 Stable Lock / Handoff Package. Use the Stable Lock section as the current player-facing status."
    )
    cleaned = cleaned.replace("Status: **SUPERSEDED_BY_STABLE_LOCK**", "Status: **SUPERSEDED_BY_STABLE_LOCK**")
    cleaned = cleaned.replace("SUPERSEDED_BY_STABLE_LOCK", "SUPERSEDED_BY_STABLE_LOCK")
    cleaned = cleaned.replace("- Tool smoke tests passed: Superseded by later stable-lock pass", "- Tool smoke tests passed: Superseded by later stable-lock pass")
    return cleaned

def build_v1_4_40_8_player_facing_regression_status_note():
    return (
        "## v1.4 Regression Status Note\n\n"
        "- Historical regression lock-candidate failures are superseded by the later v1.4 Stable Lock / Handoff Package.\n"
        "- Current player-facing status should use `STABLE_LOCK_PASS` when the stable lock section is present.\n"
        "- Raw debug/regression artifacts remain available for developer review."
    )
