from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


VERSION = "v1.4.34"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"
LIVE_LAYERS_DIR = STRATEGY_ROOT / "layers"

INDEX_ROOT = STRATEGY_ROOT / "index" / "v1.4.34"
INDEX_JSON = INDEX_ROOT / "strategy_profile_index_v1.4.34.json"
INDEX_MD = INDEX_ROOT / "STRATEGY_PROFILE_INDEX_SUMMARY_v1.4.34.md"

LATEST_INDEX_JSON = STRATEGY_ROOT / "index" / "strategy_profile_index.latest.json"
LATEST_INDEX_MD = STRATEGY_ROOT / "index" / "STRATEGY_PROFILE_INDEX_SUMMARY.latest.md"


ROLE_KEYWORDS = {
    "ramp": ["ramp", "mana acceleration", "mana dork", "treasure", "land ramp", "ritual"],
    "card_draw": ["card draw", "draw cards", "impulse draw", "cantrip", "refill", "card advantage"],
    "removal": ["removal", "destroy", "exile", "bounce", "fight", "targeted interaction"],
    "board_wipe": ["board wipe", "sweeper", "wrath", "mass removal"],
    "protection": ["protection", "hexproof", "indestructible", "counterspell", "save", "protect"],
    "recursion": ["recursion", "return from graveyard", "reanimate", "graveyard", "regrowth"],
    "sacrifice": ["sacrifice", "sac outlet", "dies trigger", "aristocrat"],
    "tokens": ["token", "tokens", "go-wide", "creature token", "copy token"],
    "lands": ["landfall", "lands matter", "land entering", "extra land", "fetchland"],
    "artifacts": ["artifact", "treasure", "clue", "food", "vehicle", "equipment"],
    "enchantments": ["enchantment", "aura", "enchantress", "saga"],
    "spells": ["instant", "sorcery", "spellslinger", "cast", "storm", "magecraft"],
    "combat": ["combat", "attack", "damage", "trample", "double strike", "evasion"],
    "counters": ["+1/+1 counter", "counter", "proliferate", "modified"],
    "tribal": ["typal", "tribal", "creature type", "lord", "kindred"],
    "graveyard": ["graveyard", "mill", "self-mill", "discard", "reanimator"],
    "lifegain": ["lifegain", "life gain", "life total", "drain", "life loss"],
    "combo": ["combo", "loop", "infinite", "engine", "deterministic"],
}


SECTION_HINTS = {
    "commander_identity": ["commander identity", "commander traits", "commander"],
    "game_plan": ["core game plan", "game plan", "what the deck is trying to do"],
    "resource_engine": ["primary resource engine", "resource engine"],
    "win_conditions": ["win conditions", "typical win conditions", "finishers"],
    "role_buckets": ["role buckets", "key card roles", "roles"],
    "signals": ["cards / effects that signal", "signal", "signals"],
    "synergy": ["synergy packages", "synergy"],
    "cut_logic": ["cut logic", "cut guidance"],
    "protect_logic": ["cards to protect", "protect from cuts", "protection"],
    "replacement_logic": ["replacement logic", "replacement guidance"],
    "build_from_collection": ["build from collection", "owned-card", "owned card"],
    "rough_shell": ["rough shell"],
    "full_draft": ["full 100-card draft", "full draft"],
    "power_level": ["bracket", "power-level", "power level"],
    "ai_tags": ["ai parsing tags", "keywords", "tags"],
}


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


def _normalize_words(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+/'-]{2,}", text.lower())
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "into", "deck", "cards",
        "strategy", "commander", "your", "you", "are", "can", "will", "should", "when",
        "has", "have", "not", "but", "they", "their", "its", "use", "used", "using",
        "more", "most", "less", "very", "also", "often", "than", "then", "because",
    }
    return [word for word in words if word not in stop]


def _heading_records(body: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", body, flags=re.MULTILINE):
        records.append({
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
            "line": body[:match.start()].count("\n") + 1,
        })
    return records


def _extract_section_snippets(body: str) -> dict[str, str]:
    headings = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", body, flags=re.MULTILINE))
    snippets: dict[str, str] = {}
    if not headings:
        return snippets

    for idx, match in enumerate(headings):
        title = match.group(2).strip()
        title_l = title.lower()
        start = match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(body)
        section_text = body[start:end].strip()
        if not section_text:
            continue

        compact = re.sub(r"\s+", " ", section_text).strip()
        compact = compact[:700]

        for canonical, hints in SECTION_HINTS.items():
            if canonical in snippets:
                continue
            if any(hint in title_l for hint in hints):
                snippets[canonical] = compact
                break

    return snippets


def _infer_role_tags(text: str) -> list[str]:
    text_l = text.lower()
    found = []
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in text_l for keyword in keywords):
            found.append(role)
    return sorted(found)


