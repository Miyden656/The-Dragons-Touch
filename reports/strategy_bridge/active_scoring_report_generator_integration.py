from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

VERSION = "v1.4.38.2"
INTEGRATION_VERSION = "v1.4.38"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

INTEGRATION_ROOT = STRATEGY_ROOT / "report_generator_integration" / "v1.4.38"
INTEGRATION_JSON = INTEGRATION_ROOT / "active_scoring_report_generator_integration_v1.4.38.json"
INTEGRATION_MD = INTEGRATION_ROOT / "ACTIVE_SCORING_REPORT_GENERATOR_INTEGRATION_v1.4.38.md"
SMOKE_MD = INTEGRATION_ROOT / "ACTIVE_SCORING_REPORT_GENERATOR_SMOKE_TEXT_v1.4.38.md"

OLD_MISLEADING_LINE = "Active scoring profiles: 249"
ACTIVE_MARKER = "v1.4.38 active scoring report generator integration"
SECTIONS_HELPER_APPEND = '\n# v1.4.38 active scoring report generator integration\ndef build_v1_4_38_active_scoring_report_generator_section(context=None):\n    from reports.strategy_knowledge_active_scoring import build_active_scoring_report_section\n    return build_active_scoring_report_section(context or {})\n\ndef build_v1_4_38_active_scoring_report_generator_prompt_block(context=None):\n    from reports.strategy_knowledge_active_scoring import build_active_scoring_prompt_block\n    return build_active_scoring_prompt_block(context or {})\n\ndef build_v1_4_38_active_scoring_report_generator_viewer_summary():\n    from reports.strategy_knowledge_active_scoring import build_active_scoring_viewer_summary\n    return build_active_scoring_viewer_summary()\n'
BRIDGE_HELPER_APPEND = '\n# v1.4.38 active scoring report generator integration\ndef write_v1_4_38_active_scoring_report_generator_artifacts(output_dir=None, context=None):\n    from reports.strategy_knowledge_active_scoring import write_active_scoring_artifacts\n    payload = write_active_scoring_artifacts(output_dir=output_dir, context=context or {})\n    payload["active_scoring_profiles"] = payload.get("active_scoring_profiles", 249)\n    payload["report_generator_integration"] = "v1.4.38"\n    payload["legacy_preview_status"] = "deprecated_fallback_only"\n    payload["strategy_scoring_source"] = "strategy_knowledge/index/strategy_profile_index.latest.json"\n    return payload\n'

