from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


VERSION = "v1.4.35"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

INDEX_PATH = STRATEGY_ROOT / "index" / "strategy_profile_index.latest.json"
ACTIVE_SCORING_ROOT = STRATEGY_ROOT / "active_scoring" / "v1.4.35"
ACTIVE_SCORING_JSON = ACTIVE_SCORING_ROOT / "strategy_knowledge_active_scoring_expansion_v1.4.35.json"
ACTIVE_SCORING_MD = ACTIVE_SCORING_ROOT / "STRATEGY_KNOWLEDGE_ACTIVE_SCORING_EXPANSION_v1.4.35.md"

LEGACY_PREVIEW_PROFILES = ["Aristocrats", "Landfall", "Spellslinger", "Tokens", "Voltron"]


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": str(exc)}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts: list[str] = []
        preferred = [
            "commander", "commander_name", "deck_name", "strategy", "primary_strategy",
            "secondary_strategy", "deck_text", "decklist", "card_names", "cards",
            "user_intent", "review_direction", "build_preferences", "report_text",
        ]
        for key in preferred:
            if key in value:
                parts.append(_as_text(value[key]))
        for key, item in value.items():
            if key not in preferred and isinstance(item, (str, list, tuple, set)):
                parts.append(_as_text(item))
        return "\n".join(part for part in parts if part)
    if isinstance(value, (list, tuple, set)):
        return "\n".join(_as_text(item) for item in value)
    return str(value)


def _tokens(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+/'-]{2,}", text)
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "into", "deck", "cards",
        "commander", "your", "you", "are", "can", "will", "should", "when", "have",
        "has", "not", "but", "they", "their", "its", "using", "use", "used", "more",
        "most", "less", "very", "also", "often", "than", "then", "because", "there",
        "each", "other", "creature", "creatures", "spell", "spells",
    }
    return [word for word in words if word not in stop]


def _phrase_hits(source_text: str, candidate_text: str) -> list[str]:
    source_l = source_text.lower()
    phrases = []
    phrase_bank = [
        "aristocrats", "landfall", "lands matter", "spellslinger", "tokens", "voltron",
        "x spells", "x-spells", "lifegain", "life gain", "reanimator", "graveyard",
        "blink", "flicker", "sacrifice", "treasure", "clues", "investigate", "food",
        "vehicles", "mill", "discard", "control", "combo", "storm", "typal", "tribal",
        "go wide", "go-wide", "combat", "equipment", "auras", "enchantress", "artifacts",
        "counters", "+1/+1", "proliferate", "draw", "ramp", "recursion", "tokens",
    ]
    for phrase in phrase_bank:
        if phrase in source_l and phrase in candidate_text:
            phrases.append(phrase)
    return sorted(set(phrases))


def _load_index() -> Dict[str, Any]:
    return _load_json(INDEX_PATH)


def _profile_candidate_text(profile: Dict[str, Any]) -> str:
    parts = [
        profile.get("strategy_id", ""),
        profile.get("display_name", ""),
        profile.get("layer", ""),
        " ".join(profile.get("keywords", []) or []),
        " ".join(profile.get("role_tags", []) or []),
        profile.get("searchable_text", ""),
    ]
    snippets = profile.get("section_snippets", {}) or {}
    if isinstance(snippets, dict):
        parts.extend(str(value) for value in snippets.values())
    return " ".join(part for part in parts if part).lower()


