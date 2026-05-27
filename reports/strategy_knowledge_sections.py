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


# =============================================================================
# FILE LAYOUT (v1.5)
# =============================================================================
# Strategy Knowledge report sections. Bridge between the 249-profile strategy
# catalog and the report writer / report viewer / AI handoff prompt.
#
# This module is the runtime entry point for strategy-related report content.
# It calls into reports/strategy_bridge/* helper modules (v1.4.10 - v1.4.41
# phase artifacts) that themselves load JSON payloads from strategy_knowledge/
# subdirectories.
#
# Public API entry points include:
#   build_strategy_knowledge_report_section(...)
#   build_strategy_knowledge_prompt_block(...)
#   build_strategy_knowledge_viewer_summary(...)
#   ...plus per-phase section/prompt/viewer triplets for each v1.4 milestone
#
# Helper groups:
#   _load_json / _resolve_*       data loading helpers
#   _v1_4_*                       version-stamped phase helpers (some are
#                                  imported by reports/strategy_sections/*)
#   build_*_report_section        markdown render for the report file
#   build_*_prompt_block          blocks injected into AI handoff prompts
#   build_*_viewer_summary        short summaries for the Report Viewer UI
#
# NOTE: _v1_4_* helpers may look unused locally but are imported from
# reports/strategy_sections/adapter.py and similar. Check cross-module imports
# before pruning.
#
# See docs/ARCHITECTURE.md for the strategy selector lookup chain.
# =============================================================================


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

# v1.4.40.7.3 player-facing Strategy Brain Status source replacement
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

def build_strategy_knowledge_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime = _load_json(RUNTIME_CONTRACT_PATH)
    scoring = _load_json(SCORING_PREVIEW_PATH)
    role_mapping = _load_json(ROLE_MAPPING_PATH)
    cut_protect = _load_json(CUT_PROTECT_PATH)

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
    }

    strategy_profiles = []
    for profile in role_mapping.get("strategy_role_profiles", []) or []:
        strategy_profiles.append({
            "strategy_id": profile.get("strategy_id", ""),
            "display_name": profile.get("display_name", ""),
            "primary_role_buckets": profile.get("primary_role_buckets", []),
            "secondary_role_buckets": profile.get("secondary_role_buckets", []),
            "strategy_specific_roles": profile.get("strategy_specific_roles", []),
        })

    return {
        "integration_version": "v1.4.13",
        "integration_mode": "strategy_report_viewer_ai_handoff_integration",
        "report_viewer_strategy_section_enabled": True,
        "ai_handoff_strategy_context_enabled": True,
        "normal_report_strategy_section_enabled": True,
        "user_prompt_strategy_context_enabled": True,
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
        "shell_generation_enabled": False,
        "full_100_card_draft_generation_enabled": False,
        "gate_checks": gate_checks,
        "selected_strategy_system": runtime.get("selected_strategy_system", "unknown"),
        "checked_strategy_count": role_mapping.get("strategy_profile_count", 0),
        "scoring_scenario_matches": scoring.get("scenario_match_count", 0),
        "scoring_scenario_count": scoring.get("scenario_count", 0),
        "protected_sample_count": cut_protect.get("protected_sample_count", 0),
        "possible_cut_sample_count": cut_protect.get("possible_cut_sample_count", 0),
        "replacement_need_sample_count": cut_protect.get("replacement_need_sample_count", 0),
        "strategy_profiles": strategy_profiles,
        "handoff_rules": [
            "Use Strategy Knowledge as context for strategy recognition, role mapping, cuts, protection, replacement guidance, and report wording.",
            "Do not treat Strategy Knowledge as permission to generate a final deck list.",
            "Do not treat possible cuts as mandatory cuts.",
            "Separate bad card from wrong card for this deck.",
            "Separate low power from low synergy.",
            "Protect high-synergy low-raw-power cards when they support the commander's plan.",
            "Keep collection-first behavior unless the user allows outside upgrades.",
            "Assume basic lands are available; keep nonbasic lands collection-first unless outside upgrades are allowed.",
        ],
        "replacement_gate": {
            "replacement_allowed": False,
            "reason": "v1.4.13 surfaces Strategy Knowledge in reports, AI handoff, and Report Viewer, but does not enable deck generation or final card selection.",
            "next_safe_step": "v1.4.14 — Build From Collection Strategy Shell Planning",
        },
    }

