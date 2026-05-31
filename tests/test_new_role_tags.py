"""v1.6.2 Phase A — new role-tag pattern tests.

Verifies the new tag patterns added for the deferred-fixes pass:
  - devotion_payoff (Gray Merchant, Heliod, Nykthos, Thassa, Erebos, Omnath)
  - token_doubler (Doubling Season, Anointed Procession, Parallel Lives,
                   Mondrak Glory Dominus, Primal Vigor)
  - overrun_finisher (Craterhoof Behemoth, Overwhelming Stampede,
                      Triumph of the Hordes, Akroma's Will, Pathbreaker Ibex)
  - untap_engine (Voltaic Key, Manifold Key, Aphetto Alchemist, Pemmin's Aura,
                  Freed from the Real, Thousand-Year Elixir)
  - uncounterable_enabler (Cavern of Souls, Allosaurus Shepherd, Veil of
                           Summer, Vexing Shusher, Grand Abolisher)

Uses synthetic Scryfall fixtures + the curated card-name overrides so the
test runs without scryfall_cards.json.

Run from project root:  py -3 tests/test_new_role_tags.py
"""
from _test_helpers import TestRun

from analysis.role_tags import infer_card_role_tags


def _card(name: str, *, type_line: str = "Instant", oracle_text: str = "",
          cmc: float = 2.0, color_identity=None) -> dict:
    return {
        "name": name,
        "type_line": type_line,
        "cmc": cmc,
        "color_identity": color_identity if color_identity is not None else [],
        "oracle_text": oracle_text,
    }


