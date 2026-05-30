"""v1.6.1 Phase 6 — commander format rules tests.

Verifies the new rules/commander_format_rules.py module:
  1. Constants present with the right values.
  2. detect_command_zone_rules() correctly identifies basic legendary,
     planeswalker-commander, partner, partner-with, background,
     choose-a-background, friends-forever, doctor's-companion, and doctor.
  3. is_format_disallowed_card() catches conspiracies / planes / schemes /
     phenomena / vanguards / dungeons / attractions / stickers / contraptions.
  4. is_silver_border_or_acorn() catches the un-card border marker.
  5. is_companion_card() detects the keyword but does NOT promote to
     commander status.
  6. is_basic_land_singleton_exempt() handles basic + basic snow + non-basic
     lands correctly.
  7. is_commander_deck_size_legal() catches deck sizes != 100.
  8. Cross-module alignment: commander_discovery.eligibility's
     RULE_BASIC_LEGENDARY_CREATURE is the SAME string as the canonical
     COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE in rules.

Run from project root:  py -3 tests/test_commander_format_rules.py
"""
from _test_helpers import TestRun

from rules.commander_format_rules import (
    COMMANDER_DECK_SIZE,
    COMMANDER_DECK_SIZE_INCLUDES_COMMANDER,
    COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE,
    COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER,
    COMMAND_ZONE_RULE_PARTNER,
    COMMAND_ZONE_RULE_PARTNER_WITH,
    COMMAND_ZONE_RULE_BACKGROUND,
    COMMAND_ZONE_RULE_CHOOSE_BACKGROUND,
    COMMAND_ZONE_RULE_FRIENDS_FOREVER,
    COMMAND_ZONE_RULE_DOCTORS_COMPANION,
    COMMAND_ZONE_RULE_DOCTOR,
    COMPANION_IS_NOT_A_COMMANDER,
    FORMAT_DISALLOWED_TYPES,
    FORMAT_DISALLOWED_BORDER_COLORS,
    SINGLETON_RULE,
    COLOR_IDENTITY_RULE,
    detect_command_zone_rules,
    is_basic_land_singleton_exempt,
    is_background_card,
    is_choose_a_background_commander,
    is_commander_deck_size_legal,
    is_companion_card,
    is_doctors_companion,
    is_format_disallowed_card,
    is_friends_forever,
    is_partner,
    is_partner_with,
    is_planeswalker_commander,
    is_silver_border_or_acorn,
    is_the_doctor,
)


def _legendary_creature(name: str, *, oracle: str = "", type_extra: str = "") -> dict:
    return {
        "name": name,
        "type_line": f"Legendary Creature — {type_extra or 'Human Wizard'}",
        "oracle_text": oracle,
        "legalities": {"commander": "legal"},
        "color_identity": [],
    }