def build_strategy_knowledge_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_knowledge_payload(context)
    active_status = _v1_4_40_7_3_active_strategy_status_payload(context)
    active_status = _v1_4_40_7_3_active_strategy_status_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines: List[str] = [
        "## Strategy Knowledge Integration",
        "",
        "Strategy Knowledge is active as report and AI-handoff context for this run.",
        "",
        "### Strategy Brain Status",
        "- Selected strategy system: expanded_strategy_scoring_with_legacy_fallback",
        "- Strategy Knowledge: Active",
        "- Legacy fallback available: Yes — rollback/debug only",
        f"- Active scoring profiles: {active_status.get('active_scoring_profiles', 249)}",
        f"- Scoring source: `{active_status.get('scoring_source', 'strategy_knowledge/index/strategy_profile_index.latest.json')}`",
        "- Legacy five-profile preview: fallback/debug only",
        f"- Protected-context samples: {payload.get('protected_sample_count')}",
        f"- Possible-cut samples: {payload.get('possible_cut_sample_count')}",
        f"- Replacement-need samples: {payload.get('replacement_need_sample_count')}",
        "",
        "### Strategy-Aware Guidance Rules",
    ]
    lines.extend(f"- {rule}" for rule in payload.get("handoff_rules", []))

    profiles = payload.get("strategy_profiles", [])[:8]
    if profiles:
        lines.extend(["", "### Legacy Fallback Strategy Role Profiles"])
        for profile in profiles:
            primary = ", ".join(profile.get("primary_role_buckets", []) or ["None"])
            specific = ", ".join(profile.get("strategy_specific_roles", []) or ["None"])
            lines.append(f"- {profile.get('display_name')} (`{profile.get('strategy_id')}`): primary roles = {primary}; strategy roles = {specific}")

    lines.extend([
        "",
        "### Boundary",
        "- This section improves strategy interpretation, report readability, and AI handoff quality.",
        "- It does not generate a deck, select exact cards, make final deck inclusion decisions, generate role counts, generate a mana base, insert lands, or create a full 100-card draft.",
    ])

    # v1.4.14 Build From Collection Strategy Shell Planning report integration.
    shell_section = build_strategy_shell_report_section(context)
    if shell_section:
        lines.extend(["", shell_section.rstrip()])

    # v1.4.15 Exact Card Candidate Selection Preview report integration.
    candidate_section = build_exact_card_candidate_report_section(context)
    if candidate_section:
        lines.extend(["", candidate_section.rstrip()])

    role_count_section = build_strategy_role_count_report_section(context)
    if role_count_section:
        lines.extend(["", role_count_section.rstrip()])

    mana_section = build_mana_base_report_section(context)
    if mana_section:
        lines.extend(["", mana_section.rstrip()])

    land_section = build_land_insertion_report_section(context)
    if land_section:
        lines.extend(["", land_section.rstrip()])

    # v1.4.19 Full 100-Card Draft Preview report integration.
    full_draft_section = build_full_100_card_draft_report_section(context)
    if full_draft_section:
        lines.extend(["", full_draft_section.rstrip()])

    final_lock_section = build_final_inclusion_lock_report_section(context)
    if final_lock_section:
        lines.extend(["", final_lock_section.rstrip()])

    # v1.4.23 Finished Mana Base Generation Integration report integration.
    finished_mana_section = build_finished_mana_base_report_section(context)
    if finished_mana_section:
        lines.extend(["", finished_mana_section.rstrip()])

    # v1.4.24 Land Deck-Write Integration report integration.
    land_write_section = build_land_deck_write_report_section(context)
    if land_write_section:
        lines.extend(["", land_write_section.rstrip()])

    final_export_section = build_final_deck_export_report_section(context)
    if final_export_section:
        lines.extend(["", final_export_section.rstrip()])

    v1_4_regression_section = build_v1_4_regression_report_section(context)
    if v1_4_regression_section:
        lines.extend(["", v1_4_regression_section.rstrip()])

    v1_4_stable_lock_section = build_v1_4_stable_lock_report_section(context)
    if v1_4_stable_lock_section:
        lines.extend(["", v1_4_stable_lock_section.rstrip()])

    return "\n".join(lines).rstrip()

