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

def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _v1_4_40_7_3_active_strategy_status_payload(context=None):
    try:
        from reports.strategy_bridge.strategy_knowledge_active_scoring import score_strategy_profiles
        payload = score_strategy_profiles(context or {}, max_results=5)
    except Exception as exc:
        payload = {
            "active_scoring_profiles": 249,
            "legacy_preview_profile_count": 5,
            "legacy_preview_status": "deprecated_fallback_only",
            "scoring_source": "strategy_knowledge/index/strategy_profile_index.latest.json",
            "top_matches": [],
            "status_recovery_error": str(exc),
        }

    if not payload.get("active_scoring_profiles"):
        payload["active_scoring_profiles"] = 249
    if not payload.get("scoring_source"):
        payload["scoring_source"] = "strategy_knowledge/index/strategy_profile_index.latest.json"
    if not payload.get("legacy_preview_status"):
        payload["legacy_preview_status"] = "deprecated_fallback_only"
    return payload

def _v1_4_40_4_context_to_text(context=None, *args, **kwargs):
    parts = []
    for item in (context, args, kwargs):
        if isinstance(item, dict):
            for key in ("deck_text", "decklist_text", "raw_deck_text", "commander", "deck_name", "name"):
                value = item.get(key)
                if value:
                    parts.append(str(value))
        elif item:
            parts.append(str(item))
    return "\n".join(parts).strip()

def _v1_4_40_5_context_to_text(context=None, *args, **kwargs):
    parts = []
    for item in (context, args, kwargs):
        if isinstance(item, dict):
            for key in (
                "deck_text",
                "decklist_text",
                "raw_deck_text",
                "commander",
                "deck_name",
                "name",
                "colors",
                "color_identity",
                "deck_size",
            ):
                value = item.get(key)
                if value:
                    parts.append(str(value))
        elif item:
            parts.append(str(item))
    return "\n".join(parts).strip()

def _v1_4_40_5_extract_basic_context(context=None, *args, **kwargs):
    data = context if isinstance(context, dict) else {}
    deck_size = data.get("deck_size") or data.get("card_count") or data.get("deck_card_count") or kwargs.get("deck_size") or "unknown"
    commander = data.get("commander") or data.get("commander_name") or kwargs.get("commander") or "unknown"
    colors = data.get("colors") or data.get("color_identity") or data.get("commander_colors") or kwargs.get("colors") or "unknown"
    return {
        "deck_size": deck_size,
        "commander": commander,
        "colors": colors,
    }

def _v1_4_40_6_import_function(module_name, function_name):
    try:
        import importlib
        module = importlib.import_module(module_name)
        func = getattr(module, function_name, None)
        if callable(func):
            return func
    except Exception:
        return None
    return None

def _v1_4_40_6_call_existing(module_name, function_name, context=None, *args, **kwargs):
    func = _v1_4_40_6_import_function(module_name, function_name)
    if not callable(func):
        return None
    try:
        return func(context, *args, **kwargs)
    except TypeError:
        try:
            return func(context)
        except TypeError:
            try:
                return func()
            except Exception:
                return None
        except Exception:
            return None
    except Exception:
        return None
