"""v1.6.1 Phase 5 — bracket data module + filter regression tests.

Verifies:
  1. All five brackets are defined with the expected metadata.
  2. Filter regression — the new data-driven is_card_allowed_in_bracket and
     score_modifier_for_bracket produce the same answers as the v1.5.40
     hard-coded branches for representative cards across all 5 brackets.
  3. AND-group exclusions (combo_piece_possible + win_condition at B2,
     ritual + fast_mana at B2).
  4. Precon-friendly name exemptions (Sol Ring at B2).
  5. Label parsing handles all the labels emitted by the UI.

Run from project root:  py -3 tests/test_bracket_definitions.py
"""
from _test_helpers import TestRun

from rules.bracket_definitions import (
    BRACKETS,
    BRACKET_1,
    BRACKET_2,
    BRACKET_3,
    BRACKET_4,
    BRACKET_5,
    PRECON_FRIENDLY_EXEMPTIONS,
    bracket_number_from_label,
    filter_summary_for_bracket,
    get_bracket_definition,
    is_precon_friendly_exemption,
    tags_hard_excluded,
    tags_soft_modifier,
)
from build_from_collection.bracket_filter import (
    bracket_filter_summary,
    bracket_to_int,
    is_card_allowed_in_bracket,
    score_modifier_for_bracket,
)