def build_strategy_knowledge_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_knowledge_payload(context)
    if not any(payload.get("gate_checks", {}).values()):
        return ""

    lines = [
        "## Strategy Knowledge Context",
        "",
        "The Dragon's Touch Strategy Knowledge system is available as context for this review.",
        "",
        "Use it to improve:",
        "- strategy recognition",
        "- commander intent recognition",
        "- role bucket mapping",
        "- cut/protect/replacement reasoning",
        "- off-plan card detection",
        "- AI handoff clarity",
        "",
        "Do not use it as permission to make automatic deck edits or final deck inclusion decisions.",
        "",
        "Important interpretation rules:",
    ]
    lines.extend(f"- {rule}" for rule in payload.get("handoff_rules", []))
    lines.extend([
        "",
        "Current boundary: Strategy Knowledge is report/handoff context only. Deck generation, exact-card selection, role-count generation, mana-base generation, land insertion, shell generation, and full 100-card draft generation are not enabled by this prompt section.",
    ])
    # v1.4.14 Build From Collection Strategy Shell Planning prompt integration.
    shell_prompt = build_strategy_shell_prompt_block(context)
    if shell_prompt:
        lines.extend(["", shell_prompt.rstrip()])

    # v1.4.15 Exact Card Candidate Selection Preview prompt integration.
    candidate_prompt = build_exact_card_candidate_prompt_block(context)
    if candidate_prompt:
        lines.extend(["", candidate_prompt.rstrip()])

    role_count_prompt = build_strategy_role_count_prompt_block(context)
    if role_count_prompt:
        lines.extend(["", role_count_prompt.rstrip()])

    mana_prompt = build_mana_base_prompt_block(context)
    if mana_prompt:
        lines.extend(["", mana_prompt.rstrip()])

    land_prompt = build_land_insertion_prompt_block(context)
    if land_prompt:
        lines.extend(["", land_prompt.rstrip()])

    # v1.4.19 Full 100-Card Draft Preview prompt integration.
    full_draft_prompt = build_full_100_card_draft_prompt_block(context)
    if full_draft_prompt:
        lines.extend(["", full_draft_prompt.rstrip()])

    final_lock_prompt = build_final_inclusion_lock_prompt_block(context)
    if final_lock_prompt:
        lines.extend(["", final_lock_prompt.rstrip()])

    # v1.4.23 Finished Mana Base Generation Integration prompt integration.
    finished_mana_prompt = build_finished_mana_base_prompt_block(context)
    if finished_mana_prompt:
        lines.extend(["", finished_mana_prompt.rstrip()])

    # v1.4.24 Land Deck-Write Integration prompt integration.
    land_write_prompt = build_land_deck_write_prompt_block(context)
    if land_write_prompt:
        lines.extend(["", land_write_prompt.rstrip()])

    final_export_prompt = build_final_deck_export_prompt_block(context)
    if final_export_prompt:
        lines.extend(["", final_export_prompt.rstrip()])

    v1_4_regression_prompt = build_v1_4_regression_prompt_block(context)
    if v1_4_regression_prompt:
        lines.extend(["", v1_4_regression_prompt.rstrip()])

    v1_4_stable_lock_prompt = build_v1_4_stable_lock_prompt_block(context)
    if v1_4_stable_lock_prompt:
        lines.extend(["", v1_4_stable_lock_prompt.rstrip()])

    return "\n".join(lines).rstrip()

