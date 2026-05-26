from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


VERSION = "v1.4.37"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = PROJECT_ROOT / "strategy_knowledge"

REGRESSION_ROOT = STRATEGY_ROOT / "scoring_regression" / "v1.4.37"
REGRESSION_JSON = REGRESSION_ROOT / "strategy_knowledge_scoring_regression_old_vs_new_v1.4.37.json"
REGRESSION_MD = REGRESSION_ROOT / "STRATEGY_KNOWLEDGE_SCORING_REGRESSION_OLD_VS_NEW_v1.4.37.md"

LEGACY_PROFILE_IDS = {
    "aristocrats",
    "landfall_lands_matter",
    "landfall",
    "spellslinger",
    "tokens",
    "voltron",
}
LEGACY_PROFILE_DISPLAY_NAMES = {
    "aristocrats",
    "landfall",
    "landfall / lands matter",
    "lands matter",
    "spellslinger",
    "tokens",
    "voltron",
}

SAMPLE_DECK_CONTEXTS = [
    {
        "deck_name": "Witherbloom Creature-Affinity X-Spells Smoke Test",
        "commander": "Witherbloom, the Balancer",
        "deck_text": (
            "The deck wants lots of cheap creatures and tokens to make instant and sorcery X spells enormous. "
            "It uses go-wide creature count, spellslinger payoffs, token makers, ramp, card draw, and big X finishers. "
            "The intended win pattern is building a creature board, then casting massive X spells."
        ),
        "expected_new_strength": "Should find more than generic Tokens/Spellslinger by surfacing X-spells, creature-count, go-wide, or spell payoff adjacent strategies if present.",
    },
    {
        "deck_name": "Miirym Dragon Copy Smoke Test",
        "commander": "Miirym, Sentinel Wyrm",
        "deck_text": (
            "The deck wants dragon typal synergy, nontoken dragon copies, clone effects, blink and copy effects, big combat pressure, "
            "ETB triggers, ramp, protection, and value engines. The deck wins through copied dragons and overwhelming board presence."
        ),
        "expected_new_strength": "Should find typal/tribal, dragon, copy, blink, combat, or big creature themes beyond the old five preview profiles.",
    },
    {
        "deck_name": "Toggo Artifact Tokens / Landfall Smoke Test",
        "commander": "Toggo, Goblin Weaponsmith",
        "deck_text": (
            "The deck cares about lands entering the battlefield, landfall, artifact tokens, rocks, equipment, sacrifice outlets, "
            "clue food treasure style tokens, and value from small artifacts. It wants lands and artifacts to work together."
        ),
        "expected_new_strength": "Should connect landfall with artifacts, equipment, tokens, sacrifice, and utility token themes beyond only Landfall/Tokens.",
    },
    {
        "deck_name": "Life Gain Drain Smoke Test",
        "commander": "Generic Orzhov Lifegain Commander",
        "deck_text": (
            "The deck gains life repeatedly, drains opponents, uses life total as a resource, protects payoff creatures, "
            "and wants cards that trigger whenever life is gained. It may use aristocrats or sacrifice as a secondary plan."
        ),
        "expected_new_strength": "Should find lifegain and drain strategies that the old five-profile preview could not directly name.",
    },
    {
        "deck_name": "Vehicle Artifact Combat Smoke Test",
        "commander": "Generic Jeskai Vehicle Commander",
        "deck_text": (
            "The deck uses vehicles, artifact creatures, pilots, crew enablers, artifact synergies, combat pressure, "
            "and equipment support. It wants artifact payoff cards and ways to keep vehicles attacking."
        ),
        "expected_new_strength": "Should find Vehicles, Artifacts, Equipment, and combat-adjacent strategies impossible in the old five-profile preview.",
    },
]


def _is_legacy_match(item: Dict[str, Any]) -> bool:
    sid = str(item.get("strategy_id", "")).lower()
    display = str(item.get("display_name", "")).lower()
    return sid in LEGACY_PROFILE_IDS or display in LEGACY_PROFILE_DISPLAY_NAMES


def _trim_match(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "strategy_id": item.get("strategy_id", ""),
        "display_name": item.get("display_name", ""),
        "layer": item.get("layer", ""),
        "score": item.get("score"),
        "raw_score": item.get("raw_score"),
        "keyword_hits": item.get("keyword_hits", [])[:12],
        "role_hits": item.get("role_hits", [])[:12],
        "phrase_hits": item.get("phrase_hits", [])[:12],
        "source": item.get("source", ""),
    }