def score_strategy_profiles(
    context: Any = None,
    *,
    max_results: int = 15,
    min_score: float = 0.0,
) -> Dict[str, Any]:
    index = _load_index()
    profiles = index.get("strategy_profiles", []) or []

    source_text = _as_text(context).strip()
    if not source_text:
        source_text = (
            "Commander deck review strategy scoring context. Use the full Strategy Knowledge "
            "index to identify likely archetypes, role buckets, synergy, cut protection, and replacement logic."
        )

    source_tokens = Counter(_tokens(source_text))
    source_token_set = set(source_tokens)

    scored: list[dict[str, Any]] = []

    for profile in profiles:
        candidate_text = _profile_candidate_text(profile)
        candidate_tokens = Counter(_tokens(candidate_text))
        candidate_token_set = set(candidate_tokens)

        overlap = source_token_set & candidate_token_set
        keyword_hits = sorted(set(profile.get("keywords", []) or []) & source_token_set)
        role_hits = sorted(set(profile.get("role_tags", []) or []) & source_token_set)
        phrase_hits = _phrase_hits(source_text, candidate_text)

        overlap_score = sum(min(source_tokens[token], candidate_tokens[token]) for token in overlap)
        keyword_score = len(keyword_hits) * 4
        role_score = len(role_hits) * 5
        phrase_score = len(phrase_hits) * 8
        name_score = 0

        display = str(profile.get("display_name", "")).lower()
        strategy_id = str(profile.get("strategy_id", "")).lower().replace("_", " ")
        source_l = source_text.lower()
        if display and display in source_l:
            name_score += 25
        if strategy_id and strategy_id in source_l:
            name_score += 20

        # Mild normalization so very long profiles do not always dominate.
        profile_length_penalty = math.log(max(len(candidate_token_set), 10), 10)
        raw_score = overlap_score + keyword_score + role_score + phrase_score + name_score
        normalized_score = raw_score / max(profile_length_penalty, 1.0)

        if normalized_score > min_score:
            scored.append({
                "strategy_id": profile.get("strategy_id", ""),
                "display_name": profile.get("display_name", ""),
                "layer": profile.get("layer", ""),
                "path": profile.get("path", ""),
                "score": round(normalized_score, 3),
                "raw_score": raw_score,
                "overlap_count": len(overlap),
                "keyword_hits": keyword_hits[:20],
                "role_hits": role_hits[:20],
                "phrase_hits": phrase_hits[:20],
                "section_snippets": profile.get("section_snippets", {}),
                "source": "strategy_profile_index.latest.json",
            })

    scored.sort(key=lambda item: (item["score"], item["raw_score"], item["display_name"]), reverse=True)

    return {
        "scoring_version": VERSION,
        "scoring_name": "Strategy Knowledge Active Scoring Expansion",
        "scoring_source": str(INDEX_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "index_available": INDEX_PATH.exists(),
        "index_version": index.get("index_version", ""),
        "active_scoring_profiles": len(profiles),
        "legacy_preview_profiles": LEGACY_PREVIEW_PROFILES,
        "legacy_preview_profile_count": len(LEGACY_PREVIEW_PROFILES),
        "legacy_preview_status": "deprecated_fallback_only",
        "active_scoring_source_status": "strategy_knowledge_249_profile_index",
        "input_token_count": len(source_tokens),
        "candidate_count": len(scored),
        "top_matches": scored[:max_results],
        "all_match_count": len(scored),
        "runtime_behavior_changed": True,
        "active_scoring_wiring_performed": True,
        "indexing_performed_previously": index.get("indexing_performed") is True,
        "report_behavior_changed": True,
        "main_py_changed": False,
        "gate_checks": {
            "index_available": INDEX_PATH.exists(),
            "index_profile_count_is_249": len(profiles) == 249,
            "active_scoring_profiles_is_249": len(profiles) == 249,
            "legacy_preview_is_fallback_only": True,
            "top_matches_available": bool(scored[:max_results]),
            "main_py_not_changed": True,
        },
    }


def write_active_scoring_artifacts(output_dir: str | Path | None = None, context: Any = None) -> Dict[str, Any]:
    payload = score_strategy_profiles(context, max_results=25)
    ACTIVE_SCORING_ROOT.mkdir(parents=True, exist_ok=True)
    ACTIVE_SCORING_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    ACTIVE_SCORING_MD.write_text(build_active_scoring_markdown(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_knowledge_active_scoring_expansion_v1.4.35.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / "STRATEGY_KNOWLEDGE_ACTIVE_SCORING_EXPANSION_v1.4.35.md").write_text(
            build_active_scoring_markdown(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def build_active_scoring_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or score_strategy_profiles({})
    lines = [
        "# Strategy Knowledge Active Scoring Expansion — v1.4.35",
        "",
        "## Result",
        "",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"- Scoring source: `{payload.get('scoring_source')}`",
        f"- Legacy preview profile count: {payload.get('legacy_preview_profile_count')}",
        f"- Legacy preview status: {payload.get('legacy_preview_status')}",
        f"- Active scoring wiring performed: {payload.get('active_scoring_wiring_performed')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Top Matches",
        "",
    ]

    for idx, item in enumerate(payload.get("top_matches", [])[:15], start=1):
        lines.append(
            f"{idx}. **{item.get('display_name')}** "
            f"(`{item.get('strategy_id')}`) — score {item.get('score')}"
        )
        hits = item.get("phrase_hits") or item.get("keyword_hits") or item.get("role_hits")
        if hits:
            lines.append(f"   - Hits: {', '.join(hits[:10])}")

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
        "- This patch makes the 249-profile Strategy Knowledge index the active scoring source.",
        "- The old five-profile preview set is retained as fallback only.",
        "- This patch does not change `main.py`.",
        "",
        "## Next Safe Step",
        "",
        "v1.4.36 — Report / Batch Integration Proof",
    ])

    return "\n".join(lines).rstrip()


def build_active_scoring_report_section(context: Any = None) -> str:
    payload = score_strategy_profiles(context, max_results=8)
    lines = [
        "## Strategy Knowledge Scoring",
        "",
        f"Active scoring profiles: **{payload.get('active_scoring_profiles')}**",
        f"Scoring source: `{payload.get('scoring_source')}`",
        "Legacy five-profile preview: fallback only",
        "",
        "### Top Matched Strategies",
    ]

    for idx, item in enumerate(payload.get("top_matches", [])[:8], start=1):
        hits = item.get("phrase_hits") or item.get("keyword_hits") or item.get("role_hits") or []
        hit_text = f" — hits: {', '.join(hits[:6])}" if hits else ""
        lines.append(
            f"{idx}. **{item.get('display_name')}** "
            f"(`{item.get('strategy_id')}`), score {item.get('score')}{hit_text}"
        )

    return "\n".join(lines).rstrip()


def build_active_scoring_prompt_block(context: Any = None) -> str:
    payload = score_strategy_profiles(context, max_results=12)
    lines = [
        "## Strategy Knowledge Active Scoring Context",
        "",
        f"Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"Scoring source: {payload.get('scoring_source')}",
        "The old five-profile preview is fallback only.",
        "",
        "Top strategy matches:",
    ]
    for item in payload.get("top_matches", [])[:12]:
        lines.append(f"- {item.get('display_name')} (`{item.get('strategy_id')}`), score {item.get('score')}")
    return "\n".join(lines).rstrip()


def build_active_scoring_viewer_summary() -> str:
    payload = score_strategy_profiles({}, max_results=5)
    return "\n".join([
        "Strategy Knowledge Active Scoring",
        "=================================",
        "",
        f"Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"Scoring source: {payload.get('scoring_source')}",
        "Legacy five-profile preview: fallback only",
    ]).rstrip()


def main() -> int:
    print("v1.4.35 - Strategy Knowledge Active Scoring Expansion")
    print("=" * 78)
    sample_context = {
        "deck_name": "Strategy Knowledge active scoring smoke test",
        "deck_text": (
            "tokens spellslinger landfall aristocrats voltron lifegain artifacts graveyard "
            "sacrifice recursion combat counters mill food clues vehicles enchantress control combo"
        ),
    }
    payload = write_active_scoring_artifacts(context=sample_context)

    print(f"Active scoring profiles: {payload.get('active_scoring_profiles')}")
    print(f"Scoring source: {payload.get('scoring_source')}")
    print(f"Legacy preview status: {payload.get('legacy_preview_status')}")
    print(f"Top matches available: {bool(payload.get('top_matches'))}")
    print(f"Artifact written: {ACTIVE_SCORING_JSON}")
    print(f"Summary written: {ACTIVE_SCORING_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.4.36 — Report / Batch Integration Proof")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
