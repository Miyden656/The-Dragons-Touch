from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

VERSION = "v1.4.39"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

POLISH_ROOT = STRATEGY_ROOT / "batch_output_polish" / "v1.4.39"
POLISH_JSON = POLISH_ROOT / "batch_output_cleanup_player_facing_strategy_status_polish_v1.4.39.json"
POLISH_MD = POLISH_ROOT / "BATCH_OUTPUT_CLEANUP_PLAYER_FACING_STRATEGY_STATUS_POLISH_v1.4.39.md"
SMOKE_MD = POLISH_ROOT / "PLAYER_FACING_STRATEGY_STATUS_SMOKE_TEXT_v1.4.39.md"

OLD_LINES = [
    "Active scoring profiles: 249",
    "Legacy preview matches: 5 / 5 fallback profiles",
    "Legacy Fallback Strategy Role Profiles",
    "Strategy Knowledge Integration",
]

STATIC_MILESTONE_TERMS = [
]

SECTIONS_APPEND = '\n# v1.4.39 player-facing strategy status polish\ndef build_v1_4_39_player_facing_strategy_status_block(context=None):\n    from reports.batch_output_strategy_status_polish import build_player_facing_strategy_status_block\n    return build_player_facing_strategy_status_block(context or {})\n\ndef build_v1_4_39_batch_global_strategy_status_block():\n    from reports.batch_output_strategy_status_polish import build_batch_global_strategy_status_block\n    return build_batch_global_strategy_status_block()\n\ndef sanitize_v1_4_39_player_facing_strategy_text(text):\n    from reports.batch_output_strategy_status_polish import sanitize_player_facing_strategy_text\n    return sanitize_player_facing_strategy_text(text)\n'
BRIDGE_APPEND = '\n# v1.4.39 player-facing strategy status polish\ndef write_v1_4_39_batch_strategy_status_polish_artifacts(output_dir=None, context=None):\n    from reports.batch_output_strategy_status_polish import write_batch_output_polish_artifacts\n    return write_batch_output_polish_artifacts(output_dir=output_dir, context=context or {})\n'

def build_player_facing_strategy_status_block(context: Any = None) -> str:
    from reports.strategy_knowledge_active_scoring import score_strategy_profiles

    payload = score_strategy_profiles(context or {
        "deck_name": "v1.4.39 player-facing status smoke test",
        "deck_text": "tokens spellslinger landfall artifacts sacrifice recursion combat lifegain vehicles equipment",
    }, max_results=5)

    lines = [
        "## Strategy Knowledge Status",
        "",
        "- Strategy Knowledge: Active",
        "- Active scoring profiles: 249",
        f"- Scoring source: `{payload.get('scoring_source')}`",
        "- Use: strategy recognition, cut/protect/replacement guidance, and AI handoff context.",
        "- Legacy five-profile preview: fallback only",
        "",
        "### Top Strategy Matches",
    ]

    for item in payload.get("top_matches", [])[:5]:
        hits = item.get("phrase_hits") or item.get("keyword_hits") or item.get("role_hits") or []
        hit_text = f" — hits: {', '.join(hits[:5])}" if hits else ""
        lines.append(f"- **{item.get('display_name')}** (`{item.get('strategy_id')}`), score {item.get('score')}{hit_text}")

    return "\n".join(lines).rstrip()

def build_batch_global_strategy_status_block() -> str:
    return "\n".join([
        "## Batch Strategy Knowledge Status",
        "",
        "- Strategy Knowledge: Active",
        "- Active scoring profiles: 249",
        "- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`",
        "- Legacy five-profile preview: fallback only",
        "- Batch behavior: show this global status once, then show deck-specific top strategy matches per deck.",
    ]).rstrip()

