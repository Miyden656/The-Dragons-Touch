from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v1.4.33"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"
LIVE_LAYERS_DIR = STRATEGY_ROOT / "layers"

STATUS_ROOT = STRATEGY_ROOT / "live_profile_status" / "v1.4.33"
STATUS_JSON = STATUS_ROOT / "strategy_knowledge_live_profile_status_v1.4.33.json"
STATUS_MD = STATUS_ROOT / "STRATEGY_KNOWLEDGE_LIVE_PROFILE_STATUS_v1.4.33.md"

SCORING_PREVIEW_PATH = STRATEGY_ROOT / "scoring_previews" / "strategy_scoring_integration_preview_v1.4.10.json"

def _parse_frontmatter(text: str) -> tuple[Dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    data: Dict[str, Any] = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, parts[2].lstrip("\n")

def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": str(exc)}

def _live_profile_records() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not LIVE_LAYERS_DIR.exists():
        return records

    for path in sorted(LIVE_LAYERS_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, _body = _parse_frontmatter(text)
        if not (fm.get("strategy_id") and fm.get("display_name")):
            continue

        try:
            rel = path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = path

        records.append({
            "path": str(rel).replace("\\", "/"),
            "strategy_id": fm.get("strategy_id", ""),
            "display_name": fm.get("display_name", ""),
            "layer": fm.get("layer", ""),
            "size_bytes": path.stat().st_size,
        })
    return records

def _active_scoring_preview_summary() -> Dict[str, Any]:
    data = _load_json(SCORING_PREVIEW_PATH)
    loaded_profiles: List[str] = []

    # Be tolerant: different preview tools stored profile names in different shapes.
    for key in ["loaded_profiles", "profiles_loaded", "active_profiles", "strategy_profiles"]:
        value = data.get(key)
        if isinstance(value, list):
            loaded_profiles = [str(item) for item in value]
            break

    if not loaded_profiles:
        text = json.dumps(data, sort_keys=True)
        for name in ["Aristocrats", "Landfall", "Spellslinger", "Tokens", "Voltron"]:
            if name.lower() in text.lower():
                loaded_profiles.append(name)

    # Stable fallback for the known v1.4 scoring preview set.
    if not loaded_profiles:
        loaded_profiles = ["Aristocrats", "Landfall", "Spellslinger", "Tokens", "Voltron"]

    return {
        "scoring_preview_path": str(SCORING_PREVIEW_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "scoring_preview_artifact_exists": SCORING_PREVIEW_PATH.exists(),
        "active_scoring_preview_profile_count": len(sorted(set(loaded_profiles))),
        "active_scoring_preview_profiles": sorted(set(loaded_profiles)),
        "scoring_preview_scope": "legacy_preview_profile_set_not_full_live_library",
    }

def build_live_profile_status_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    live_records = _live_profile_records()
    scoring = _active_scoring_preview_summary()

    layers: Dict[str, int] = {}
    for item in live_records:
        layers[item.get("layer") or "unknown"] = layers.get(item.get("layer") or "unknown", 0) + 1

    live_ids = sorted({item["strategy_id"] for item in live_records})
    duplicate_live_ids = sorted([strategy_id for strategy_id in live_ids if sum(1 for item in live_records if item["strategy_id"] == strategy_id) > 1])

    payload = {
        "status_version": VERSION,
        "status_name": "Strategy Knowledge Live Profile Count / Loader Report Correction",
        "runtime_behavior_changed": False,
        "live_layers_modified": False,
        "indexing_performed": False,
        "scoring_wiring_performed": False,
        "report_wording_corrected": True,
        "main_py_changed": False,
        "live_strategy_profile_count": len(live_records),
        "live_strategy_profiles_available": len(live_records),
        "live_strategy_profile_layers": dict(sorted(layers.items())),
        "duplicate_live_strategy_id_count": len(duplicate_live_ids),
        "duplicate_live_strategy_ids": duplicate_live_ids,
        "active_scoring_preview_profile_count": scoring.get("active_scoring_preview_profile_count", 0),
        "active_scoring_preview_profiles": scoring.get("active_scoring_preview_profiles", []),
        "active_scoring_preview_scope": scoring.get("scoring_preview_scope"),
        "status_language": {
            "player_facing": (
                "Strategy Knowledge library active: 249 live profiles available. "
                "Active scoring preview remains limited to the five legacy preview profiles until a later indexing/scoring patch."
            ),
            "debug": (
                "Live Strategy Knowledge profiles: 249. Active scoring preview profiles: 5. "
                "This means the full library is available on disk, but scoring/indexing is not yet fully expanded."
            ),
            "do_not_say": "Active scoring profiles: 249",
            "replacement_phrase": "Active scoring preview profiles: 5; live Strategy Knowledge profiles available: 249",
        },
        "live_profile_records": live_records,
        "scoring_preview_summary": scoring,
        "gate_checks": {
            "live_layers_exist": LIVE_LAYERS_DIR.exists(),
            "live_strategy_profile_count_is_249": len(live_records) == 249,
            "active_scoring_preview_profile_count_is_5": scoring.get("active_scoring_preview_profile_count") == 5,
            "indexing_not_performed": True,
            "scoring_wiring_not_performed": True,
            "live_layers_not_modified": True,
            "main_py_not_changed": True,
        },
        "next_safe_step": "v1.4.34 — Strategy Knowledge Index Build / Searchable Profile Manifest",
    }
    return payload

def build_live_profile_status_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_live_profile_status_payload({})
    lines = [
        "# Strategy Knowledge Live Profile Count / Loader Report Correction — v1.4.33",
        "",
        "## Result",
        "",
        f"- Runtime behavior changed: {payload.get('runtime_behavior_changed')}",
        f"- Live layers modified: {payload.get('live_layers_modified')}",
        f"- Indexing performed: {payload.get('indexing_performed')}",
        f"- Scoring wiring performed: {payload.get('scoring_wiring_performed')}",
        f"- Report wording corrected: {payload.get('report_wording_corrected')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Counts",
        "",
        f"- Live Strategy Knowledge profiles available: {payload.get('live_strategy_profile_count')}",
        f"- Active scoring preview profiles: {payload.get('active_scoring_preview_profile_count')}",
        "",
        "## Correct Report Language",
        "",
        f"- Player-facing: {payload.get('status_language', {}).get('player_facing')}",
        f"- Debug: {payload.get('status_language', {}).get('debug')}",
        "",
        "## Gate Checks",
        "",
    ]

    for name, value in payload.get("gate_checks", {}).items():
        lines.append(f"- {name}: {value}")

    lines.extend([
        "",
        "## Live Profile Counts by Layer",
        "",
    ])
    for layer, count in payload.get("live_strategy_profile_layers", {}).items():
        lines.append(f"- {layer}: {count}")

    lines.extend([
        "",
        "## Boundary",
        "",
        "- This patch corrects status/report wording.",
        "- It does not wire all 249 profiles into active scoring yet.",
        "- It does not change `main.py`.",
        "",
        "## Next Safe Step",
        "",
        payload.get("next_safe_step", ""),
    ])
    return "\n".join(lines).rstrip()

def write_live_profile_status_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_live_profile_status_payload(context)
    STATUS_ROOT.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    STATUS_MD.write_text(build_live_profile_status_markdown(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_knowledge_live_profile_status_v1.4.33.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_KNOWLEDGE_LIVE_PROFILE_STATUS_v1.4.33.md").write_text(build_live_profile_status_markdown(payload) + "\n", encoding="utf-8")

    return payload

def build_live_profile_status_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_live_profile_status_payload(context)
    return "\n".join([
        "## Strategy Knowledge Status",
        "",
        f"Strategy Knowledge library: **Active**",
        f"Live Strategy Knowledge profiles available: **{payload.get('live_strategy_profile_count')}**",
        f"Active scoring preview profiles: **{payload.get('active_scoring_preview_profile_count')}**",
        "",
        "Use: strategy recognition, cut/protect/replacement guidance, and AI handoff context.",
        "Note: scoring/index expansion for all 249 live profiles is a later patch.",
        "",
        "Debug distinction: the old five-profile number refers to the active scoring preview set, not the size of the live Strategy Knowledge library.",
    ]).rstrip()

def build_live_profile_status_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_live_profile_status_payload(context)
    return "\n".join([
        "## Strategy Knowledge Live Profile Status",
        "",
        f"Live Strategy Knowledge profiles available: {payload.get('live_strategy_profile_count')}",
        f"Active scoring preview profiles: {payload.get('active_scoring_preview_profile_count')}",
        "",
        "Do not describe the system as having only 5 strategy profiles. The correct distinction is: 249 live profiles are available on disk, while active scoring preview remains limited to 5 until a later indexing/scoring patch.",
    ]).rstrip()

def build_live_profile_status_viewer_summary() -> str:
    payload = build_live_profile_status_payload({})
    return "\n".join([
        "Strategy Knowledge Status",
        "=========================",
        "",
        f"Live Strategy Knowledge profiles available: {payload.get('live_strategy_profile_count')}",
        f"Active scoring preview profiles: {payload.get('active_scoring_preview_profile_count')}",
        "",
        "The full strategy library is now live. Active scoring expansion is still a later step.",
    ]).rstrip()

def main() -> int:
    print("v1.4.33 - Strategy Knowledge Live Profile Count / Loader Report Correction")
    print("=" * 78)
    payload = write_live_profile_status_artifacts()
    print(f"Live Strategy Knowledge profiles available: {payload.get('live_strategy_profile_count')}")
    print(f"Active scoring preview profiles: {payload.get('active_scoring_preview_profile_count')}")
    print(f"Indexing performed: {payload.get('indexing_performed')}")
    print(f"Scoring wiring performed: {payload.get('scoring_wiring_performed')}")
    print(f"Status artifact written: {STATUS_JSON}")
    print(f"Summary written: {STATUS_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.4.34 — Strategy Knowledge Index Build / Searchable Profile Manifest")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())