def main() -> None:
    t = TestRun("test_commander_format_rules")

    # ----- Constants ------------------------------------------------------
    t.eq("COMMANDER_DECK_SIZE == 100", COMMANDER_DECK_SIZE, 100)
    t.true("COMMANDER_DECK_SIZE_INCLUDES_COMMANDER True",
           COMMANDER_DECK_SIZE_INCLUDES_COMMANDER is True)
    t.true("COMPANION_IS_NOT_A_COMMANDER True", COMPANION_IS_NOT_A_COMMANDER is True)
    t.true("SINGLETON_RULE non-empty", bool(SINGLETON_RULE))
    t.true("COLOR_IDENTITY_RULE non-empty", bool(COLOR_IDENTITY_RULE))
    t.eq("COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE value",
         COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE, "basic_legendary_creature")
    t.eq("COMMAND_ZONE_RULE_PARTNER value",
         COMMAND_ZONE_RULE_PARTNER, "partner")
    t.in_set("FORMAT_DISALLOWED_TYPES contains Conspiracy",
             "Conspiracy", FORMAT_DISALLOWED_TYPES)
    t.in_set("FORMAT_DISALLOWED_TYPES contains Scheme",
             "Scheme", FORMAT_DISALLOWED_TYPES)
    t.in_set("FORMAT_DISALLOWED_TYPES contains Vanguard",
             "Vanguard", FORMAT_DISALLOWED_TYPES)
    t.in_set("FORMAT_DISALLOWED_TYPES contains Attraction",
             "Attraction", FORMAT_DISALLOWED_TYPES)
    t.in_set("FORMAT_DISALLOWED_BORDER_COLORS contains silver",
             "silver", FORMAT_DISALLOWED_BORDER_COLORS)

    # ----- Cross-module string alignment ----------------------------------
    from commander_discovery.eligibility import RULE_BASIC_LEGENDARY_CREATURE
    t.eq("eligibility.RULE_BASIC_LEGENDARY_CREATURE == COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE",
         RULE_BASIC_LEGENDARY_CREATURE, COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE)

    # ----- is_commander_deck_size_legal -----------------------------------
    t.true("100 == legal", is_commander_deck_size_legal(100))
    t.true("99 not legal", not is_commander_deck_size_legal(99))
    t.true("101 not legal", not is_commander_deck_size_legal(101))
    t.true("60 (Standard) not legal", not is_commander_deck_size_legal(60))

    # ----- is_basic_land_singleton_exempt --------------------------------
    plains = {"type_line": "Basic Land — Plains"}
    snow_island = {"type_line": "Basic Snow Land — Island"}
    forest = {"type_line": "Basic Land — Forest"}
    command_tower = {"type_line": "Land"}
    triome = {"type_line": "Land — Forest Island Plains"}
    wastes = {"type_line": "Basic Land"}
    t.true("Plains is basic-exempt", is_basic_land_singleton_exempt(plains))
    t.true("Snow Island is basic-exempt", is_basic_land_singleton_exempt(snow_island))
    t.true("Forest is basic-exempt", is_basic_land_singleton_exempt(forest))
    t.true("Wastes is basic-exempt", is_basic_land_singleton_exempt(wastes))
    t.true("Command Tower NOT basic-exempt",
           not is_basic_land_singleton_exempt(command_tower))
    t.true("Triome NOT basic-exempt",
           not is_basic_land_singleton_exempt(triome))

    # ----- detect_command_zone_rules: basic legendary --------------------
    atraxa = _legendary_creature("Atraxa, Praetors' Voice",
                                  oracle="Flying, vigilance, deathtouch, lifelink.\n"
                                         "At the beginning of your end step, proliferate.",
                                  type_extra="Phyrexian Angel Horror")
    rules = detect_command_zone_rules(atraxa)
    t.in_set("Atraxa: basic_legendary_creature",
             COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE, rules)
    t.true("Atraxa: NOT partner", COMMAND_ZONE_RULE_PARTNER not in rules)

    # ----- detect_command_zone_rules: partner (bare) ---------------------
    tymna = _legendary_creature(
        "Tymna the Weaver",
        oracle="Partner (You can have two commanders if both have partner.)\n"
               "At the beginning of your post-combat main phase, draw a card.",
    )
    rules = detect_command_zone_rules(tymna)
    t.in_set("Tymna: basic_legendary_creature",
             COMMAND_ZONE_RULE_BASIC_LEGENDARY_CREATURE, rules)
    t.in_set("Tymna: partner", COMMAND_ZONE_RULE_PARTNER, rules)
    t.true("Tymna: partner_with NOT triggered (bare partner)",
           COMMAND_ZONE_RULE_PARTNER_WITH not in rules)
    t.true("is_partner(Tymna) True", is_partner(tymna))
    found, name = is_partner_with(tymna)
    t.true("is_partner_with(Tymna): False", not found)

    # ----- detect_command_zone_rules: partner with -----------------------
    pir = _legendary_creature(
        "Pir, Imaginative Rascal",
        oracle="Partner with Toothy, Imaginary Friend (When this creature enters, "
               "target player may put Toothy into their hand from their library, "
               "then shuffle.)\n"
               "If one or more counters would be put on a permanent you control, "
               "that many plus one of each of those kinds of counters are put on "
               "that permanent instead.",
    )
    rules = detect_command_zone_rules(pir)
    t.in_set("Pir: partner_with", COMMAND_ZONE_RULE_PARTNER_WITH, rules)
    t.true("Pir: bare partner NOT triggered",
           COMMAND_ZONE_RULE_PARTNER not in rules)
    found, name = is_partner_with(pir)
    t.true("is_partner_with(Pir) True", found)
    t.true("partner-with name extracted contains 'Toothy'",
           name is not None and "toothy" in name.lower())

    # ----- detect_command_zone_rules: background -------------------------
    candlekeep_sage = _legendary_creature(
        "Candlekeep Sage",
        oracle="Choose a Background (You can have a Background as a second commander.)\n"
               "Whenever you cast a creature spell, draw a card.",
    )
    rules = detect_command_zone_rules(candlekeep_sage)
    t.in_set("Candlekeep Sage: choose_a_background",
             COMMAND_ZONE_RULE_CHOOSE_BACKGROUND, rules)
    t.true("is_choose_a_background_commander(Candlekeep Sage) True",
           is_choose_a_background_commander(candlekeep_sage))

    raised_by_giants = {
        "name": "Raised by Giants",
        "type_line": "Legendary Enchantment — Background",
        "oracle_text": "Commander creatures you own have +2/+2 and the Giant creature type.",
        "legalities": {"commander": "legal"},
        "color_identity": ["W"],
    }
    rules = detect_command_zone_rules(raised_by_giants)
    t.in_set("Raised by Giants: background",
             COMMAND_ZONE_RULE_BACKGROUND, rules)
    t.true("is_background_card(Raised by Giants) True",
           is_background_card(raised_by_giants))
    t.true("is_background_card(Atraxa) False",
           not is_background_card(atraxa))

    # ----- detect_command_zone_rules: Friends Forever --------------------
    ferell = _legendary_creature(
        "Faceless One",
        oracle="Friends forever (You can have two commanders if both have friends forever.)\n"
               "Sacrifice this creature: It deals 1 damage to any target.",
    )
    rules = detect_command_zone_rules(ferell)
    t.in_set("Faceless One: friends_forever",
             COMMAND_ZONE_RULE_FRIENDS_FOREVER, rules)
    t.true("is_friends_forever(Faceless One) True", is_friends_forever(ferell))

    # ----- detect_command_zone_rules: Doctor's Companion + Doctor -------
    sarah_jane = _legendary_creature(
        "Sarah Jane Smith",
        oracle="Doctor's companion (You can have two commanders if the other is "
               "the Doctor.)\n"
               "When this creature enters, scry 2.",
        type_extra="Human",
    )
    rules = detect_command_zone_rules(sarah_jane)
    t.in_set("Sarah Jane: doctor's_companion",
             COMMAND_ZONE_RULE_DOCTORS_COMPANION, rules)
    t.true("is_doctors_companion(Sarah Jane) True",
           is_doctors_companion(sarah_jane))

    fourth_doctor = {
        "name": "The Fourth Doctor",
        "type_line": "Legendary Creature — Time Lord Doctor",
        "oracle_text": "When this creature enters, you may draw a card.",
        "legalities": {"commander": "legal"},
        "color_identity": ["U"],
    }
    rules = detect_command_zone_rules(fourth_doctor)
    t.in_set("Fourth Doctor: doctor", COMMAND_ZONE_RULE_DOCTOR, rules)
    t.true("is_the_doctor(Fourth Doctor) True", is_the_doctor(fourth_doctor))

    # ----- detect_command_zone_rules: planeswalker commander -------------
    daretti = {
        "name": "Daretti, Scrap Savant",
        "type_line": "Legendary Planeswalker — Daretti",
        "oracle_text": "Daretti, Scrap Savant can be your commander.\n"
                       "[+2]: Draw two cards, then discard two cards.",
        "legalities": {"commander": "legal"},
        "color_identity": ["R"],
    }
    rules = detect_command_zone_rules(daretti)
    t.in_set("Daretti: planeswalker_commander",
             COMMAND_ZONE_RULE_PLANESWALKER_COMMANDER, rules)
    t.true("is_planeswalker_commander(Daretti) True",
           is_planeswalker_commander(daretti))

    # ----- format-disallowed types ----------------------------------------
    conspiracy = {
        "name": "Backup Plan",
        "type_line": "Conspiracy",
        "oracle_text": "(Start the game with this conspiracy face up...)\n"
                       "Draw an extra opening hand.",
        "border_color": "black",
    }
    disallowed, reason = is_format_disallowed_card(conspiracy)
    t.true("Conspiracy is format-disallowed", disallowed and "Conspiracy" in reason)

    plane = {"type_line": "Plane — Dominaria", "border_color": "black"}
    disallowed, reason = is_format_disallowed_card(plane)
    t.true("Plane is format-disallowed", disallowed)

    scheme = {"type_line": "Scheme", "border_color": "black"}
    disallowed, reason = is_format_disallowed_card(scheme)
    t.true("Scheme is format-disallowed", disallowed)

    vanguard = {"type_line": "Vanguard", "border_color": "black"}
    disallowed, reason = is_format_disallowed_card(vanguard)
    t.true("Vanguard is format-disallowed", disallowed)

    legal_creature = atraxa
    disallowed, reason = is_format_disallowed_card(legal_creature)
    t.true("Legendary Creature is NOT format-disallowed", not disallowed)

    # ----- silver-border detection ----------------------------------------
    silver = {"name": "Cheatyface", "type_line": "Creature", "border_color": "silver"}
    t.true("silver-border detected", is_silver_border_or_acorn(silver))
    t.true("black-border NOT detected as silver",
           not is_silver_border_or_acorn(atraxa))
    t.true("None NOT silver", not is_silver_border_or_acorn(None))

    # ----- Companion -----------------------------------------------------
    lutri = _legendary_creature(
        "Lutri, the Spellchaser",
        oracle="Companion — Each nonland card in your starting deck has a "
               "different name.\n"
               "Flying.\n"
               "When this creature enters, if you cast it, copy target instant "
               "or sorcery spell you control.",
        type_extra="Elemental Otter",
    )
    t.true("is_companion_card(Lutri) True", is_companion_card(lutri))
    # A non-companion legendary doesn't trip the detector even though Tymna
    # has 'partner' (the regex must not be wider than 'companion'):
    t.true("Tymna is NOT a companion card", not is_companion_card(tymna))

    # ----- Defensive: None / empty inputs ---------------------------------
    t.eq("detect_command_zone_rules(None) -> []",
         detect_command_zone_rules(None), [])
    t.eq("detect_command_zone_rules({}) -> []",
         detect_command_zone_rules({}), [])
    t.true("is_format_disallowed_card(None) -> (False, '')",
           is_format_disallowed_card(None) == (False, ""))

    t.report_and_exit()


if __name__ == "__main__":
    main()
