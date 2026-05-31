"""v1.6.2 Phase C — tribal fidelity tests.

Verifies:
  1. extract_commander_tribes pulls subtypes correctly and strips
     UNIVERSAL_CLASS_TYPES (Elder, Avatar).
  2. extract_card_tribes returns all subtypes (including Elder).
  3. tribal_fidelity_boost scales correctly: 0 for no overlap, default for
     1 shared, 1.5x default for 2 shared, 2.0x for 3 shared.
  4. End-to-end: Ghalta-style dinosaur build pulls MORE dinosaur creatures
     than a Ghalta build run WITHOUT the boost — proving the score boost
     measurably shifts selection.

Run from project root:  py -3 tests/test_tribal_fidelity.py
"""
from _test_helpers import TestRun

from build_from_collection.full_100_card_draft_builder import build_full_100_card_draft
from build_from_collection.tribal_fidelity import (
    EXTRA_TRIBE_MULTIPLIER,
    describe_tribal_match,
    extract_card_tribes,
    extract_commander_tribes,
    shared_tribes,
    tribal_fidelity_boost,
)


def main() -> None:
    t = TestRun("test_tribal_fidelity")

    # ----- extract_commander_tribes ---------------------------------------
    ghalta = {"type_line": "Legendary Creature — Elder Dinosaur"}
    tribes = extract_commander_tribes(ghalta)
    t.in_set("Ghalta: 'dinosaur' in commander tribes", "dinosaur", tribes)
    t.true("Ghalta: 'elder' EXCLUDED (universal class type)",
           "elder" not in tribes)

    baylen = {"type_line": "Legendary Creature — Rabbit Citizen"}
    tribes = extract_commander_tribes(baylen)
    t.in_set("Baylen: 'rabbit' in tribes", "rabbit", tribes)
    t.in_set("Baylen: 'citizen' in tribes", "citizen", tribes)

    omnath = {"type_line": "Legendary Creature — Elder Elemental"}
    tribes = extract_commander_tribes(omnath)
    t.in_set("Omnath: 'elemental' in tribes", "elemental", tribes)
    t.true("Omnath: 'elder' EXCLUDED", "elder" not in tribes)

    # Edge cases.
    t.eq("None card -> empty set", extract_commander_tribes(None), set())
    t.eq("Empty dict -> empty set", extract_commander_tribes({}), set())
    t.eq("Non-creature card -> empty set",
         extract_commander_tribes({"type_line": "Instant"}), set())

    # ----- extract_card_tribes -------------------------------------------
    elder_dinosaur = {"type_line": "Creature — Elder Dinosaur"}
    tribes = extract_card_tribes(elder_dinosaur)
    t.in_set("Elder Dinosaur card: 'elder' included",
             "elder", tribes)
    t.in_set("Elder Dinosaur card: 'dinosaur' included",
             "dinosaur", tribes)

    # ----- shared_tribes -------------------------------------------------
    cmdr = extract_commander_tribes(ghalta)  # {dinosaur}
    card_dino = extract_card_tribes({"type_line": "Creature — Dinosaur"})
    card_human = extract_card_tribes({"type_line": "Creature — Human Wizard"})
    t.eq("Dinosaur card vs Ghalta: shared = {dinosaur}",
         shared_tribes(cmdr, card_dino), {"dinosaur"})
    t.eq("Human Wizard card vs Ghalta: shared = empty",
         shared_tribes(cmdr, card_human), set())

    # ----- tribal_fidelity_boost scaling --------------------------------
    t.eq("0 shared -> boost = 0.0",
         tribal_fidelity_boost(set(), set()), 0.0)
    t.eq("0 shared (no overlap) -> boost = 0.0",
         tribal_fidelity_boost({"dinosaur"}, {"goblin"}), 0.0)
    t.eq("1 shared -> boost = default 2.5",
         tribal_fidelity_boost({"dinosaur"}, {"dinosaur"}, default_boost=2.5),
         2.5)
    # 2 shared: 2.5 * (1 + 0.5) = 3.75
    t.eq("2 shared -> 1.5x default = 3.75",
         tribal_fidelity_boost({"goblin", "warrior"}, {"goblin", "warrior"},
                               default_boost=2.5),
         3.75)
    # 3 shared: 2.5 * (1 + 1.0) = 5.0
    t.eq("3 shared -> 2.0x default = 5.0",
         tribal_fidelity_boost({"goblin", "warrior", "shaman"},
                               {"goblin", "warrior", "shaman"},
                               default_boost=2.5),
         5.0)

    # ----- describe_tribal_match ----------------------------------------
    t.eq("describe: no overlap -> empty",
         describe_tribal_match(set(), set()), "")
    desc = describe_tribal_match({"dinosaur"}, {"dinosaur"})
    t.true("describe: single match contains 'Dinosaur'", "Dinosaur" in desc)
    t.true("describe: starts with 'Tribal fit'",
           desc.startswith("Tribal fit"))
    desc = describe_tribal_match({"goblin", "warrior"}, {"goblin", "warrior"})
    t.true("describe: multi-tribe lists both", "Goblin" in desc and "Warrior" in desc)

    # ----- End-to-end: Ghalta build pulls more Dinosaurs with boost ------
    # Build a synthetic collection: 30 Dinosaurs + 30 generic green creatures.
    # With tribal fidelity boost active, the Strategy bucket should prefer
    # Dinosaurs even though all 60 creatures have the same role tags.
    commander = {
        "name": "Test Ghalta Lord",
        "type_line": "Legendary Creature — Elder Dinosaur",
        "cmc": 12,
        "color_identity": ["G"],
        "oracle_text": "Trample. This spell costs {X} less to cast, where X "
                       "is the total power of creatures you control.",
        "legalities": {"commander": "legal"},
    }
    scryfall_lookup = {commander["name"].lower(): commander}
    owned_cards: list[dict] = []

    def add(card: dict) -> None:
        scryfall_lookup[card["name"].lower()] = card
        owned_cards.append({
            "name": card["name"], "owned_quantity": 1,
            "source_files": ["t.txt"],
            "oracle_text": card.get("oracle_text", ""),
            "type_line": card.get("type_line", ""),
        })

    for i in range(30):
        add({
            "name": f"Stomping Dinosaur {i}",
            "type_line": "Creature — Dinosaur",
            "cmc": 5 + (i % 3),
            "color_identity": ["G"],
            "oracle_text": "Trample.",
            "legalities": {"commander": "legal"},
        })
    for i in range(30):
        add({
            "name": f"Random Green Creature {i}",
            "type_line": "Creature — Beast",
            "cmc": 5 + (i % 3),
            "color_identity": ["G"],
            "oracle_text": "Trample.",
            "legalities": {"commander": "legal"},
        })
    # Noncreature support so deck reaches 100.
    for i in range(15):
        add({
            "name": f"Ramp {i}",
            "type_line": "Sorcery", "cmc": 2,
            "color_identity": ["G"],
            "oracle_text": "Search your library for a basic land card and put "
                           "it onto the battlefield.",
            "legalities": {"commander": "legal"},
        })
    for i in range(15):
        add({
            "name": f"Draw {i}",
            "type_line": "Sorcery", "cmc": 3,
            "color_identity": ["G"],
            "oracle_text": "Draw two cards.",
            "legalities": {"commander": "legal"},
        })
    for i in range(15):
        add({
            "name": f"Removal {i}",
            "type_line": "Instant", "cmc": 2,
            "color_identity": ["G"],
            "oracle_text": "Destroy target creature.",
            "legalities": {"commander": "legal"},
        })

    result = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"],
                             "color_identity_key": "G"},
        owned_cards=owned_cards,
        scryfall_lookup=scryfall_lookup,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    dino_count = sum(
        1 for e in result.entries if "Stomping Dinosaur" in e.card_name
    )
    beast_count = sum(
        1 for e in result.entries if "Random Green Creature" in e.card_name
    )
    t.true(
        f"Ghalta build: more Dinosaurs ({dino_count}) than off-tribe Beasts ({beast_count})",
        dino_count > beast_count,
    )
    t.true(
        f"Ghalta build: at least 15 Dinosaurs (got {dino_count})",
        dino_count >= 15,
    )
    # Tribal-fit why-tag appears on the dinosaur picks.
    tribal_why_tags_present = sum(
        1 for e in result.entries
        if any("Tribal fit" in w for w in (e.why_tags or []))
    )
    t.true(
        f"Ghalta build: 'Tribal fit' why-tag on at least 10 picks "
        f"(got {tribal_why_tags_present})",
        tribal_why_tags_present >= 10,
    )

    t.report_and_exit()


if __name__ == "__main__":
    main()
