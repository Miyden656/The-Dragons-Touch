"""v1.6.2 Phase B — commander amplifier pattern tests.

Verifies that synthetic commanders modeled on the famous edge-case
commanders from the audit pick up the new amplifier tags:

  - Omnath Locus of All-like (devotion to all 5 colors) -> devotion_payoff
  - Garth-style tutor-via-activated-ability -> untap_engine, activated_ability_synergy
  - Aisha of Sparks and Smoke / Shorikai (activated abilities matter) ->
    untap_engine, repeatable_activation
  - Baylen (10+ tokens) -> token_doubler, go_wide_token_engine
  - Thrun (can't be countered) -> uncounterable_enabler

Plus a regression: a control commander (counterspells) does NOT get
overrun_finisher or uncounterable_enabler — those are specific signals.

Run from project root:  py -3 tests/test_commander_amplifier_patterns.py
"""
from _test_helpers import TestRun

from build_from_collection.commander_text_scorer import (
    commander_amplifier_tags,
    commander_amplifier_summary,
)


def _commander(name: str, type_line: str, oracle: str) -> dict:
    return {
        "name": name,
        "type_line": type_line,
        "oracle_text": oracle,
        "color_identity": ["W", "U", "B", "R", "G"],  # 5-color so identity isn't a filter
    }


def main() -> None:
    t = TestRun("test_commander_amplifier_patterns")

    # ----- Devotion commander (Omnath Locus of All style) ----------------
    omnath_style = _commander(
        "Test Devotion Locus",
        "Legendary Creature — Elemental",
        "If you would draw a card after the first one you draw each turn, "
        "exile that card face down instead. You may look at and play cards "
        "exiled this way. Add {W}{U}{B}{R}{G} for each color you have devotion to.",
    )
    tags = commander_amplifier_tags(omnath_style)
    t.in_set("devotion commander: devotion_payoff", "devotion_payoff", tags)
    t.in_set("devotion commander: mana_source", "mana_source", tags)

    # ----- Activated-ability commander (Garth One-Eye style) -------------
    garth_style = _commander(
        "Test Tutor Lord",
        "Legendary Creature — Human Wizard",
        "{2}{W}{U}{B}{R}{G}, {T}: You may activate this ability only any time "
        "you could cast a sorcery. Search your library for a card and put it "
        "into your hand.",
    )
    tags = commander_amplifier_tags(garth_style)
    t.in_set("Garth-style: untap_engine", "untap_engine", tags)
    t.in_set("Garth-style: activated_ability_synergy", "activated_ability_synergy", tags)
    t.in_set("Garth-style: repeatable_activation", "repeatable_activation", tags)

    # ----- Aisha of Sparks and Smoke style ------------------------------
    aisha_style = _commander(
        "Test Aisha Lord",
        "Legendary Creature — Dragon",
        "Indestructible.\nWhenever you activate an ability of a nonland "
        "permanent you control that isn't a mana ability, this creature "
        "deals 2 damage to each opponent.",
    )
    tags = commander_amplifier_tags(aisha_style)
    t.in_set("Aisha-style: untap_engine (activated abilities matter)",
             "untap_engine", tags)
    t.in_set("Aisha-style: activated_ability_synergy",
             "activated_ability_synergy", tags)
    t.in_set("Aisha-style: trigger_amplifier (every activation matters)",
             "trigger_amplifier", tags)

    # ----- Token commander (Baylen style: '10 or more tokens') ----------
    baylen_style = _commander(
        "Test Baylen Lord",
        "Legendary Creature — Rabbit Citizen",
        "When this creature enters, create three 1/1 white Rabbit creature "
        "tokens.\nAt the beginning of your end step, if you have ten or more "
        "tokens, draw two cards.",
    )
    tags = commander_amplifier_tags(baylen_style)
    t.in_set("Baylen-style: token_doubler (wants Anointed Procession etc.)",
             "token_doubler", tags)
    t.in_set("Baylen-style: token_maker", "token_maker", tags)
    t.in_set("Baylen-style: go_wide_token_engine",
             "go_wide_token_engine", tags)

    # ----- Stompy commander (Thrun style: can't be countered) -----------
    thrun_style = _commander(
        "Test Thrun Lord",
        "Legendary Creature — Phyrexian Troll",
        "This spell can't be countered. Hexproof, Reach, Trample, "
        "Indestructible.\nWhenever this creature attacks, put a +1/+1 counter "
        "on another target creature you control. That creature gains hexproof "
        "and indestructible until end of turn.",
    )
    tags = commander_amplifier_tags(thrun_style)
    t.in_set("Thrun-style: uncounterable_enabler (wants Cavern etc.)",
             "uncounterable_enabler", tags)
    t.in_set("Thrun-style: protection", "protection", tags)
    t.in_set("Thrun-style: combat_synergy", "combat_synergy", tags)
    t.in_set("Thrun-style: counter_synergy (+1/+1 counter)",
             "counter_synergy", tags)

    # ----- Regression: control commander does NOT get overrun_finisher --
    control_style = _commander(
        "Test Counter Lord",
        "Legendary Creature — Human Wizard",
        "Whenever you cast a noncreature spell, scry 1. {U}{U}, {T}: Counter "
        "target spell unless its controller pays 2.",
    )
    tags = commander_amplifier_tags(control_style)
    t.true("control commander: NOT overrun_finisher",
           "overrun_finisher" not in tags)
    t.true("control commander: NOT uncounterable_enabler "
           "(its OWN text doesn't make spells uncounterable)",
           "uncounterable_enabler" not in tags)
    t.in_set("control commander: spell_payoff (still detected)",
             "spell_payoff", tags)

    # ----- Friendly-label summary mentions new tags ---------------------
    # Thrun's synthetic text triggers >8 amplifier tags so the summary
    # truncates; just confirm the summary is well-formed.
    summary = commander_amplifier_summary(thrun_style)
    t.true("Thrun-style summary is well-formed (starts with 'Commander amplifies')",
           summary.startswith("Commander amplifies"))
    summary = commander_amplifier_summary(baylen_style)
    t.true("Baylen-style summary mentions token doublers",
           "token doublers" in summary)

    t.report_and_exit()


if __name__ == "__main__":
    main()