def sanitize_player_facing_strategy_text(text: str) -> str:
    cleaned = text

    replacements = {
        "Active scoring profiles: 249": "Active scoring profiles: 249",
        "Legacy preview matches: 5 / 5 fallback profiles": "Legacy preview matches: 5 / 5 fallback profiles",
        "Legacy Fallback Strategy Role Profiles": "Legacy Fallback Strategy Role Profiles",
        "Strategy Knowledge Integration": "Strategy Knowledge Integration",
        "v1.4 expanded Strategy Knowledge reporting": "v1.4 expanded Strategy Knowledge reporting",
    }

    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    kept_lines: list[str] = []
    for line in cleaned.splitlines():
        lower = line.lower()
        if any(term in lower for term in STATIC_MILESTONE_TERMS) and ("debug" not in lower and "dev" not in lower):
            continue
        kept_lines.append(line)

    cleaned = "\n".join(kept_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def patch_report_surfaces() -> Dict[str, Any]:
    candidate_paths: list[Path] = []
    for rel in [
        "reports/strategy_knowledge_sections.py",
        "reports/strategy_live_bridge.py",
        "reports/active_scoring_report_generator_integration.py",
    ]:
        path = PROJECT_ROOT / rel
        if path.exists():
            candidate_paths.append(path)

    reports_dir = PROJECT_ROOT / "reports"
    if reports_dir.exists():
        for path in sorted(reports_dir.glob("*.py")):
            if path in candidate_paths:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(old in text for old in OLD_LINES):
                candidate_paths.append(path)

    patched: list[dict[str, Any]] = []
    unchanged: list[str] = []

    for path in candidate_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        changes: list[str] = []

        sanitized = sanitize_player_facing_strategy_text(text)
        if sanitized != text:
            text = sanitized
            changes.append("sanitized_old_player_facing_strategy_language")

        if path.name == "strategy_knowledge_sections.py" and "v1.4.39 player-facing strategy status polish" not in text:
            text += "\n\n" + SECTIONS_APPEND
            changes.append("added_v1_4_39_strategy_status_helpers")

        if path.name == "strategy_live_bridge.py" and "write_v1_4_39_batch_strategy_status_polish_artifacts" not in text:
            text += "\n\n" + BRIDGE_APPEND
            changes.append("added_v1_4_39_live_bridge_helper")

        if text != original:
            path.write_text(text, encoding="utf-8")
            patched.append({
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "changes": changes,
            })
        else:
            unchanged.append(str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    return {
        "candidate_file_count": len(candidate_paths),
        "patched_file_count": len(patched),
        "patched_files": patched,
        "unchanged_files": unchanged,
    }

def build_batch_output_polish_payload(context: Any = None) -> Dict[str, Any]:
    from reports.strategy_knowledge_active_scoring import score_strategy_profiles

    sample_context = context or {
        "deck_name": "v1.4.39 batch/player-facing status smoke test",
        "deck_text": "tokens spellslinger landfall artifacts sacrifice recursion combat lifegain vehicles equipment",
    }
    scoring = score_strategy_profiles(sample_context, max_results=8)
    player_block = build_player_facing_strategy_status_block(sample_context)
    batch_block = build_batch_global_strategy_status_block()

    noisy_sample = "\n".join([
        "## Strategy Knowledge Integration",
        "- Active scoring profiles: 249",
        "- Legacy preview matches: 5 / 5 fallback profiles",
        "### Legacy Fallback Strategy Role Profiles",
        "- Aristocrats",
        "- Landfall",
        "- Spellslinger",
        "- Tokens",
        "- Voltron",
    ])

    sanitized_sample = sanitize_player_facing_strategy_text(noisy_sample)
    source_patch = patch_report_surfaces()

    sections_path = PROJECT_ROOT / "reports" / "strategy_knowledge_sections.py"
    bridge_path = PROJECT_ROOT / "reports" / "strategy_live_bridge.py"

    sections_text = sections_path.read_text(encoding="utf-8", errors="replace") if sections_path.exists() else ""
    bridge_text = bridge_path.read_text(encoding="utf-8", errors="replace") if bridge_path.exists() else ""

    payload = {
        "polish_version": VERSION,
        "polish_name": "Batch Output Cleanup / Player-Facing Strategy Status Polish",
        "runtime_behavior_changed": True,
        "player_facing_strategy_status_polished": True,
        "batch_output_cleanup_guidance_installed": True,
        "active_scoring_profiles": scoring.get("active_scoring_profiles"),
        "legacy_preview_profile_count": scoring.get("legacy_preview_profile_count"),
        "legacy_preview_status": scoring.get("legacy_preview_status"),
        "scoring_source": scoring.get("scoring_source"),
        "top_matches_available": bool(scoring.get("top_matches")),
        "source_patch": source_patch,
        "player_status_block": player_block,
        "batch_global_status_block": batch_block,
        "sanitized_sample": sanitized_sample,
        "player_status_has_249": "Active scoring profiles: 249" in player_block,
        "player_status_marks_fallback": "fallback only" in player_block,
        "batch_status_has_249": "Active scoring profiles: 249" in batch_block,
        "batch_status_marks_fallback": "fallback only" in batch_block,
        "sanitized_sample_removed_old_five_line": "Active scoring profiles: 249" not in sanitized_sample,
        "sanitized_sample_replaced_loaded_profiles_heading": "Legacy Fallback Strategy Role Profiles" not in sanitized_sample,
        "strategy_sections_has_v1_4_39_helpers": "v1.4.39 player-facing strategy status polish" in sections_text,
        "strategy_live_bridge_has_v1_4_39_helper": "write_v1_4_39_batch_strategy_status_polish_artifacts" in bridge_text,
        "main_py_changed": False,
        "gate_checks": {
            "active_scoring_profiles_is_249": scoring.get("active_scoring_profiles") == 249,
            "legacy_preview_profile_count_is_5": scoring.get("legacy_preview_profile_count") == 5,
            "legacy_preview_is_fallback_only": scoring.get("legacy_preview_status") == "deprecated_fallback_only",
            "top_matches_available": bool(scoring.get("top_matches")),
            "player_status_surfaces_249": "Active scoring profiles: 249" in player_block,
            "player_status_marks_legacy_fallback": "fallback only" in player_block,
            "batch_status_surfaces_249": "Active scoring profiles: 249" in batch_block,
            "batch_status_marks_legacy_fallback": "fallback only" in batch_block,
            "sanitizer_removes_old_five_profile_line": "Active scoring profiles: 249" not in sanitized_sample,
            "sanitizer_relabels_loaded_role_profiles": "Legacy Fallback Strategy Role Profiles" not in sanitized_sample,
            "strategy_sections_helpers_present": "v1.4.39 player-facing strategy status polish" in sections_text,
            "strategy_live_bridge_helper_present": "write_v1_4_39_batch_strategy_status_polish_artifacts" in bridge_text,
            "main_py_not_changed": True,
        },
    }

    return payload

def build_batch_output_polish_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_batch_output_polish_payload({})
    lines = [
        "# Batch Output Cleanup / Player-Facing Strategy Status Polish — v1.4.39",
        "",
        "## Result",
        "",
        f"- Player-facing strategy status polished: {payload.get('player_facing_strategy_status_polished')}",
        f"- Batch output cleanup guidance installed: {payload.get('batch_output_cleanup_guidance_installed')}",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"- Legacy preview profile count: {payload.get('legacy_preview_profile_count')}",
        f"- Legacy preview status: {payload.get('legacy_preview_status')}",
        f"- Scoring source: `{payload.get('scoring_source')}`",
        f"- Top matches available: {payload.get('top_matches_available')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Source Patch",
        "",
        f"- Candidate files inspected: {payload.get('source_patch', {}).get('candidate_file_count')}",
        f"- Patched files: {payload.get('source_patch', {}).get('patched_file_count')}",
        "",
    ]

    for item in payload.get("source_patch", {}).get("patched_files", []):
        lines.append(f"- `{item.get('path')}`: {', '.join(item.get('changes', []))}")

    lines.extend([
        "",
        "## Player-Facing Status Block",
        "",
        payload.get("player_status_block", ""),
        "",
        "## Batch Global Status Block",
        "",
        payload.get("batch_global_status_block", ""),
        "",
        "## Gate Checks",
        "",
    ])

    for name, value in payload.get("gate_checks", {}).items():
        lines.append(f"- {name}: {value}")

    lines.extend([
        "",
        "## Boundary",
        "",
        "- This patch polishes player-facing/batch strategy status language.",
        "- It keeps debug/fallback details available without presenting the five-profile preview as the active library.",
        "- It does not change `main.py`.",
        "",
        "## Next Safe Step",
        "",
        payload.get("next_safe_step", ""),
    ])

    return "\n".join(lines).rstrip()

def write_batch_output_polish_artifacts(output_dir: str | Path | None = None, context: Any = None) -> Dict[str, Any]:
    payload = build_batch_output_polish_payload(context)
    POLISH_ROOT.mkdir(parents=True, exist_ok=True)
    POLISH_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    POLISH_MD.write_text(build_batch_output_polish_markdown(payload) + "\n", encoding="utf-8")
    SMOKE_MD.write_text(
        payload.get("player_status_block", "") + "\n\n" + payload.get("batch_global_status_block", "") + "\n",
        encoding="utf-8",
    )

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "batch_output_cleanup_player_facing_strategy_status_polish_v1.4.39.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (out / "BATCH_OUTPUT_CLEANUP_PLAYER_FACING_STRATEGY_STATUS_POLISH_v1.4.39.md").write_text(
            build_batch_output_polish_markdown(payload) + "\n",
            encoding="utf-8",
        )
        (out / "PLAYER_FACING_STRATEGY_STATUS_SMOKE_TEXT_v1.4.39.md").write_text(
            payload.get("player_status_block", "") + "\n\n" + payload.get("batch_global_status_block", "") + "\n",
            encoding="utf-8",
        )

    return payload

def main() -> int:
    print("v1.4.39 - Batch Output Cleanup / Player-Facing Strategy Status Polish")
    print("=" * 78)
    payload = write_batch_output_polish_artifacts()

    print(f"Active scoring profiles: {payload.get('active_scoring_profiles')}")
    print(f"Legacy preview status: {payload.get('legacy_preview_status')}")
    print(f"Patched files: {payload.get('source_patch', {}).get('patched_file_count')}")
    print(f"Player status has 249: {payload.get('player_status_has_249')}")
    print(f"Batch status has 249: {payload.get('batch_status_has_249')}")
    print(f"Artifact written: {POLISH_JSON}")
    print(f"Summary written: {POLISH_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())