def main() -> None:
    t = TestRun("test_bracket_definitions")

    # ----- All five brackets defined --------------------------------------
    t.eq("5 brackets defined", len(BRACKETS), 5)
    for n in (1, 2, 3, 4, 5):
        t.in_set(f"bracket {n} present", n, BRACKETS)
        bd = BRACKETS[n]
        t.eq(f"bracket {n} number matches key", bd.number, n)
        t.true(f"bracket {n} has non-empty full_label", bool(bd.full_label))
        t.true(f"bracket {n} has non-empty intent", bool(bd.intent))
        t.true(f"bracket {n} banned_cards_allowed is False (always)",
               bd.banned_cards_allowed is False)

    t.eq("B1 game_changer_count_limit == 0", BRACKET_1.game_changer_count_limit, 0)
    t.eq("B2 game_changer_count_limit == 0", BRACKET_2.game_changer_count_limit, 0)
    t.eq("B3 game_changer_count_limit == 3", BRACKET_3.game_changer_count_limit, 3)
    t.true("B4 game_changer_count_limit is unlimited (None)",
           BRACKET_4.game_changer_count_limit is None)
    t.true("B5 game_changer_count_limit is unlimited (None)",
           BRACKET_5.game_changer_count_limit is None)
    t.eq("B1 expected turns before win == 9", BRACKET_1.expected_turns_before_win, 9)
    t.eq("B5 has no turn expectation", BRACKET_5.expected_turns_before_win, None)

    # ----- Label / number parsing -----------------------------------------
    t.eq("bracket_to_int 'Bracket 1 — Low Power / Precon-Friendly' == 1",
         bracket_to_int("Bracket 1 — Low Power / Precon-Friendly"), 1)
    t.eq("bracket_to_int 'Bracket 5 — cEDH / Competitive' == 5",
         bracket_to_int("Bracket 5 — cEDH / Competitive"), 5)
    t.eq("bracket_to_int 'Not Sure Yet' == 0",
         bracket_to_int("Not Sure Yet"), 0)
    t.eq("bracket_to_int '' == 0", bracket_to_int(""), 0)
    t.eq("bracket_to_int None == 0", bracket_to_int(None), 0)
    t.eq("bracket_number_from_label int 3 == 3", bracket_number_from_label(3), 3)
    t.eq("bracket_number_from_label int 7 (out of range) == 0",
         bracket_number_from_label(7), 0)
    t.true("get_bracket_definition int 3 returns BRACKET_3",
           get_bracket_definition(3) is BRACKET_3)
    t.true("get_bracket_definition 'Bracket 2 — Casual Upgraded' returns BRACKET_2",
           get_bracket_definition("Bracket 2 — Casual Upgraded") is BRACKET_2)
    t.true("get_bracket_definition 'Not Sure Yet' returns None",
           get_bracket_definition("Not Sure Yet") is None)

    # ----- Precon-friendly exemptions -------------------------------------
    t.true("'Sol Ring' is precon-friendly", is_precon_friendly_exemption("Sol Ring"))
    t.true("'sol ring' (case) is precon-friendly", is_precon_friendly_exemption("sol ring"))
    t.true("'Arcane Signet' is precon-friendly",
           is_precon_friendly_exemption("Arcane Signet"))
    t.true("'Mana Crypt' is NOT precon-friendly",
           not is_precon_friendly_exemption("Mana Crypt"))
    t.true("None / '' is NOT precon-friendly",
           not is_precon_friendly_exemption("") and not is_precon_friendly_exemption(None))

    # ----- Filter regression: B1 -------------------------------------------
    # B1 (Low Power) excludes fast mana, ritual, efficient_tutor,
    # free_interaction, combo_protection, bracket_pressure, high_bracket_pressure.
    b1 = "Bracket 1 — Low Power / Precon-Friendly"
    t.true("B1: fast_mana excluded",
           not is_card_allowed_in_bracket({"fast_mana"}, "Mana Crypt", b1))
    t.true("B1: ritual excluded",
           not is_card_allowed_in_bracket({"ritual"}, "Dark Ritual", b1))
    t.true("B1: efficient_tutor excluded",
           not is_card_allowed_in_bracket({"efficient_tutor"}, "Demonic Tutor", b1))
    t.true("B1: free_interaction excluded",
           not is_card_allowed_in_bracket({"free_interaction"}, "Force of Will", b1))
    t.true("B1: bracket_pressure excluded",
           not is_card_allowed_in_bracket({"bracket_pressure"}, "Generic Pressure", b1))
    t.true("B1: Sol Ring excluded (no precon exemption at B1)",
           not is_card_allowed_in_bracket({"fast_mana"}, "Sol Ring", b1))
    t.true("B1: plain creature with no pressure tags passes",
           is_card_allowed_in_bracket({"etb_value", "creature_type_present"}, "Dragon Lord", b1))

    # ----- Filter regression: B2 -------------------------------------------
    b2 = "Bracket 2 — Casual Upgraded"
    t.true("B2: Sol Ring allowed (precon exemption)",
           is_card_allowed_in_bracket({"fast_mana"}, "Sol Ring", b2))
    t.true("B2: Arcane Signet allowed (precon exemption)",
           is_card_allowed_in_bracket({"fast_mana"}, "Arcane Signet", b2))
    t.true("B2: high_bracket_pressure excluded",
           not is_card_allowed_in_bracket({"high_bracket_pressure"}, "Mana Crypt", b2))
    t.true("B2: free_interaction excluded",
           not is_card_allowed_in_bracket({"free_interaction"}, "Force of Will", b2))
    t.true("B2: efficient_tutor excluded",
           not is_card_allowed_in_bracket({"efficient_tutor"}, "Vampiric Tutor", b2))
    t.true("B2: combo_protection excluded",
           not is_card_allowed_in_bracket({"combo_protection"}, "Silence", b2))
    t.true("B2: ritual+fast_mana pair excluded (e.g., LED-like)",
           not is_card_allowed_in_bracket({"ritual", "fast_mana"}, "Lion's Eye Diamond", b2))
    t.true("B2: combo_piece_possible+win_condition pair excluded",
           not is_card_allowed_in_bracket(
               {"combo_piece_possible", "win_condition"}, "Thassa's Oracle", b2))
    t.true("B2: combo_piece_possible alone allowed (no win_condition)",
           is_card_allowed_in_bracket({"combo_piece_possible"}, "Generic Combo Piece", b2))
    t.true("B2: plain creature allowed",
           is_card_allowed_in_bracket({"etb_value"}, "Generic Dragon", b2))

    # ----- Filter regression: B3 / B4 / B5 (no hard excludes) -------------
    b3 = "Bracket 3 — Strong Casual"
    b4 = "Bracket 4 — High Power"
    b5 = "Bracket 5 — cEDH / Competitive"
    for label in (b3, b4, b5):
        # No matter how many pressure tags a card has, B3+ allows it.
        t.true(f"{label}: fast_mana allowed",
               is_card_allowed_in_bracket({"fast_mana"}, "Mana Crypt", label))
        t.true(f"{label}: free_interaction allowed",
               is_card_allowed_in_bracket({"free_interaction"}, "Force of Will", label))
        t.true(f"{label}: combo_piece_possible+win_condition allowed",
               is_card_allowed_in_bracket(
                   {"combo_piece_possible", "win_condition"}, "Thassa's Oracle", label))

    # ----- Filter regression: 'Not Sure Yet' / unset --------------------
    t.true("Not Sure: all cards pass",
           is_card_allowed_in_bracket({"fast_mana", "free_interaction"}, "Mana Crypt", "Not Sure Yet"))
    t.true("None bracket: all cards pass",
           is_card_allowed_in_bracket({"fast_mana"}, "Mana Crypt", None))

    # ----- Soft score modifier regression --------------------------------
    # B1/B2 modifiers are 0 (their hard filter handled exclusions).
    t.eq("B1 soft modifier always 0", score_modifier_for_bracket({"fast_mana"}, b1), 0.0)
    t.eq("B2 soft modifier always 0", score_modifier_for_bracket({"fast_mana"}, b2), 0.0)
    # B3 penalty values from v1.5.40 (regression).
    t.eq("B3 high_bracket_pressure penalty == -3.0",
         score_modifier_for_bracket({"high_bracket_pressure"}, b3), -3.0)
    t.eq("B3 free_interaction penalty == -1.5",
         score_modifier_for_bracket({"free_interaction"}, b3), -1.5)
    t.eq("B3 efficient_tutor penalty == -1.5",
         score_modifier_for_bracket({"efficient_tutor"}, b3), -1.5)
    t.eq("B3 combo_protection penalty == -1.0",
         score_modifier_for_bracket({"combo_protection"}, b3), -1.0)
    t.eq("B3 no-pressure card == 0",
         score_modifier_for_bracket({"etb_value", "card_draw"}, b3), 0.0)
    # B4 mild boosts from v1.5.40 (regression).
    t.eq("B4 bracket_pressure boost == 0.5",
         score_modifier_for_bracket({"bracket_pressure"}, b4), 0.5)
    t.eq("B4 high_bracket_pressure boost == 1.0",
         score_modifier_for_bracket({"high_bracket_pressure"}, b4), 1.0)
    # B5 boosts from v1.5.40 (regression).
    t.eq("B5 fast_mana boost == 2.5",
         score_modifier_for_bracket({"fast_mana"}, b5), 2.5)
    t.eq("B5 ritual boost == 1.5",
         score_modifier_for_bracket({"ritual"}, b5), 1.5)
    t.eq("B5 free_interaction boost == 2.5",
         score_modifier_for_bracket({"free_interaction"}, b5), 2.5)
    t.eq("B5 efficient_tutor boost == 2.0",
         score_modifier_for_bracket({"efficient_tutor"}, b5), 2.0)
    t.eq("B5 multiple-tag stacks: fast_mana + free_interaction = 5.0",
         score_modifier_for_bracket({"fast_mana", "free_interaction"}, b5), 5.0)
    t.eq("Not Sure: 0 soft modifier",
         score_modifier_for_bracket({"fast_mana"}, "Not Sure Yet"), 0.0)

    # ----- Summary text reasonable ----------------------------------------
    for label in (b1, b2, b3, b4, b5):
        s = bracket_filter_summary(label)
        t.true(f"{label}: summary is non-empty", bool(s) and len(s) > 10)
    t.true("'Not Sure' summary mentions no filter",
           "no" in filter_summary_for_bracket("Not Sure Yet").lower())

    # ----- Cross-check: tags_hard_excluded() helper -----------------------
    t.in_set("B1 hard excludes fast_mana",
             "fast_mana", tags_hard_excluded(1))
    t.in_set("B2 hard excludes high_bracket_pressure",
             "high_bracket_pressure", tags_hard_excluded(2))
    t.eq("B3 hard excludes empty set", tags_hard_excluded(3), frozenset())
    t.eq("B5 hard excludes empty set", tags_hard_excluded(5), frozenset())

    # ----- Sanity: BRACKETS dict's filter_summary attributes set ---------
    for n, bd in BRACKETS.items():
        t.true(f"bracket {n} has non-empty filter_summary string", bool(bd.filter_summary))

    t.report_and_exit()


if __name__ == "__main__":
    main()
