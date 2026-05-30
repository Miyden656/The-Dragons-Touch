"""v1.6.1 Phase 3 — creature-skeleton tests.

Verifies:
  1. classify_creature_band picks the right band for each strategy family.
  2. is_creature_type_line handles plain creatures, MDFC, split, and creature lands.
  3. End-to-end builder enforces the creature ceiling so even a creature-heavy
     synthetic collection produces a deck within the band for the chosen
     strategy.

Uses synthetic fixtures so no project data is required.

Run from project root:  py -3 tests/test_creature_skeleton.py
"""
from _test_helpers import TestRun

from build_from_collection.creature_skeleton import (
    BAND_CREATURE_HEAVY,
    BAND_CREATURE_LITE,
    BAND_CREATURE_MID,
    BAND_DEFAULT,
    CATEGORY_CREATURE_HEAVY,
    CATEGORY_CREATURE_LITE,
    CATEGORY_CREATURE_MID,
    CATEGORY_DEFAULT,
    classify_creature_band,
    creature_band_status_label,
    is_creature_type_line,
)
from build_from_collection.full_100_card_draft_builder import build_full_100_card_draft


def _card(
    name: str,
    *,
    type_line: str = "Creature — Dragon",
    cmc: float = 4.0,
    color_identity: list[str] | None = None,
    oracle_text: str = "",
    commander_legality: str = "legal",
) -> dict:
    return {
        "name": name,
        "type_line": type_line,
        "cmc": cmc,
        "color_identity": color_identity if color_identity is not None else ["R"],
        "oracle_text": oracle_text or f"{name} does a thing.",
        "legalities": {"commander": commander_legality},
    }