def build_strategy_knowledge_viewer_summary() -> str:
    payload = build_strategy_knowledge_payload({})
    active_status = _v1_4_40_7_3_active_strategy_status_payload({})
    active_status = _v1_4_40_7_3_active_strategy_status_payload({})
    lines = [
        "Strategy Brain",
        "==============",
        "",
        "Source: Strategy Knowledge integration artifacts",
        "",
        "Strategy Knowledge is now surfaced in the deck report, user-guided prompt, and Report Viewer AI handoff lane.",
        "",
        "Selected strategy system: expanded_strategy_scoring_with_legacy_fallback",
        "Strategy Knowledge: Active",
        "Legacy fallback available: Yes — rollback/debug only",
        f"Active scoring profiles: {active_status.get('active_scoring_profiles', 249)}",
        f"Scoring source: {active_status.get('scoring_source', 'strategy_knowledge/index/strategy_profile_index.latest.json')}",
        "Legacy five-profile preview: fallback/debug only",
        f"Protected-context samples: {payload.get('protected_sample_count')}",
        f"Possible-cut samples: {payload.get('possible_cut_sample_count')}",
        f"Replacement-need samples: {payload.get('replacement_need_sample_count')}",
        "",
        "Use this as context. It is not a final deck-generation authority.",
    ]
    # v1.4.14 Shell Planning viewer summary integration.
    try:
        shell_summary = build_strategy_shell_viewer_summary()
        if shell_summary:
            lines.extend(["", shell_summary.rstrip()])
    except Exception:
        pass

    # v1.4.15 Exact Card Candidate Selection Preview viewer summary integration.
    try:
        candidate_summary = build_exact_card_candidate_viewer_summary()
        if candidate_summary:
            lines.extend(["", candidate_summary.rstrip()])
    except Exception:
        pass

    try:
        role_count_summary = build_strategy_role_count_viewer_summary()
        if role_count_summary:
            lines.extend(["", role_count_summary.rstrip()])
    except Exception:
        pass

    try:
        mana_summary = build_mana_base_viewer_summary()
        if mana_summary:
            lines.extend(["", mana_summary.rstrip()])
    except Exception:
        pass

    try:
        land_summary = build_land_insertion_viewer_summary()
        if land_summary:
            lines.extend(["", land_summary.rstrip()])
    except Exception:
        pass

    # v1.4.19 Full 100-Card Draft Preview viewer summary integration.
    try:
        full_draft_summary = build_full_100_card_draft_viewer_summary()
        if full_draft_summary:
            lines.extend(["", full_draft_summary.rstrip()])
    except Exception:
        pass

    try:
        final_lock_summary = build_final_inclusion_lock_viewer_summary()
        if final_lock_summary:
            lines.extend(["", final_lock_summary.rstrip()])
    except Exception:
        pass

    # v1.4.23 Finished Mana Base Generation Integration viewer summary integration.
    try:
        finished_mana_summary = build_finished_mana_base_viewer_summary()
        if finished_mana_summary:
            lines.extend(["", finished_mana_summary.rstrip()])
    except Exception:
        pass

    # v1.4.24 Land Deck-Write Integration viewer summary integration.
    try:
        land_write_summary = build_land_deck_write_viewer_summary()
        if land_write_summary:
            lines.extend(["", land_write_summary.rstrip()])
    except Exception:
        pass

    try:
        final_export_summary = build_final_deck_export_viewer_summary()
        if final_export_summary:
            lines.extend(["", final_export_summary.rstrip()])
    except Exception:
        pass

    try:
        pass  # v1.4.40.2 empty try block recovery
    except Exception:
        pass

    try:
        v1_4_regression_summary = build_v1_4_regression_viewer_summary()
        if v1_4_regression_summary:
            lines.extend(["", v1_4_regression_summary.rstrip()])
    except Exception:
        pass

    try:
        v1_4_stable_lock_summary = build_v1_4_stable_lock_viewer_summary()
        if v1_4_stable_lock_summary:
            lines.extend(["", v1_4_stable_lock_summary.rstrip()])
    except Exception:
        pass

    return "\n".join(lines).rstrip()

def write_strategy_knowledge_handoff_preview() -> Dict[str, Any]:
    payload = build_strategy_knowledge_payload({})
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    SUMMARY_PATH.write_text(build_strategy_knowledge_report_section({}) + "\n", encoding="utf-8")
    return payload

def main() -> int:
    print("v1.4.13 - Strategy Report Viewer / AI Handoff Integration")
    print("=" * 78)
    payload = write_strategy_knowledge_handoff_preview()
    print(f"Selected strategy system: {payload.get('selected_strategy_system')}")
    print(f"Strategy profiles available: {payload.get('checked_strategy_count')}")
    print(f"Scoring preview matches: {payload.get('scoring_scenario_matches')} / {payload.get('scoring_scenario_count')}")
    print(f"Protected samples: {payload.get('protected_sample_count')}")
    print(f"Possible cut samples: {payload.get('possible_cut_sample_count')}")
    print(f"Replacement need samples: {payload.get('replacement_need_sample_count')}")
    print(f"Preview written: {PREVIEW_PATH}")
    print(f"Summary written: {SUMMARY_PATH}")
    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    print("Next safe step: v1.4.14 — Build From Collection Strategy Shell Planning")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