def main() -> None:
    t = TestRun("test_new_role_tags")

    # ----- devotion_payoff via overrides --------------------------------
    gary = _card(
        "Gray Merchant of Asphodel",
        type_line="Creature — Zombie",
        oracle_text="When this creature enters, each opponent loses life equal "
                    "to your devotion to black.",
        cmc=5, color_identity=["B"],
    )
    tags = infer_card_role_tags(gary)
    t.in_set("Gary: devotion_payoff", "devotion_payoff", tags)
    t.in_set("Gary: lifedrain_payoff", "lifedrain_payoff", tags)
    t.in_set("Gary: win_condition", "win_condition", tags)

    nykthos = _card(
        "Nykthos, Shrine to Nyx",
        type_line="Land",
        oracle_text="{T}: Add {C}.\n{2}, {T}: Choose a color. Add an amount of "
                    "mana of that color equal to your devotion to that color.",
        cmc=0, color_identity=[],
    )
    tags = infer_card_role_tags(nykthos)
    t.in_set("Nykthos: devotion_payoff", "devotion_payoff", tags)
    t.in_set("Nykthos: mana_source", "mana_source", tags)
    t.in_set("Nykthos: ramp", "ramp", tags)

    # ----- devotion_payoff via PATTERN (no override) ---------------------
    custom_devotion = _card(
        "Test Devotion Spell",
        type_line="Sorcery",
        oracle_text="Add mana equal to your devotion to green.",
        cmc=3, color_identity=["G"],
    )
    tags = infer_card_role_tags(custom_devotion)
    t.in_set("custom devotion: devotion_payoff (via pattern)",
             "devotion_payoff", tags)

    # ----- token_doubler via overrides ----------------------------------
    doubling_season = _card(
        "Doubling Season",
        type_line="Enchantment",
        oracle_text="If an effect would create one or more tokens under your "
                    "control, it creates twice that many of those tokens instead.\n"
                    "If an effect would put one or more counters on a permanent "
                    "you control, it puts twice that many of those counters on "
                    "that permanent instead.",
        cmc=5, color_identity=["G"],
    )
    tags = infer_card_role_tags(doubling_season)
    t.in_set("Doubling Season: token_doubler", "token_doubler", tags)
    t.in_set("Doubling Season: counter_synergy", "counter_synergy", tags)
    t.in_set("Doubling Season: token_maker", "token_maker", tags)

    anointed = _card(
        "Anointed Procession",
        type_line="Enchantment",
        oracle_text="If an effect would create one or more tokens under your "
                    "control, it creates twice that many of those tokens instead.",
        cmc=4, color_identity=["W"],
    )
    tags = infer_card_role_tags(anointed)
    t.in_set("Anointed Procession: token_doubler", "token_doubler", tags)

    parallel = _card(
        "Parallel Lives",
        type_line="Enchantment",
        oracle_text="If an effect would create one or more tokens under your "
                    "control, it creates twice that many of those tokens instead.",
        cmc=4, color_identity=["G"],
    )
    tags = infer_card_role_tags(parallel)
    t.in_set("Parallel Lives: token_doubler", "token_doubler", tags)

    # ----- token_doubler via PATTERN (no override) ----------------------
    custom_doubler = _card(
        "Test Token Doubler",
        type_line="Enchantment",
        oracle_text="If an effect would create one or more tokens, that effect "
                    "creates twice that many tokens instead.",
        cmc=4, color_identity=["W"],
    )
    tags = infer_card_role_tags(custom_doubler)
    t.in_set("custom doubler: token_doubler (via pattern)",
             "token_doubler", tags)

    # Generic token-maker should NOT be flagged as a doubler.
    raise_dead = _card(
        "Test Token Maker",
        type_line="Sorcery",
        oracle_text="Create a 2/2 black Zombie creature token.",
        cmc=3, color_identity=["B"],
    )
    tags = infer_card_role_tags(raise_dead)
    t.in_set("plain token maker: token_maker", "token_maker", tags)
    t.true("plain token maker: NOT token_doubler",
           "token_doubler" not in tags)

    # ----- overrun_finisher via overrides --------------------------------
    craterhoof = _card(
        "Craterhoof Behemoth",
        type_line="Creature — Beast",
        oracle_text="Trample.\nWhen this creature enters, creatures you control "
                    "gain trample and get +X/+X until end of turn, where X is "
                    "the number of creatures you control.",
        cmc=8, color_identity=["G"],
    )
    tags = infer_card_role_tags(craterhoof)
    t.in_set("Craterhoof: overrun_finisher", "overrun_finisher", tags)
    t.in_set("Craterhoof: win_condition", "win_condition", tags)

    triumph = _card(
        "Triumph of the Hordes",
        type_line="Sorcery",
        oracle_text="Until end of turn, creatures you control gain infect and "
                    "get +1/+1.",
        cmc=4, color_identity=["G"],
    )
    tags = infer_card_role_tags(triumph)
    t.in_set("Triumph: overrun_finisher", "overrun_finisher", tags)
    t.in_set("Triumph: win_condition", "win_condition", tags)
    t.in_set("Triumph: high_bracket_pressure", "high_bracket_pressure", tags)

    # ----- overrun_finisher via PATTERN ---------------------------------
    custom_overrun = _card(
        "Test Stampede",
        type_line="Sorcery",
        oracle_text="Until end of turn, creatures you control get +3/+3 and "
                    "gain trample.",
        cmc=4, color_identity=["G"],
    )
    tags = infer_card_role_tags(custom_overrun)
    t.in_set("custom overrun: overrun_finisher (via pattern)",
             "overrun_finisher", tags)

    # ----- untap_engine via overrides -----------------------------------
    voltaic = _card(
        "Voltaic Key",
        type_line="Artifact",
        oracle_text="{1}, {T}: Untap target artifact.",
        cmc=1, color_identity=[],
    )
    tags = infer_card_role_tags(voltaic)
    t.in_set("Voltaic Key: untap_engine", "untap_engine", tags)
    t.in_set("Voltaic Key: repeatable_activation", "repeatable_activation", tags)
    t.in_set("Voltaic Key: activated_ability_synergy",
             "activated_ability_synergy", tags)

    freed = _card(
        "Freed from the Real",
        type_line="Enchantment — Aura",
        oracle_text="Enchant creature.\nEnchanted creature has \"{U}: Untap "
                    "this creature.\"",
        cmc=3, color_identity=["U"],
    )
    tags = infer_card_role_tags(freed)
    t.in_set("Freed from the Real: untap_engine", "untap_engine", tags)
    t.in_set("Freed from the Real: combo_piece_possible",
             "combo_piece_possible", tags)

    # ----- untap_engine via PATTERN ------------------------------------
    custom_untap = _card(
        "Test Untapper",
        type_line="Artifact",
        oracle_text="{T}: Untap target artifact you control.",
        cmc=2, color_identity=[],
    )
    tags = infer_card_role_tags(custom_untap)
    t.in_set("custom untapper: untap_engine (via pattern)",
             "untap_engine", tags)

    # ----- uncounterable_enabler via overrides --------------------------
    cavern = _card(
        "Cavern of Souls",
        type_line="Land",
        oracle_text="As Cavern of Souls enters, choose a creature type.\n"
                    "{T}: Add {C}.\n{T}: Add one mana of any color. Creature "
                    "spells you cast of the chosen type can't be countered.",
        cmc=0, color_identity=[],
    )
    tags = infer_card_role_tags(cavern)
    t.in_set("Cavern of Souls: uncounterable_enabler",
             "uncounterable_enabler", tags)
    t.in_set("Cavern of Souls: tribal_payoff", "tribal_payoff", tags)

    veil = _card(
        "Veil of Summer",
        type_line="Instant",
        oracle_text="Draw a card if an opponent has cast a blue or black spell "
                    "this turn.\nSpells you control can't be countered this "
                    "turn. You and permanents you control gain hexproof from "
                    "blue and from black until end of turn.",
        cmc=1, color_identity=["G"],
    )
    tags = infer_card_role_tags(veil)
    t.in_set("Veil of Summer: uncounterable_enabler",
             "uncounterable_enabler", tags)

    # ----- uncounterable_enabler via PATTERN ---------------------------
    custom_uncounterable = _card(
        "Test Stompy Lord",
        type_line="Creature — Elf",
        oracle_text="Creature spells you control can't be countered.",
        cmc=4, color_identity=["G"],
    )
    tags = infer_card_role_tags(custom_uncounterable)
    t.in_set("custom uncounterable: uncounterable_enabler (via pattern)",
             "uncounterable_enabler", tags)

    # "This spell can't be countered" alone should NOT trigger the enabler tag
    # (it's a self-protection flag, not an enabler).
    self_protected = _card(
        "Test Self-Protected Creature",
        type_line="Creature — Spirit",
        oracle_text="This spell can't be countered.\nFlying.",
        cmc=4, color_identity=["W"],
    )
    tags = infer_card_role_tags(self_protected)
    t.true("self-protected creature: NOT uncounterable_enabler",
           "uncounterable_enabler" not in tags)

    t.report_and_exit()


if __name__ == "__main__":
    main()