def main() -> None:
    t = TestRun("test_creature_skeleton")

    # ----- is_creature_type_line ------------------------------------------
    t.true("plain creature", is_creature_type_line("Creature — Dragon"))
    t.true("legendary creature", is_creature_type_line("Legendary Creature — Human Wizard"))
    t.true("artifact creature", is_creature_type_line("Artifact Creature — Construct"))
    t.true("MDFC creature/sorcery", is_creature_type_line("Creature — Elf // Sorcery"))
    t.true("split: instant//creature", is_creature_type_line("Instant // Creature — Spirit"))
    t.true("creature land NOT classified as creature",
           not is_creature_type_line("Land — Forest Creature"))
    t.true("plain land NOT a creature", not is_creature_type_line("Basic Land — Mountain"))
    t.true("instant NOT a creature", not is_creature_type_line("Instant"))
    t.true("planeswalker NOT a creature", not is_creature_type_line("Legendary Planeswalker — Jace"))
    t.true("empty string handled", not is_creature_type_line(""))
    t.true("None handled", not is_creature_type_line(None))

    # ----- classify_creature_band by TAGS ----------------------------------
    # Heavy: typal tags
    band = classify_creature_band(strategy_tags={"tribal_payoff", "creature_type_present", "token_maker"})
    t.eq("typal -> HEAVY", band.category, CATEGORY_CREATURE_HEAVY)
    # Heavy: aristocrats
    band = classify_creature_band(strategy_tags={"sacrifice_outlet", "death_trigger_payoff", "etb_value"})
    t.eq("aristocrats -> HEAVY", band.category, CATEGORY_CREATURE_HEAVY)
    # Lite: voltron tags
    band = classify_creature_band(strategy_tags={"equipment_synergy", "aura_synergy", "go_tall_support"})
    # go_tall_support is in HEAVY but equipment+aura push toward LITE. Tag
    # resolver favors LITE on ties; this combo has 2 lite vs 1 heavy.
    t.eq("voltron equipment -> LITE", band.category, CATEGORY_CREATURE_LITE)
    # Lite: control
    band = classify_creature_band(strategy_tags={"counterspell", "board_wipe", "free_interaction"})
    t.eq("control -> LITE", band.category, CATEGORY_CREATURE_LITE)
    # Lite: combo
    band = classify_creature_band(strategy_tags={"combo_piece_possible", "win_condition", "efficient_tutor"})
    t.eq("combo -> LITE", band.category, CATEGORY_CREATURE_LITE)
    # Mid: lifegain
    band = classify_creature_band(strategy_tags={"lifegain_payoff", "ramp", "mana_rock"})
    t.eq("lifegain ramp -> MID", band.category, CATEGORY_CREATURE_MID)
    # Mid: landfall
    band = classify_creature_band(strategy_tags={"landfall", "landfall_payoff", "lands_matter"})
    t.eq("landfall -> MID", band.category, CATEGORY_CREATURE_MID)

    # ----- classify_creature_band by LABEL (no tags) ----------------------
    band = classify_creature_band(strategy_tags=set(), primary_strategy_label="[Macro] Dragons")
    t.eq("'Dragons' label -> HEAVY", band.category, CATEGORY_CREATURE_HEAVY)
    band = classify_creature_band(strategy_tags=set(), primary_strategy_label="[Macro] Voltron")
    t.eq("'Voltron' label -> LITE", band.category, CATEGORY_CREATURE_LITE)
    band = classify_creature_band(strategy_tags=set(), primary_strategy_label="[Macro] Spellslinger")
    t.eq("'Spellslinger' label -> LITE", band.category, CATEGORY_CREATURE_LITE)
    band = classify_creature_band(strategy_tags=set(), primary_strategy_label="[Macro] Ramp / Big Mana")
    t.eq("'Ramp / Big Mana' label -> MID", band.category, CATEGORY_CREATURE_MID)
    band = classify_creature_band(strategy_tags=set(), primary_strategy_label="")
    t.eq("empty label -> DEFAULT", band.category, CATEGORY_DEFAULT)
    band = classify_creature_band(strategy_tags=set(), primary_strategy_label="Some Custom Thing")
    t.eq("unknown label -> DEFAULT", band.category, CATEGORY_DEFAULT)

    # ----- band status labels ---------------------------------------------
    # Avoid printing the unicode markers themselves in test labels —
    # the Windows cp1252 console can't render them — just probe content.
    label = creature_band_status_label(BAND_CREATURE_HEAVY, 26)
    t.true("within band status text contains 'within band'", "within band" in label)
    label = creature_band_status_label(BAND_CREATURE_HEAVY, 18)
    t.true("below floor status text contains 'below floor'", "below floor" in label)
    label = creature_band_status_label(BAND_CREATURE_HEAVY, 38)
    t.true("above ceiling status text contains 'above ceiling'", "above ceiling" in label)

    # ----- End-to-end: ceiling holds even with creature-heavy collection ---
    # Commander is a red Dragon, strategy is non-creature (control), so band
    # should be LITE (ceiling 20). Collection has 60 creatures + a handful of
    # noncreature support spells. The builder MUST cap creatures around the
    # ceiling and prefer noncreature spells for Strategy + Flex when possible.
    commander = _card(
        "Test Red Control Lord",
        type_line="Legendary Creature — Dragon Wizard",
        cmc=6,
        color_identity=["R"],
        oracle_text=(
            "Whenever you cast an instant or sorcery spell, counter target spell "
            "unless its controller pays 2."
        ),
    )

    scryfall_lookup = {commander["name"].lower(): commander}
    owned_cards: list[dict] = []

    def add(card: dict, qty: int = 1) -> None:
        scryfall_lookup[card["name"].lower()] = card
        owned_cards.append({
            "name": card["name"],
            "owned_quantity": qty,
            "source_files": ["test.txt"],
            "oracle_text": card.get("oracle_text", ""),
            "type_line": card.get("type_line", ""),
        })

    # 50 creatures available. We want the ceiling to actually HOLD here, so
    # we need enough noncreature support that the builder's safety-net pass
    # doesn't have to relax the ceiling. 50 creatures + ~75 noncreatures of
    # various roles is plenty for the LITE ceiling of 20 to bind.
    for i in range(50):
        add(_card(
            f"Volcanic Beast {i}",
            type_line="Creature — Dragon",
            cmc=4 + (i % 4),
            oracle_text="Flying.\nWhenever this creature attacks, deal 1 damage.",
        ))
    # Noncreature spells across utility roles. ~75 total so even the LITE
    # ceiling has plenty of headroom for the deck to reach 100 cards without
    # relaxing.
    for i in range(20):
        add(_card(
            f"Wisdom Cantrip {i}",
            type_line="Instant", cmc=2,
            oracle_text="Draw two cards.",
        ))
    for i in range(15):
        add(_card(
            f"Burn Surge {i}",
            type_line="Sorcery", cmc=3,
            oracle_text="Destroy target creature.",
        ))
    for i in range(10):
        add(_card(
            f"Counterforce {i}",
            type_line="Instant", cmc=2,
            oracle_text="Counter target spell.",
        ))
    for i in range(8):
        add(_card(
            f"Bracer {i}",
            type_line="Instant", cmc=1,
            oracle_text="Target creature gains hexproof and indestructible until end of turn.",
        ))
    for i in range(20):
        add(_card(
            f"Treasure Smash {i}",
            type_line="Sorcery", cmc=2,
            oracle_text="Search your library for a basic land card and put it onto the battlefield tapped.",
        ))
    for i in range(5):
        add(_card(
            f"Mass Burn {i}",
            type_line="Sorcery", cmc=5,
            oracle_text="Destroy all creatures.",
        ))

    # Build with a control / spellslinger strategy label -> LITE band, ceiling 20.
    result = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"], "color_identity_key": "R"},
        owned_cards=owned_cards,
        scryfall_lookup=scryfall_lookup,
        primary_strategy="[Macro] Control",
        secondary_strategy="[Macro] Spellslinger",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )

    t.eq("LITE band classified for Control + Spellslinger",
         result.creature_band_category, CATEGORY_CREATURE_LITE)
    t.eq("LITE band floor = 12", result.creature_band_floor, 12)
    t.eq("LITE band ceiling = 20", result.creature_band_ceiling, 20)
    t.true(f"creature_count ({result.creature_count}) <= ceiling (20)",
           result.creature_count <= 20)
    # When Control noncreatures naturally outscore creatures in Strategy fits,
    # the ceiling may not need to fire — the scoring chain holds the line on
    # its own. We just confirm the ceiling didn't get relaxed (no extra
    # creatures past it).
    t.eq("creatures_added_past_ceiling == 0 (ceiling honored naturally)",
         result.creatures_added_past_ceiling, 0)
    t.eq("total_cards == 100", result.total_cards, 100)
    # Verify the report verdict line shows up.
    skeleton_note_found = any("Creature skeleton" in n for n in result.notes)
    t.true("notes mention 'Creature skeleton'", skeleton_note_found)

    # Now build the SAME collection with a HEAVY strategy and confirm the
    # ceiling rises so the deck IS allowed to be creature-heavy.
    result_heavy = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"], "color_identity_key": "R"},
        owned_cards=owned_cards,
        scryfall_lookup=scryfall_lookup,
        primary_strategy="[Macro] Dragons",
        secondary_strategy="[Tribal] Dragons",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    t.eq("HEAVY band classified for Dragons typal",
         result_heavy.creature_band_category, CATEGORY_CREATURE_HEAVY)
    t.true(f"HEAVY ceiling is higher than LITE (heavy.ceiling {result_heavy.creature_band_ceiling} "
           f"> lite.ceiling {result.creature_band_ceiling})",
           result_heavy.creature_band_ceiling > result.creature_band_ceiling)
    t.true(f"HEAVY creature_count ({result_heavy.creature_count}) > LITE creature_count "
           f"({result.creature_count})",
           result_heavy.creature_count > result.creature_count)
    t.true(f"HEAVY creature_count ({result_heavy.creature_count}) <= ceiling "
           f"({result_heavy.creature_band_ceiling})",
           result_heavy.creature_count <= result_heavy.creature_band_ceiling)

    # Collection-thin-on-noncreatures: should bump ceiling and surface a note.
    # Same Control strategy but collection has only 5 noncreature spells.
    scryfall_lookup_thin = {commander["name"].lower(): commander}
    owned_thin: list[dict] = []

    def add_thin(card: dict, qty: int = 1) -> None:
        scryfall_lookup_thin[card["name"].lower()] = card
        owned_thin.append({
            "name": card["name"],
            "owned_quantity": qty,
            "source_files": ["test.txt"],
            "oracle_text": card.get("oracle_text", ""),
            "type_line": card.get("type_line", ""),
        })

    for i in range(80):
        add_thin(_card(f"Smol Drake {i}", type_line="Creature — Drake", cmc=3))
    for i in range(5):
        add_thin(_card(f"Tiny Cantrip {i}", type_line="Instant", cmc=1,
                       oracle_text="Draw a card."))

    result_thin = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"], "color_identity_key": "R"},
        owned_cards=owned_thin,
        scryfall_lookup=scryfall_lookup_thin,
        primary_strategy="[Macro] Control",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    t.eq("thin collection: total still 100", result_thin.total_cards, 100)
    t.true(f"thin collection: creatures_added_past_ceiling > 0 "
           f"(got {result_thin.creatures_added_past_ceiling})",
           result_thin.creatures_added_past_ceiling > 0)
    relax_note_found = any("past the creature ceiling" in n for n in result_thin.notes)
    t.true("thin collection: surfaces the relax note",
           relax_note_found)

    t.report_and_exit()


if __name__ == "__main__":
    main()