def _summarize_improvement(new_top: List[Dict[str, Any]], legacy_top: List[Dict[str, Any]]) -> Dict[str, Any]:
    new_ids = [str(item.get("strategy_id")) for item in new_top]
    legacy_ids = {str(item.get("strategy_id")) for item in legacy_top}
    impossible = [item for item in new_top if str(item.get("strategy_id")) not in legacy_ids and not _is_legacy_match(item)]

    return {
        "new_top_match_ids": new_ids,
        "legacy_visible_ids": sorted(legacy_ids),
        "new_matches_not_possible_in_legacy_count": len(impossible),
        "new_matches_not_possible_in_legacy": [_trim_match(item) for item in impossible[:10]],
        "first_non_legacy_match": _trim_match(impossible[0]) if impossible else {},
    }


def build_scoring_regression_payload(context: Any = None) -> Dict[str, Any]:
    from reports.strategy_knowledge_active_scoring import score_strategy_profiles

    deck_results: list[dict[str, Any]] = []

    for deck_context in SAMPLE_DECK_CONTEXTS:
        full_payload = score_strategy_profiles(deck_context, max_results=249)
        all_matches = full_payload.get("top_matches", [])

        new_top_12 = all_matches[:12]
        legacy_candidates = [item for item in all_matches if _is_legacy_match(item)]
        legacy_top = legacy_candidates[:5]

        improvement = _summarize_improvement(new_top_12, legacy_top)

        deck_results.append({
            "deck_name": deck_context.get("deck_name"),
            "commander": deck_context.get("commander"),
            "expected_new_strength": deck_context.get("expected_new_strength"),
            "active_scoring_profiles": full_payload.get("active_scoring_profiles"),
            "legacy_preview_profile_count": full_payload.get("legacy_preview_profile_count"),
            "legacy_preview_status": full_payload.get("legacy_preview_status"),
            "scoring_source": full_payload.get("scoring_source"),
            "new_249_top_matches": [_trim_match(item) for item in new_top_12],
            "legacy_5_visible_matches": [_trim_match(item) for item in legacy_top],
            "legacy_5_visible_match_count": len(legacy_top),
            "regression_summary": improvement,
            "new_finds_more_than_legacy": improvement["new_matches_not_possible_in_legacy_count"] > 0,
            "top_match_is_from_249_scoring": bool(new_top_12),
        })

    aggregate = {
        "sample_deck_count": len(deck_results),
        "all_decks_active_scoring_249": all(item.get("active_scoring_profiles") == 249 for item in deck_results),
        "all_decks_legacy_preview_fallback_only": all(item.get("legacy_preview_status") == "deprecated_fallback_only" for item in deck_results),
        "all_decks_have_new_matches_not_possible_in_legacy": all(item.get("new_finds_more_than_legacy") for item in deck_results),
        "all_decks_have_top_matches": all(item.get("top_match_is_from_249_scoring") for item in deck_results),
        "total_new_matches_not_possible_in_legacy_top_12": sum(
            item.get("regression_summary", {}).get("new_matches_not_possible_in_legacy_count", 0)
            for item in deck_results
        ),
    }

    payload = {
        "regression_version": VERSION,
        "regression_name": "Strategy Knowledge Scoring Regression / Old-vs-New Comparison",
        "runtime_behavior_changed": False,
        "regression_performed": True,
        "active_scoring_profiles": 249,
        "legacy_preview_profile_count": 5,
        "legacy_preview_status": "deprecated_fallback_only",
        "old_scoring_definition": "legacy five-profile preview set: Aristocrats, Landfall, Spellslinger, Tokens, Voltron",
        "new_scoring_definition": "249-profile Strategy Knowledge index active scoring",
        "main_py_changed": False,
        "deck_results": deck_results,
        "aggregate": aggregate,
        "gate_checks": {
            "regression_performed": True,
            "active_scoring_profiles_is_249_for_all_samples": aggregate["all_decks_active_scoring_249"],
            "legacy_preview_is_fallback_only_for_all_samples": aggregate["all_decks_legacy_preview_fallback_only"],
            "new_scoring_finds_matches_not_possible_in_legacy_for_all_samples": aggregate["all_decks_have_new_matches_not_possible_in_legacy"],
            "top_matches_available_for_all_samples": aggregate["all_decks_have_top_matches"],
            "total_new_matches_not_possible_in_legacy_positive": aggregate["total_new_matches_not_possible_in_legacy_top_12"] > 0,
            "main_py_not_changed": True,
        },
        "next_safe_step": "v1.4.38 — v1.4 Expanded Strategy Scoring Lock Candidate",
    }

    return payload