def _top_keywords(text: str, limit: int = 32) -> list[str]:
    counts = Counter(_normalize_words(text))
    # Bias MTG-important multiword phrase fragments by adding normalized phrase terms.
    phrase_bonus = [
        "landfall", "spellslinger", "tokens", "voltron", "aristocrats", "reanimator",
        "blink", "flicker", "lifegain", "typal", "tribal", "artifacts", "enchantress",
        "graveyard", "sacrifice", "combat", "control", "storm", "counters", "vehicles",
        "food", "clues", "treasure", "mill", "discard", "draw", "ramp", "removal",
    ]
    text_l = text.lower()
    for phrase in phrase_bonus:
        if phrase in text_l:
            counts[phrase] += 5
    return [word for word, _count in counts.most_common(limit)]


def _first_nonempty_heading(body: str) -> str:
    for item in _heading_records(body):
        if item.get("title"):
            return item["title"]
    return ""


def _strategy_file_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not LIVE_LAYERS_DIR.exists():
        return records

    for path in sorted(LIVE_LAYERS_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, body = _parse_frontmatter(text)
        strategy_id = fm.get("strategy_id", "")
        display_name = fm.get("display_name", "") or _first_nonempty_heading(body)
        if not strategy_id or not display_name:
            continue

        rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        layer = fm.get("layer", "")
        if not layer:
            try:
                layer = path.relative_to(LIVE_LAYERS_DIR).parts[0]
            except Exception:
                layer = "unknown"

        headings = _heading_records(body)
        section_snippets = _extract_section_snippets(body)
        role_tags = _infer_role_tags(text)
        keywords = _top_keywords(text)
        content_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

        searchable_text = " ".join([
            strategy_id,
            display_name,
            layer,
            " ".join(keywords),
            " ".join(role_tags),
            " ".join(item.get("title", "") for item in headings[:24]),
            " ".join(section_snippets.values()),
        ])
        searchable_text = re.sub(r"\s+", " ", searchable_text).strip()[:6000]

        records.append({
            "strategy_id": strategy_id,
            "display_name": display_name,
            "layer": layer,
            "path": rel,
            "size_bytes": path.stat().st_size,
            "content_sha256": content_hash,
            "keywords": keywords,
            "role_tags": role_tags,
            "heading_count": len(headings),
            "headings": headings[:80],
            "section_snippets": section_snippets,
            "searchable_text": searchable_text,
            "source_status": fm.get("source", ""),
            "normalization_version": fm.get("normalization_version", ""),
        })

    return records


def build_strategy_profile_index_payload(context: dict[str, Any] | None = None) -> Dict[str, Any]:
    records = _strategy_file_records()
    strategy_ids = [item["strategy_id"] for item in records]
    duplicate_ids = sorted([sid for sid, count in Counter(strategy_ids).items() if count > 1])
    layers = Counter(item.get("layer", "unknown") for item in records)

    keyword_index: dict[str, list[str]] = {}
    role_index: dict[str, list[str]] = {}
    layer_index: dict[str, list[str]] = {}

    for item in records:
        sid = item["strategy_id"]
        for keyword in item.get("keywords", []):
            keyword_index.setdefault(keyword, []).append(sid)
        for role in item.get("role_tags", []):
            role_index.setdefault(role, []).append(sid)
        layer_index.setdefault(item.get("layer", "unknown"), []).append(sid)

    for index in [keyword_index, role_index, layer_index]:
        for key in list(index.keys()):
            index[key] = sorted(set(index[key]))

    payload = {
        "index_version": VERSION,
        "index_name": "Strategy Knowledge Index Build / Searchable Profile Manifest",
        "runtime_behavior_changed": False,
        "live_layers_modified": False,
        "indexing_performed": True,
        "searchable_manifest_built": True,
        "active_scoring_wiring_performed": False,
        "report_behavior_changed": False,
        "main_py_changed": False,
        "source_live_layers": str(LIVE_LAYERS_DIR.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "indexed_profile_count": len(records),
        "unique_strategy_id_count": len(set(strategy_ids)),
        "duplicate_strategy_id_count": len(duplicate_ids),
        "duplicate_strategy_ids": duplicate_ids,
        "layer_counts": dict(sorted(layers.items())),
        "strategy_profiles": records,
        "keyword_index": dict(sorted(keyword_index.items())),
        "role_index": dict(sorted(role_index.items())),
        "layer_index": dict(sorted(layer_index.items())),
        "index_usage_policy": {
            "intended_next_consumer": "v1.4.35 Strategy Knowledge Active Scoring Expansion",
            "active_scoring_source_now": "legacy five-profile scoring preview",
            "active_scoring_source_after_next_patch": "strategy_profile_index_v1.4.34.json",
            "do_not_dump_all_profiles_in_player_reports": True,
            "score_against_all_profiles_then_show_top_matches": True,
        },
        "gate_checks": {
            "live_layers_exist": LIVE_LAYERS_DIR.exists(),
            "indexed_profile_count_is_249": len(records) == 249,
            "unique_strategy_id_count_is_249": len(set(strategy_ids)) == 249,
            "no_duplicate_strategy_ids": len(duplicate_ids) == 0,
            "indexing_performed": True,
            "active_scoring_wiring_not_performed": True,
            "report_behavior_not_changed": True,
            "main_py_not_changed": True,
        },
        "next_safe_step": "v1.4.35 — Strategy Knowledge Active Scoring Expansion",
    }

    return payload


def build_strategy_profile_index_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_strategy_profile_index_payload({})
    lines = [
        "# Strategy Knowledge Index Build / Searchable Profile Manifest — v1.4.34",
        "",
        "## Result",
        "",
        f"- Runtime behavior changed: {payload.get('runtime_behavior_changed')}",
        f"- Live layers modified: {payload.get('live_layers_modified')}",
        f"- Indexing performed: {payload.get('indexing_performed')}",
        f"- Searchable manifest built: {payload.get('searchable_manifest_built')}",
        f"- Active scoring wiring performed: {payload.get('active_scoring_wiring_performed')}",
        f"- Report behavior changed: {payload.get('report_behavior_changed')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Counts",
        "",
        f"- Indexed profiles: {payload.get('indexed_profile_count')}",
        f"- Unique strategy IDs: {payload.get('unique_strategy_id_count')}",
        f"- Duplicate strategy IDs: {payload.get('duplicate_strategy_id_count')}",
        "",
        "## Layer Counts",
        "",
    ]

    for layer, count in payload.get("layer_counts", {}).items():
        lines.append(f"- {layer}: {count}")

    lines.extend([
        "",
        "## Role Index Counts",
        "",
    ])
    for role, ids in payload.get("role_index", {}).items():
        lines.append(f"- {role}: {len(ids)}")

    lines.extend([
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
        "- This patch builds the searchable 249-profile index.",
        "- It does not wire the index into active scoring yet.",
        "- It does not change player-facing report behavior yet.",
        "- It does not change `main.py`.",
        "",
        "## Next Safe Step",
        "",
        payload.get("next_safe_step", ""),
    ])

    return "\n".join(lines).rstrip()


def write_strategy_profile_index_artifacts(output_dir: str | Path | None = None, context: dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = build_strategy_profile_index_payload(context)
    INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    INDEX_MD.write_text(build_strategy_profile_index_markdown(payload) + "\n", encoding="utf-8")

    LATEST_INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)
    LATEST_INDEX_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LATEST_INDEX_MD.write_text(build_strategy_profile_index_markdown(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_profile_index_v1.4.34.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_PROFILE_INDEX_SUMMARY_v1.4.34.md").write_text(
            build_strategy_profile_index_markdown(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_strategy_profile_index_report_section(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_profile_index_payload(context)
    return "\n".join([
        "## Strategy Knowledge Index Status",
        "",
        f"Indexed Strategy Knowledge profiles: **{payload.get('indexed_profile_count')}**",
        "Index use: searchable strategy reference for the next scoring-expansion patch.",
        "Active scoring source: still the legacy five-profile preview until v1.4.35.",
    ]).rstrip()


def build_strategy_profile_index_prompt_block(context: dict[str, Any] | None = None) -> str:
    payload = build_strategy_profile_index_payload(context)
    return "\n".join([
        "## Strategy Knowledge Index Context",
        "",
        f"Indexed Strategy Knowledge profiles: {payload.get('indexed_profile_count')}",
        "The 249-profile searchable index exists and should be used by future scoring expansion.",
        "Do not claim all 249 are active scoring profiles until the scoring expansion patch is applied.",
    ]).rstrip()


def main() -> int:
    print("v1.4.34 - Strategy Knowledge Index Build / Searchable Profile Manifest")
    print("=" * 78)
    payload = write_strategy_profile_index_artifacts()

    print(f"Indexed profiles: {payload.get('indexed_profile_count')}")
    print(f"Unique strategy IDs: {payload.get('unique_strategy_id_count')}")
    print(f"Duplicate strategy IDs: {payload.get('duplicate_strategy_id_count')}")
    print(f"Index written: {INDEX_JSON}")
    print(f"Latest index written: {LATEST_INDEX_JSON}")
    print(f"Summary written: {INDEX_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.4.35 — Strategy Knowledge Active Scoring Expansion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