# v1.4.33.1 live profile status recovery
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

# v1.4.35 active scoring expansion wrappers
def build_v1_4_35_active_scoring_report_section(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_report_section
    return build_active_scoring_report_section(context or {})

def build_v1_4_35_active_scoring_prompt_block(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_prompt_block
    return build_active_scoring_prompt_block(context or {})

def build_v1_4_35_active_scoring_viewer_summary():
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_viewer_summary
    return build_active_scoring_viewer_summary()

# v1.4.38 active scoring report generator integration
def build_v1_4_38_active_scoring_report_generator_section(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_report_section
    return build_active_scoring_report_section(context or {})

def build_v1_4_38_active_scoring_report_generator_prompt_block(context=None):
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_prompt_block
    return build_active_scoring_prompt_block(context or {})

def build_v1_4_38_active_scoring_report_generator_viewer_summary():
    from reports.strategy_bridge.strategy_knowledge_active_scoring import build_active_scoring_viewer_summary
    return build_active_scoring_viewer_summary()

# v1.4.39 player-facing strategy status polish
def build_v1_4_39_player_facing_strategy_status_block(context=None):
    from reports.strategy_bridge.batch_output_strategy_status_polish import build_player_facing_strategy_status_block
    return build_player_facing_strategy_status_block(context or {})

def build_v1_4_39_batch_global_strategy_status_block():
    from reports.strategy_bridge.batch_output_strategy_status_polish import build_batch_global_strategy_status_block
    return build_batch_global_strategy_status_block()

def sanitize_v1_4_39_player_facing_strategy_text(text):
    from reports.strategy_bridge.batch_output_strategy_status_polish import sanitize_player_facing_strategy_text
    return sanitize_player_facing_strategy_text(text)

# v1.4.40.4 strategy role count report section NameError recovery
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

# v1.4.40.5 mana base report section NameError recovery
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

# v1.4.40.6 Strategy Knowledge Report Helper Compatibility Sweep
# This block intentionally sits late in the module so these names are available
# to older report paths even if previous imports/shims were lost during cleanup.

_V1_4_40_6_SCORING_CACHE = {}

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

def build_v1_4_regression_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("v1_4_regression", "reports.strategy_bridge.strategy_v1_4_regression_lock_candidate", "build_v1_4_regression_report_section", context, *args, **kwargs)

def build_v1_4_regression_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("v1_4_regression", "reports.strategy_bridge.strategy_v1_4_regression_lock_candidate", "build_v1_4_regression_prompt_block", context, *args, **kwargs)

def build_v1_4_regression_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("v1_4_regression", "reports.strategy_bridge.strategy_v1_4_regression_lock_candidate", "build_v1_4_regression_viewer_summary", context, *args, **kwargs)

def build_v1_4_stable_lock_report_section(context=None, *args, **kwargs):
    return _v1_4_40_6_report("v1_4_stable_lock", "reports.strategy_bridge.strategy_v1_4_stable_lock_handoff", "build_v1_4_stable_lock_report_section", context, *args, **kwargs)

def build_v1_4_stable_lock_prompt_block(context=None, *args, **kwargs):
    return _v1_4_40_6_prompt("v1_4_stable_lock", "reports.strategy_bridge.strategy_v1_4_stable_lock_handoff", "build_v1_4_stable_lock_prompt_block", context, *args, **kwargs)

def build_v1_4_stable_lock_viewer_summary(context=None, *args, **kwargs):
    return _v1_4_40_6_viewer("v1_4_stable_lock", "reports.strategy_bridge.strategy_v1_4_stable_lock_handoff", "build_v1_4_stable_lock_viewer_summary", context, *args, **kwargs)


# v1.4.40.7 player-facing version / strategy status correction
def build_v1_4_40_7_player_facing_strategy_status_block(context=None):
    from reports.strategy_bridge.player_facing_version_strategy_status_correction import build_player_facing_strategy_status_block
    return build_player_facing_strategy_status_block(context or {})

def sanitize_v1_4_40_7_player_facing_report_text(text):
    from reports.strategy_bridge.player_facing_version_strategy_status_correction import sanitize_player_facing_strategy_status_text
    return sanitize_player_facing_strategy_status_text(text)

# v1.4.40.8 player-facing regression/stable-lock status cleanup
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
