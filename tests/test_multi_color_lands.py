"""v1.6.2 Phase D — multi-color premium-fixer tests.

Verifies:
  1. PREMIUM_FIXERS contains the canonical first-pick lands.
  2. is_premium_fixer / fixer_priority correctly classify lands.
  3. prefers_premium_fixers returns True for 2+ colors, False for 0-1.
  4. End-to-end: a 4-color build with Command Tower + triomes in the
     collection picks them ahead of random alphabetically-early lands.

Run from project root:  py -3 tests/test_multi_color_lands.py
"""
from _test_helpers import TestRun

from rules.multi_color_lands import (
    PREMIUM_FIXERS,
    TIER_1_FIXERS,
    TIER_2_FIXERS,
    fixer_priority,
    is_premium_fixer,
    prefers_premium_fixers,
)
from build_from_collection.full_100_card_draft_builder import build_full_100_card_draft


def main() -> None:
    t = TestRun("test_multi_color_lands")

    # ----- Canonical premium fixers present in TIER_1 -------------------
    must_be_tier_1 = [
        "command tower", "reflecting pool", "exotic orchard",
        "city of brass", "mana confluence",
        "hallowed fountain", "watery grave", "polluted delta",
        "verdant catacombs",
    ]
    for name in must_be_tier_1:
        t.in_set(f"'{name}' is tier-1 premium fixer", name, TIER_1_FIXERS)

    # ----- Helpers ------------------------------------------------------
    t.true("is_premium_fixer('Command Tower') True",
           is_premium_fixer("Command Tower"))
    t.true("is_premium_fixer('command tower') True (case insensitive)",
           is_premium_fixer("command tower"))
    t.true("is_premium_fixer('Random Mono Land') False",
           not is_premium_fixer("Random Mono Land"))
    t.true("is_premium_fixer(None) False", not is_premium_fixer(None))
    t.true("is_premium_fixer('') False", not is_premium_fixer(""))

    t.eq("fixer_priority('Command Tower') == 0 (tier 1)",
         fixer_priority("Command Tower"), 0)
    t.eq("fixer_priority('Sunpetal Grove') == 1 (tier 2)",
         fixer_priority("Sunpetal Grove"), 1)
    t.eq("fixer_priority('Random Mono Land') == 2 (no tier)",
         fixer_priority("Random Mono Land"), 2)
    t.eq("fixer_priority(None) == 2", fixer_priority(None), 2)

    # ----- prefers_premium_fixers --------------------------------------
    t.true("0 colors: NO premium-fixer preference",
           not prefers_premium_fixers(0))
    t.true("1 color: NO premium-fixer preference",
           not prefers_premium_fixers(1))
    t.true("2 colors: YES premium-fixer preference",
           prefers_premium_fixers(2))
    t.true("5 colors: YES premium-fixer preference",
           prefers_premium_fixers(5))

    # ----- End-to-end: 4-color build prefers Command Tower etc. --------
    commander = {
        "name": "Test 4-Color Lord",
        "type_line": "Legendary Creature — Phyrexian Angel",
        "cmc": 4,
        "color_identity": ["W", "U", "B", "G"],
        "oracle_text": "Flying, vigilance.",
        "legalities": {"commander": "legal"},
    }
    scry = {commander["name"].lower(): commander}
    owned: list[dict] = []

    def add(card: dict) -> None:
        scry[card["name"].lower()] = card
        owned.append({
            "name": card["name"], "owned_quantity": 1,
            "source_files": ["t.txt"],
            "oracle_text": card.get("oracle_text", ""),
            "type_line": card.get("type_line", ""),
        })

    # Premium fixers — should be picked first.
    add({"name": "Command Tower", "type_line": "Land",
         "color_identity": [], "cmc": 0,
         "oracle_text": "{T}: Add one mana of any color in your commander's identity.",
         "legalities": {"commander": "legal"}})
    add({"name": "Reflecting Pool", "type_line": "Land",
         "color_identity": [], "cmc": 0,
         "oracle_text": "{T}: Add one mana of any type that a land you control could produce.",
         "legalities": {"commander": "legal"}})
    add({"name": "Indatha Triome", "type_line": "Land — Plains Swamp Forest",
         "color_identity": ["W", "B", "G"], "cmc": 0,
         "oracle_text": "({T}: Add {W}, {B}, or {G}.) Indatha Triome enters tapped. Cycling {3}.",
         "legalities": {"commander": "legal"}})
    # Random mono-color lands that would be alphabetically earlier (A-, B-).
    for letter, color in [("A", "W"), ("B", "U")]:
        add({"name": f"{letter}rcane Sanctuary", "type_line": "Land",
             "color_identity": [color], "cmc": 0,
             "oracle_text": f"{{T}}: Add {{{color}}}.",
             "legalities": {"commander": "legal"}})

    # Fill rest of deck so build hits 100.
    for i in range(30):
        add({"name": f"Generic Creature {i}", "type_line": "Creature — Human",
             "color_identity": ["W"], "cmc": 3,
             "oracle_text": "Flying.",
             "legalities": {"commander": "legal"}})
    for i in range(15):
        add({"name": f"Ramp Sorcery {i}", "type_line": "Sorcery",
             "color_identity": ["G"], "cmc": 2,
             "oracle_text": "Search your library for a basic land card and put it onto the battlefield.",
             "legalities": {"commander": "legal"}})
    for i in range(15):
        add({"name": f"Draw Spell {i}", "type_line": "Instant",
             "color_identity": ["U"], "cmc": 2,
             "oracle_text": "Draw two cards.",
             "legalities": {"commander": "legal"}})
    for i in range(15):
        add({"name": f"Removal Spell {i}", "type_line": "Instant",
             "color_identity": ["B"], "cmc": 2,
             "oracle_text": "Destroy target creature.",
             "legalities": {"commander": "legal"}})

    result = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"],
                             "color_identity_key": "WUBG"},
        owned_cards=owned,
        scryfall_lookup=scry,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    deck_names = {e.card_name for e in result.entries}
    t.in_set("4-color build: Command Tower included",
             "Command Tower", deck_names)
    t.in_set("4-color build: Reflecting Pool included",
             "Reflecting Pool", deck_names)
    t.in_set("4-color build: Indatha Triome included",
             "Indatha Triome", deck_names)

    t.report_and_exit()


if __name__ == "__main__":
    main()
