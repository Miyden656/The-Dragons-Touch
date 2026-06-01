"""Tests: deck-derived persona affinity (Layer 2).

Pure logic, no Ollama / no engine run. Feeds synthetic analysis objects and
asserts the derived personas are sensible, always include the neutral baseline,
never include an intent persona, and only ever name real philosophy keys.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.training.persona_affinity import (
    BASELINE_PERSONA,
    INTENT_PERSONAS,
    derive_personas_for_deck,
    intent_persona_sample,
)
from analysis.deck_building_philosophies import PHILOSOPHY_PROFILES


def _analysis(primary="Midrange / Value", bracket="Bracket 3", threat="low", pressure="low"):
    return {
        "strategy_summary": NS(primary_strategy=primary, secondary_strategy=""),
        "bracket_summary": NS(estimated_bracket=bracket, pressure_level=pressure),
        "multiplayer_summary": NS(archenemy_risk_band=threat),
    }


def _keys(picks):
    return [p.key for p in picks]


def main() -> None:
    t = TestRun("ai_persona_affinity")
    valid = set(PHILOSOPHY_PROFILES.keys())

    # --- shape: baseline + up to 2 fit, baseline first ---
    picks = derive_personas_for_deck(_analysis())
    t.eq("returns 3 picks (baseline + 2 fit)", len(picks), 3)
    t.eq("first pick is the neutral baseline", picks[0].key, BASELINE_PERSONA)
    t.true("every pick carries a why", all(p.why for p in picks))
    t.true("no duplicate persona keys", len(set(_keys(picks))) == len(picks))

    # --- only ever names real philosophy keys ---
    t.true("all keys are real philosophy keys", all(k in valid for k in _keys(picks)))

    # --- never includes an intent persona ---
    t.true("intent personas excluded", not (set(_keys(picks)) & set(INTENT_PERSONAS)))

    # --- strategy axis reads ---
    combo = _keys(derive_personas_for_deck(_analysis(primary="Combo-Adjacent Value")))
    t.true("combo deck -> combo_builder", "combo_builder" in combo)
    control = _keys(derive_personas_for_deck(_analysis(primary="Control")))
    t.true("control deck -> interaction_controller", "interaction_controller" in control)
    tokens = _keys(derive_personas_for_deck(_analysis(primary="Tokens / Go-Wide Combat")))
    t.true("tokens deck -> big_moment", "big_moment" in tokens)

    # --- power axis reads ---
    high = _keys(derive_personas_for_deck(_analysis(primary="Combo-Adjacent Value",
                                                    bracket="Bracket 4", threat="high", pressure="high")))
    t.true("high power -> competitive_closer", "competitive_closer" in high)
    low = _keys(derive_personas_for_deck(_analysis(primary="Big Creature / Stompy",
                                                   bracket="Bracket 2", threat="low", pressure="low")))
    t.true("low power -> battlecruiser", "battlecruiser" in low)

    # --- robustness: empty / garbage analysis still yields a valid set ---
    empty = derive_personas_for_deck({})
    t.eq("empty analysis still returns 3", len(empty), 3)
    t.true("empty analysis keys valid", all(k in valid for k in _keys(empty)))
    t.eq("None analysis -> baseline first", derive_personas_for_deck(None)[0].key, BASELINE_PERSONA)
    garbage = derive_personas_for_deck(NS(strategy_summary="???", bracket_summary=42, multiplayer_summary=None))
    t.true("garbage analysis does not crash + valid", all(k in valid for k in _keys(garbage)))

    # --- intent sampling ---
    decks = [f"d{i}.txt" for i in range(50)]
    t.eq("sample size respected", len(intent_persona_sample(decks, 12)), 12)
    t.true("sample is a subset, no dupes", len(set(intent_persona_sample(decks, 12))) == 12)
    t.eq("fewer decks than sample -> all", len(intent_persona_sample(decks[:5], 12)), 5)
    t.eq("zero sample -> empty", intent_persona_sample(decks, 0), [])
    t.eq("empty decks -> empty", intent_persona_sample([], 12), [])

    t.report_and_exit()


if __name__ == "__main__":
    main()
