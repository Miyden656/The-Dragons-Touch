"""End-to-end bucket fill verification (combines Items 5 + 6 Phase A + 6 Phase B).

Covers:
- Obeka + [Macro] Combo + Combo Builder persona: all buckets fill to target, zero missing
- Obeka + [Mechanical] Voltron + Battlecruiser: all buckets fill, Strategy bucket differs substantially
- Baylen + [Macro] Tempo + non-curated [Strategic] Kingmaker secondary: still all buckets fill
  (this is the regression case from v1.5.46 — non-curated secondary should not pollute)

Requires the user's collection/ files + data/scryfall_cards.json + the combo index.

Run from project root: py -3 tests/test_bucket_fill_end_to_end.py
"""
from _test_helpers import TestRun, load_scryfall_or_skip, load_owned_collection


def build(commander_name, primary, secondary, persona, bracket, scry, owned):
    from build_from_collection.full_100_card_draft_builder import build_full_100_card_draft
    com = scry.get(commander_name.lower())
    if com is None:
        return None, f"Commander not in scryfall: {commander_name}"
    identity = "".join(com.get("color_identity", []))
    result = build_full_100_card_draft(
        commander_candidate={"commander_name": com["name"], "color_identity_key": identity},
        owned_cards=owned,
        scryfall_lookup=scry,
        primary_strategy=primary,
        secondary_strategy=secondary,
        bracket_preference=bracket,
        sub_philosophy=persona,
    )
    return result, None


def strategy_picks(result):
    return {e.card_name for e in result.entries if e.role_bucket == "Strategy"}


def main() -> None:
    t = TestRun("test_bucket_fill_end_to_end")
    scry = load_scryfall_or_skip()
    owned = load_owned_collection(scry)
    t.true("Owned collection has at least 100 cards from user's files",
           len(owned) >= 100,
           f"got {len(owned)} cards")

    # --- Test 1: Curated x curated (Combo + Revenge) ---
    r1, err = build(
        "Obeka, Splitter of Seconds",
        "[Macro] Combo",
        "[Strategic] Revenge / Retaliation",
        "Combo Builder — Jasper / Jennifer",
        "Bracket 3 — Strong Casual",
        scry, owned,
    )
    if err:
        t.true(f"Obeka Combo build skipped: {err}", False)
    else:
        counts = dict(r1.role_counts)
        t.eq("Obeka Combo: Ramp 10/10", counts.get("Ramp"), 10)
        t.eq("Obeka Combo: Card Draw 10/10", counts.get("Card Draw"), 10)
        t.eq("Obeka Combo: Removal 7/7", counts.get("Removal"), 7)
        t.eq("Obeka Combo: Protection 3/3", counts.get("Protection"), 3)
        t.eq("Obeka Combo: Strategy 25/25", counts.get("Strategy"), 25)
        t.eq("Obeka Combo: Flex 7/7", counts.get("Flex"), 7)
        t.eq("Obeka Combo: 100 total cards", r1.total_cards, 100)
        t.eq("Obeka Combo: no missing slots", dict(r1.missing_slots), {})

    # --- Test 2: Voltron differentiation ---
    r2, err = build(
        "Obeka, Splitter of Seconds",
        "[Mechanical] Voltron",
        "[Mechanical] Equipment",
        "Battlecruiser — Aaron / Ariana",
        "Bracket 3 — Strong Casual",
        scry, owned,
    )
    if err:
        t.true(f"Obeka Voltron build skipped: {err}", False)
    elif r1 is not None and not err:
        counts = dict(r2.role_counts)
        t.eq("Obeka Voltron: Ramp 10/10", counts.get("Ramp"), 10)
        t.eq("Obeka Voltron: Removal 7/7", counts.get("Removal"), 7)
        t.eq("Obeka Voltron: Protection 3/3", counts.get("Protection"), 3)
        t.eq("Obeka Voltron: Strategy 25/25", counts.get("Strategy"), 25)
        s1 = strategy_picks(r1)
        s2 = strategy_picks(r2)
        differential = len(s1 ^ s2)  # symmetric difference
        t.true(f"Combo vs Voltron Strategy buckets differ substantially (>=30 picks differ)",
               differential >= 30,
               f"symmetric diff = {differential}")

    # --- Test 3: non-curated secondary regression (v1.5.46 fix) ---
    r3, err = build(
        "Baylen, the Haymaker",
        "[Macro] Tempo",
        "[Strategic] Kingmaker / Table-Balancer",  # non-curated
        "Combo Builder — Jasper / Jennifer",
        "Bracket 3 — Strong Casual",
        scry, owned,
    )
    if err:
        t.true(f"Baylen build skipped: {err}", False)
    else:
        counts = dict(r3.role_counts)
        # The regression bug had Ramp 0/10 and Removal 0/7 because the placeholder
        # secondary leaked utility tags into the combined strategy_tags.
        t.eq("Baylen Tempo+Kingmaker: Ramp 10/10 (non-curated secondary fix)",
             counts.get("Ramp"), 10)
        t.eq("Baylen Tempo+Kingmaker: Removal 7/7 (non-curated secondary fix)",
             counts.get("Removal"), 7)
        t.eq("Baylen Tempo+Kingmaker: Protection 3/3",
             counts.get("Protection"), 3)
        t.eq("Baylen Tempo+Kingmaker: no missing slots",
             dict(r3.missing_slots), {})

    t.report_and_exit()


if __name__ == "__main__":
    main()
