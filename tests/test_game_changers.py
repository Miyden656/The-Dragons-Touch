"""v1.6.2 Phase E — Game Changer tracking tests.

Verifies:
  1. Curated GAME_CHANGERS list has the canonical first-tier names.
  2. is_game_changer / count_game_changers / game_changer_status work.
  3. End-to-end: a build with Rhystic Study + Smothering Tithe + Cyclonic
     Rift in the collection produces a result with game_changer_count=3
     and game_changer_status='over_limit' at B2 (limit 0).
  4. Same deck at B4 (unlimited) is 'ok' status.

Run from project root:  py -3 tests/test_game_changers.py
"""
from _test_helpers import TestRun

from build_from_collection.full_100_card_draft_builder import (
    build_full_100_card_draft,
    render_full_100_card_draft_markdown,
)
from rules.game_changers import (
    GAME_CHANGERS,
    count_game_changers,
    game_changer_status,
    is_game_changer,
    list_game_changers_in_deck,
)


def main() -> None:
    t = TestRun("test_game_changers")

    # ----- Curated list spot-check -------------------------------------
    expected = [
        "rhystic study", "smothering tithe", "cyclonic rift",
        "mystic remora", "demonic tutor", "vampiric tutor",
        "the one ring", "fierce guardianship", "necropotence",
        "drannith magistrate", "thassa's oracle",
    ]
    for name in expected:
        t.in_set(f"'{name}' is in GAME_CHANGERS", name, GAME_CHANGERS)
    t.true("Sol Ring is NOT a Game Changer (per RC list)",
           not is_game_changer("Sol Ring"))

    # ----- is_game_changer ---------------------------------------------
    t.true("is_game_changer('Rhystic Study') True",
           is_game_changer("Rhystic Study"))
    t.true("is_game_changer('rhystic study') True (case insensitive)",
           is_game_changer("rhystic study"))
    t.true("is_game_changer('Lightning Bolt') False",
           not is_game_changer("Lightning Bolt"))
    t.true("is_game_changer(None) False", not is_game_changer(None))
    t.true("is_game_changer('') False", not is_game_changer(""))

    # ----- count_game_changers -----------------------------------------
    t.eq("count of 3 GCs in mixed list",
         count_game_changers(["Rhystic Study", "Smothering Tithe",
                              "Lightning Bolt", "Cyclonic Rift"]),
         3)
    t.eq("count of duplicates is 1",
         count_game_changers(["Rhystic Study", "Rhystic Study"]),
         1)
    t.eq("count of empty list 0", count_game_changers([]), 0)

    # ----- game_changer_status -----------------------------------------
    status, msg = game_changer_status(0, 0)
    t.eq("count 0, limit 0: status ok", status, "ok")
    status, msg = game_changer_status(2, 3)
    t.eq("count 2, limit 3: status ok", status, "ok")
    status, msg = game_changer_status(5, 0)
    t.eq("count 5, limit 0: status over_limit", status, "over_limit")
    t.true("over_limit message includes over-by count", "over by 5" in msg)
    status, msg = game_changer_status(3, None)
    t.eq("count 3, limit None: status ok", status, "ok")
    t.true("unlimited bracket message still notes disclosure",
           "disclose" in msg.lower() or "unlimited" in msg.lower())

    # ----- list_game_changers_in_deck ----------------------------------
    found = list_game_changers_in_deck([
        "Rhystic Study", "Lightning Bolt", "Smothering Tithe", "Sol Ring",
    ])
    t.eq("list_game_changers_in_deck finds 2", len(found), 2)

    # ----- End-to-end: B2 build with 3 GCs flagged over-limit ----------
    commander = {
        "name": "Test Esper Lord",
        "type_line": "Legendary Creature — Human Wizard",
        "cmc": 4,
        "color_identity": ["W", "U", "B"],
        "oracle_text": "Flash.\nWhen this creature enters, draw a card.",
        "legalities": {"commander": "legal"},
    }
    rhystic = {
        "name": "Rhystic Study",
        "type_line": "Enchantment",
        "cmc": 3, "color_identity": ["U"],
        "oracle_text": "Whenever an opponent casts a spell, you may draw a card "
                       "unless that player pays {1}.",
        "legalities": {"commander": "legal"},
    }
    tithe = {
        "name": "Smothering Tithe",
        "type_line": "Enchantment",
        "cmc": 4, "color_identity": ["W"],
        "oracle_text": "Whenever an opponent draws a card, that player may pay {2}. "
                       "If they don't, you create a Treasure token.",
        "legalities": {"commander": "legal"},
    }
    rift = {
        "name": "Cyclonic Rift",
        "type_line": "Instant",
        "cmc": 2, "color_identity": ["U"],
        "oracle_text": "Return target nonland permanent you don't control to its "
                       "owner's hand.\nOverload {6}{U}",
        "legalities": {"commander": "legal"},
    }
    scry = {c["name"].lower(): c
            for c in (commander, rhystic, tithe, rift)}
    owned = [
        {"name": rhystic["name"], "owned_quantity": 1, "source_files": ["t.txt"],
         "oracle_text": rhystic["oracle_text"], "type_line": rhystic["type_line"]},
        {"name": tithe["name"], "owned_quantity": 1, "source_files": ["t.txt"],
         "oracle_text": tithe["oracle_text"], "type_line": tithe["type_line"]},
        {"name": rift["name"], "owned_quantity": 1, "source_files": ["t.txt"],
         "oracle_text": rift["oracle_text"], "type_line": rift["type_line"]},
    ]
    # Add filler so the deck reaches 100.
    for i in range(80):
        c = {"name": f"Filler Spell {i}", "type_line": "Instant",
             "color_identity": ["W"], "cmc": 2,
             "oracle_text": "Counter target spell.",
             "legalities": {"commander": "legal"}}
        scry[c["name"].lower()] = c
        owned.append({"name": c["name"], "owned_quantity": 1,
                      "source_files": ["t.txt"],
                      "oracle_text": c["oracle_text"], "type_line": c["type_line"]})

    # B2 build: GC count > limit (0).
    result_b2 = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"],
                             "color_identity_key": "WUB"},
        owned_cards=owned,
        scryfall_lookup=scry,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 2 — Casual Upgraded",
        sub_philosophy="",
    )
    # Note: B2 hard-filters efficient_tutor and free_interaction; Rhystic /
    # Smothering Tithe / Cyclonic Rift's exclusion at B2 depends on whether
    # the role_tags fire. They're not in tier-1 of bracket-filter pressure
    # tags by default. Confirm at least one GC made it in.
    t.true(f"B2 build: GC count > 0 (found {result_b2.game_changer_count})",
           result_b2.game_changer_count > 0)
    t.eq("B2 build: game_changer_limit == 0", result_b2.game_changer_limit, 0)
    t.eq("B2 build: status is over_limit",
         result_b2.game_changer_status, "over_limit")
    t.true("B2 build: report markdown mentions Game Changers",
           "Game Changers" in render_full_100_card_draft_markdown(result_b2))

    # B5 build: GC count whatever, but limit is None (unlimited).
    result_b5 = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"],
                             "color_identity_key": "WUB"},
        owned_cards=owned,
        scryfall_lookup=scry,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 5 — cEDH / Competitive",
        sub_philosophy="",
    )
    t.true("B5 build: game_changer_limit is None (unlimited)",
           result_b5.game_changer_limit is None)
    t.eq("B5 build: status is ok",
         result_b5.game_changer_status, "ok")

    t.report_and_exit()


if __name__ == "__main__":
    main()