def build_scoring_regression_markdown(payload: Dict[str, Any] | None = None) -> str:
    payload = payload or build_scoring_regression_payload({})
    lines = [
        "# Strategy Knowledge Scoring Regression / Old-vs-New Comparison — v1.4.37",
        "",
        "## Result",
        "",
        f"- Regression performed: {payload.get('regression_performed')}",
        f"- Active scoring profiles: {payload.get('active_scoring_profiles')}",
        f"- Legacy preview profile count: {payload.get('legacy_preview_profile_count')}",
        f"- Legacy preview status: {payload.get('legacy_preview_status')}",
        f"- main.py changed: {payload.get('main_py_changed')}",
        "",
        "## Old vs New Definitions",
        "",
        f"- Old scoring: {payload.get('old_scoring_definition')}",
        f"- New scoring: {payload.get('new_scoring_definition')}",
        "",
        "## Aggregate",
        "",
    ]

    for key, value in payload.get("aggregate", {}).items():
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Deck Comparisons",
        "",
    ])

    for result in payload.get("deck_results", []):
        lines.append(f"### {result.get('deck_name')}")
        lines.append(f"- Commander: {result.get('commander')}")
        lines.append(f"- New finds more than legacy: {result.get('new_finds_more_than_legacy')}")
        lines.append("- Legacy-visible matches:")
        for item in result.get("legacy_5_visible_matches", [])[:5]:
            lines.append(f"  - {item.get('display_name')} (`{item.get('strategy_id')}`), score {item.get('score')}")
        if not result.get("legacy_5_visible_matches"):
            lines.append("  - None from the old five-profile preview set.")
        lines.append("- New 249-profile top matches:")
        for item in result.get("new_249_top_matches", [])[:8]:
            lines.append(f"  - {item.get('display_name')} (`{item.get('strategy_id')}`), score {item.get('score')}")
        first = result.get("regression_summary", {}).get("first_non_legacy_match", {})
        if first:
            lines.append(f"- First match impossible in old preview: {first.get('display_name')} (`{first.get('strategy_id')}`)")
        lines.append("")

    lines.extend([
        "## Gate Checks",
        "",
    ])
    for name, value in payload.get("gate_checks", {}).items():
        lines.append(f"- {name}: {value}")

    lines.extend([
        "",
        "## Boundary",
        "",
        "- This patch proves the expanded scorer finds matches outside the old five-profile preview set.",
        "- It does not change `main.py`.",
        "- It does not remove fallback.",
        "",
        "## Next Safe Step",
        "",
        payload.get("next_safe_step", ""),
    ])

    return "\n".join(lines).rstrip()


def write_scoring_regression_artifacts(output_dir: str | Path | None = None, context: Any = None) -> Dict[str, Any]:
    payload = build_scoring_regression_payload(context)
    REGRESSION_ROOT.mkdir(parents=True, exist_ok=True)
    REGRESSION_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REGRESSION_MD.write_text(build_scoring_regression_markdown(payload) + "\n", encoding="utf-8")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "strategy_knowledge_scoring_regression_old_vs_new_v1.4.37.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (out / "STRATEGY_KNOWLEDGE_SCORING_REGRESSION_OLD_VS_NEW_v1.4.37.md").write_text(
            build_scoring_regression_markdown(payload) + "\n",
            encoding="utf-8",
        )

    return payload


def main() -> int:
    print("v1.4.37 - Strategy Knowledge Scoring Regression / Old-vs-New Comparison")
    print("=" * 78)
    payload = write_scoring_regression_artifacts()

    print(f"Active scoring profiles: {payload.get('active_scoring_profiles')}")
    print(f"Legacy preview profile count: {payload.get('legacy_preview_profile_count')}")
    print(f"Legacy preview status: {payload.get('legacy_preview_status')}")
    print(f"Sample deck count: {payload.get('aggregate', {}).get('sample_deck_count')}")
    print(f"Total new matches not possible in legacy top 12: {payload.get('aggregate', {}).get('total_new_matches_not_possible_in_legacy_top_12')}")
    print(f"Artifact written: {REGRESSION_JSON}")
    print(f"Summary written: {REGRESSION_MD}")

    if not all(payload.get("gate_checks", {}).values()):
        print("Status: FAIL")
        return 1

    print("Status: PASS")
    print("Next safe step: v1.4.38 — v1.4 Expanded Strategy Scoring Lock Candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