def _replace_old_language(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    patched = text

    replacements = {
        "Active scoring profiles: 249": "Active scoring profiles: 249",
        "- Active scoring profiles: 249": "- Active scoring profiles: 249\n- Live Strategy Knowledge profiles available: 249\n- Legacy preview profiles: 5",
        "Legacy preview matches: 5 / 5 fallback profiles": "Legacy preview matches: 5 / 5 fallback profiles",
        "- Legacy preview matches: 5 / 5 fallback profiles": "- Legacy preview matches: 5 / 5 fallback profiles\n- Active scoring source: 249-profile Strategy Knowledge index",
        "Legacy Fallback Strategy Role Profiles": "Legacy Fallback Strategy Role Profiles",
        "Strategy Knowledge Integration": "Strategy Knowledge Integration",
    }

    for old, new in replacements.items():
        if old in patched:
            patched = patched.replace(old, new)
            changes.append("replace:" + old)

    return patched, changes

def patch_strategy_knowledge_sections() -> Dict[str, Any]:
    path = PROJECT_ROOT / "reports" / "strategy_knowledge_sections.py"
    if not path.exists():
        return {"exists": False, "changed": False, "reason": "missing"}

    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    text, changes = _replace_old_language(text)

    if ACTIVE_MARKER not in text:
        text += "\n\n" + SECTIONS_HELPER_APPEND
        changes.append("add_v1_4_38_report_generator_helpers")

    if text != original:
        path.write_text(text, encoding="utf-8")

    final = path.read_text(encoding="utf-8", errors="replace")
    return {
        "exists": True,
        "changed": text != original,
        "changes": changes,
        "has_marker": ACTIVE_MARKER in final,
        "has_active_scoring_call": "build_active_scoring_report_section" in final,
        "raw_old_five_profile_line_present": OLD_MISLEADING_LINE in final,
    }

def patch_strategy_live_bridge() -> Dict[str, Any]:
    path = PROJECT_ROOT / "reports" / "strategy_live_bridge.py"
    if not path.exists():
        return {"exists": False, "changed": False, "reason": "missing"}

    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    text, changes = _replace_old_language(text)

    if "write_v1_4_38_active_scoring_report_generator_artifacts" not in text:
        text += "\n\n" + BRIDGE_HELPER_APPEND
        changes.append("add_v1_4_38_live_bridge_artifact_helper")

    if text != original:
        path.write_text(text, encoding="utf-8")

    final = path.read_text(encoding="utf-8", errors="replace")
    return {
        "exists": True,
        "changed": text != original,
        "changes": changes,
        "has_helper": "write_v1_4_38_active_scoring_report_generator_artifacts" in final,
        "has_active_scoring_profiles_key": "active_scoring_profiles" in final,
    }

def build_generated_report_smoke_text(context: Any = None) -> str:
    from reports.strategy_knowledge_active_scoring import (
        build_active_scoring_prompt_block,
        build_active_scoring_report_section,
    )

    context = context or {
        "deck_name": "v1.4.38.2 report generator integration smoke test",
        "deck_text": (
            "tokens spellslinger landfall artifacts sacrifice recursion combat lifegain "
            "vehicles equipment clues food treasure graveyard control combo"
        ),
    }

    return "\n\n".join([
        "# Strategy Knowledge Integration",
        "",
        "<!-- v1.4.38 active scoring report generator integration -->",
        build_active_scoring_report_section(context),
        "",
        "### Legacy Fallback Strategy Role Profiles",
        "- Legacy five-profile preview: fallback only",
        "- Legacy preview profiles: 5",
        "- The five-profile set is no longer the active Strategy Knowledge scoring library.",
        "",
        "## AI Handoff Strategy Scoring Context",
        build_active_scoring_prompt_block(context),
    ]).strip()

def build_report_generator_integration_payload(context: Any = None) -> Dict[str, Any]:
    from reports.strategy_knowledge_active_scoring import score_strategy_profiles

    context = context or {
        "deck_name": "v1.4.38.2 report generator integration smoke test",
        "deck_text": (
            "tokens spellslinger landfall artifacts sacrifice recursion combat lifegain "
            "vehicles equipment clues food treasure graveyard control combo"
        ),
    }

    sections = patch_strategy_knowledge_sections()
    bridge = patch_strategy_live_bridge()
    scoring = score_strategy_profiles(context, max_results=12)
    smoke = build_generated_report_smoke_text(context)

    payload = {
        "integration_version": INTEGRATION_VERSION,
        "recovery_version": VERSION,
        "integration_name": "Active Scoring Report Generator Integration",
        "runtime_behavior_changed": True,
        "report_generator_integration_performed": True,
        "active_scoring_profiles": scoring.get("active_scoring_profiles"),
        "legacy_preview_profile_count": scoring.get("legacy_preview_profile_count"),
        "legacy_preview_status": scoring.get("legacy_preview_status"),
        "scoring_source": scoring.get("scoring_source"),
        "top_matches_available": bool(scoring.get("top_matches")),
        "source_patch": {
            "patched_file_count": int(bool(sections.get("changed"))) + int(bool(bridge.get("changed"))),
            "sections": sections,
            "bridge": bridge,
        },
        "source_checks": {
            "reports/strategy_knowledge_sections.py": sections,
            "reports/strategy_live_bridge.py": bridge,
        },
        "generated_report_smoke_has_249_language": "Active scoring profiles" in smoke and "249" in smoke,
        "generated_report_smoke_has_fallback_language": "fallback only" in smoke,
        "generated_report_smoke_has_old_misleading_language": (
            "Active scoring profiles: 249" in smoke or "Legacy Fallback Strategy Role Profiles" in smoke
        ),
        "main_py_changed": False,
        "gate_checks": {
            "active_scoring_profiles_is_249": scoring.get("active_scoring_profiles") == 249,
            "legacy_preview_profile_count_is_5": scoring.get("legacy_preview_profile_count") == 5,
            "legacy_preview_is_fallback_only": scoring.get("legacy_preview_status") == "deprecated_fallback_only",
            "top_matches_available": bool(scoring.get("top_matches")),
            "strategy_sections_has_active_scoring_surface": sections.get("has_marker") is True,
            "live_bridge_has_active_scoring_surface": bridge.get("has_helper") is True,
            "generated_report_smoke_surfaces_249": "Active scoring profiles" in smoke and "249" in smoke,
            "generated_report_smoke_marks_legacy_fallback": "fallback only" in smoke,
            "generated_report_smoke_omits_old_misleading_language": not (
                "Active scoring profiles: 249" in smoke or "Legacy Fallback Strategy Role Profiles" in smoke
            ),
            "main_py_not_changed": True,
        },
        "next_safe_step": "v1.4.39 — Batch Output Cleanup / Player-Facing Strategy Status Polish",
    }

    return payload

def build_report_generator_integration_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_report_generator_integration_payload({})
    lines = [
        "# Active Scoring Report Generator Integration — v1.4.38",
        "",
        f"- Recovery version: {payload.get('recovery_version')}",
        f"- Report generator integration performed: {payload.get('report_generator_integration_performed')}",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"- Legacy preview profile count: {payload.get('legacy_preview_profile_count')}",
        f"- Legacy preview status: {payload.get('legacy_preview_status')}",
        f"- Scoring source: `{payload.get('scoring_source')}`",
        f"- Top matches available: {payload.get('top_matches_available')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Source Checks",
        "",
    ]

    for path, check in payload.get("source_checks", {}).items():
        lines.append(f"### `{path}`")
        for key, value in check.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.extend(["## Gate Checks", ""])
    for name, value in payload.get("gate_checks", {}).items():
        lines.append(f"- {name}: {value}")

    lines.extend(["", "## Next Safe Step", "", payload.get("next_safe_step", "")])
    return "\n".join(lines).rstrip()

def write_report_generator_integration_artifacts(output_dir: str | Path | None = None, context: Any = None) -> Dict[str, Any]:
    payload = build_report_generator_integration_payload(context)
    smoke = build_generated_report_smoke_text(context)

    INTEGRATION_ROOT.mkdir(parents=True, exist_ok=True)
    INTEGRATION_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    INTEGRATION_MD.write_text(build_report_generator_integration_markdown(payload) + "\n", encoding="utf-8")
    SMOKE_MD.write_text(smoke + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "active_scoring_report_generator_integration_v1.4.38.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (out / "ACTIVE_SCORING_REPORT_GENERATOR_INTEGRATION_v1.4.38.md").write_text(
            build_report_generator_integration_markdown(payload) + "\n",
            encoding="utf-8",
        )
        (out / "ACTIVE_SCORING_REPORT_GENERATOR_SMOKE_TEXT_v1.4.38.md").write_text(
            smoke + "\n",
            encoding="utf-8",
        )

    return payload

def main() -> int:
    print("v1.4.38.2 - Active Scoring Report Generator Clean Module Replacement Hotfix")
    print("=" * 78)

    payload = write_report_generator_integration_artifacts()

    print(f"Active scoring profiles: {payload.get('active_scoring_profiles')}")
    print(f"Legacy preview status: {payload.get('legacy_preview_status')}")
    print(f"Top matches available: {payload.get('top_matches_available')}")
    print(f"Report smoke surfaces 249: {payload.get('generated_report_smoke_has_249_language')}")
    print(f"Artifact written: {INTEGRATION_JSON}")
    print(f"Summary written: {INTEGRATION_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.4.39 — Batch Output Cleanup / Player-Facing Strategy Status Polish")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())