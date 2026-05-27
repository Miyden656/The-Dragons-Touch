"""Test combo-aware scoring (Bin B Item 5, v1.5).

Covers:
- Combo index loads
- Reachable combos detected for a Grixis (UBR) collection with combo pieces
- Persona orientation table resolves correctly
- combo_score_modifier produces expected +/-/0 deltas for known combo pieces

Run from project root: py -3 tests/test_combo_scorer.py
"""
from _test_helpers import TestRun, load_combo_index_or_skip


def main() -> None:
    t = TestRun("test_combo_scorer")

    # --- Imports + module health ---
    from build_from_collection.combo_scorer import (
        combo_persona_orientation,
        relevant_combos_for_build,
        build_combo_name_lookup,
        combo_score_modifier,
    )
    t.true("combo_scorer module imports OK", True)

    # --- Persona orientation table ---
    t.eq("Combo Builder persona is leaning",
         combo_persona_orientation("Combo Builder — Jasper / Jennifer"), "leaning")
    t.eq("Competitive Closer persona is leaning",
         combo_persona_orientation("Competitive Closer — Charlie"), "leaning")
    t.eq("Let Me Do My Thing persona is averse",
         combo_persona_orientation("Let Me Do My Thing — William / Willow"), "averse")
    t.eq("Big Moment persona is averse",
         combo_persona_orientation("Big Moment — Michael / Michelle"), "averse")
    t.eq("Battlecruiser persona is neutral",
         combo_persona_orientation("Battlecruiser — Aaron / Ariana"), "neutral")
    t.eq("Empty persona is neutral",
         combo_persona_orientation(""), "neutral")
    t.eq("No Persona selector value is neutral",
         combo_persona_orientation("No Persona / Not Sure Yet"), "neutral")

    # --- Combo index loads + reachable combos ---
    load_combo_index_or_skip()  # bails early with SKIP if not built

    sample_collection = [
        "Thassa's Oracle", "Demonic Consultation", "Tainted Pact",
        "Dramatic Reversal", "Isochron Scepter",
        "Underworld Breach", "Brain Freeze", "Lion's Eye Diamond",
        "Sol Ring", "Counterspell", "Force of Will",
    ]
    combos = relevant_combos_for_build(
        commander_identity={"U", "B", "R"},
        owned_card_names=sample_collection,
        max_results=20,
    )
    t.true("At least one reachable Grixis combo detected",
           len(combos) >= 1,
           f"got {len(combos)} combos")

    # We expect well-known lines: Thoracle+Consultation, Thoracle+Tainted Pact, IsoRev, Breach storm
    owned_pairs = [tuple(sorted(c.owned_normalized_names)) for c in combos]
    famous_pairs = [
        {"demonic consultation", "thassa's oracle"},
        {"tainted pact", "thassa's oracle"},
        {"dramatic reversal", "isochron scepter"},
    ]
    found = sum(1 for fp in famous_pairs if any(fp.issubset(set(p)) for p in owned_pairs))
    t.true("Famous Grixis combo lines detected (Thoracle/Pact/IsoRev)",
           found >= 2, f"found {found}/3 famous lines")

    # --- Score modifier behavior ---
    lookup = build_combo_name_lookup(combos)

    leaning_thoracle = combo_score_modifier("Thassa's Oracle", lookup, "leaning")
    t.true("Combo-leaning Thoracle modifier > 0",
           leaning_thoracle > 0, f"got {leaning_thoracle}")
    t.true("Combo-leaning modifier capped at +6.0",
           leaning_thoracle <= 6.0, f"got {leaning_thoracle}")

    averse_thoracle = combo_score_modifier("Thassa's Oracle", lookup, "averse")
    t.true("Combo-averse Thoracle modifier < 0",
           averse_thoracle < 0, f"got {averse_thoracle}")
    t.true("Combo-averse modifier capped at -6.0",
           averse_thoracle >= -6.0, f"got {averse_thoracle}")

    neutral_thoracle = combo_score_modifier("Thassa's Oracle", lookup, "neutral")
    t.eq("Combo-neutral modifier is exactly 0", neutral_thoracle, 0.0)

    non_combo = combo_score_modifier("Sol Ring", lookup, "leaning")
    t.eq("Non-combo card gets 0 leaning modifier", non_combo, 0.0)

    t.report_and_exit()


if __name__ == "__main__":
    main()
