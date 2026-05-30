"""v1.6.1 Phase 1 — Commander legality gate tests.

Verifies that build_full_100_card_draft() never includes Commander-banned cards
when allow_banned_cards=False (the default), at any bracket, and that the gate
correctly identifies a banned commander.

This test uses small SYNTHETIC scryfall + collection fixtures so it runs without
the full scryfall_cards.json. It does NOT depend on the user's collection or
combo data.

Run from project root:  py -3 tests/test_legality_gate.py
"""
from _test_helpers import TestRun

from legality.build_legality_gate import (
    get_commander_legality,
    is_card_banned_in_commander,
    is_card_not_legal_in_commander,
    is_card_legal_in_commander,
    should_exclude_from_commander_build,
    LEGALITY_LEGAL,
    LEGALITY_NOT_LEGAL,
    LEGALITY_BANNED,
    LEGALITY_UNKNOWN,
    EXCLUDE_REASON_BANNED,
    EXCLUDE_REASON_NOT_LEGAL,
)
from build_from_collection.full_100_card_draft_builder import build_full_100_card_draft


def _card(
    name: str,
    *,
    commander_legality: str = "legal",
    type_line: str = "Creature — Dragon",
    cmc: float = 4.0,
    color_identity: list[str] | None = None,
    oracle_text: str = "",
) -> dict:
    """Build a minimal Scryfall-shaped card record for tests."""
    return {
        "name": name,
        "type_line": type_line,
        "cmc": cmc,
        "color_identity": color_identity if color_identity is not None else ["R"],
        "oracle_text": oracle_text or f"{name} does something.",
        "legalities": {"commander": commander_legality},
    }


def main() -> None:
    t = TestRun("test_legality_gate")

    # ----- Unit tests on the gate primitives ----------------------------------
    legal_card = _card("Lightning Bolt", commander_legality="legal", type_line="Instant", cmc=1, color_identity=["R"])
    banned_card = _card("Channel", commander_legality="banned", type_line="Sorcery", cmc=1, color_identity=["G"])
    not_legal_card = _card("Throat Wolf", commander_legality="not_legal")
    unknown_card = {"name": "Mystery", "type_line": "Creature", "cmc": 2, "color_identity": [], "legalities": {}}
    missing_field_card = {"name": "Older", "type_line": "Creature", "cmc": 2, "color_identity": []}

    t.eq("get_commander_legality(legal)", get_commander_legality(legal_card), LEGALITY_LEGAL)
    t.eq("get_commander_legality(banned)", get_commander_legality(banned_card), LEGALITY_BANNED)
    t.eq("get_commander_legality(not_legal)", get_commander_legality(not_legal_card), LEGALITY_NOT_LEGAL)
    t.eq("get_commander_legality(missing field)", get_commander_legality(unknown_card), LEGALITY_UNKNOWN)
    t.eq("get_commander_legality(no legalities key)", get_commander_legality(missing_field_card), LEGALITY_UNKNOWN)
    t.eq("get_commander_legality(None)", get_commander_legality(None), LEGALITY_UNKNOWN)

    t.true("is_card_banned_in_commander(banned)", is_card_banned_in_commander(banned_card))
    t.true("is_card_banned_in_commander(legal) -> False", not is_card_banned_in_commander(legal_card))
    t.true("is_card_not_legal_in_commander(not_legal)", is_card_not_legal_in_commander(not_legal_card))
    t.true("is_card_not_legal_in_commander(legal) -> False", not is_card_not_legal_in_commander(legal_card))
    t.true("is_card_legal_in_commander(legal)", is_card_legal_in_commander(legal_card))
    t.true("is_card_legal_in_commander(banned) -> False", not is_card_legal_in_commander(banned_card))

    # ----- should_exclude_from_commander_build behavior ----------------------
    excluded, reason = should_exclude_from_commander_build(legal_card)
    t.true("legal card not excluded (default)", excluded is False and reason == "")

    excluded, reason = should_exclude_from_commander_build(banned_card)
    t.true("banned card excluded with reason=banned (default)",
           excluded is True and reason == EXCLUDE_REASON_BANNED)

    excluded, reason = should_exclude_from_commander_build(banned_card, allow_banned_cards=True)
    t.true("banned card allowed in custom mode",
           excluded is False and reason == "")

    excluded, reason = should_exclude_from_commander_build(not_legal_card)
    t.true("not_legal card excluded (default)",
           excluded is True and reason == EXCLUDE_REASON_NOT_LEGAL)

    excluded, reason = should_exclude_from_commander_build(not_legal_card, allow_banned_cards=True)
    t.true("not_legal card STILL excluded in custom mode",
           excluded is True and reason == EXCLUDE_REASON_NOT_LEGAL)

    excluded, reason = should_exclude_from_commander_build(unknown_card)
    t.true("unknown-legality card not excluded (don't drop on missing data)",
           excluded is False and reason == "")

    # ----- End-to-end: banned card never enters generated deck ---------------
    # Build a synthetic owned collection that includes 1 banned card + a bunch
    # of legal creatures + ramp + draw + removal + protection so the builder
    # has a real pool to work from. Commander identity is red.
    commander = _card(
        "Test Dragon Lord",
        commander_legality="legal",
        type_line="Legendary Creature — Dragon",
        cmc=6,
        color_identity=["R"],
        oracle_text="Whenever Test Dragon Lord attacks, deal 3 damage to any target.",
    )

    scryfall_lookup: dict[str, dict] = {commander["name"].lower(): commander}
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

    # The poisonous one — Commander banned. (Channel is banned IRL; we mark it
    # banned in the fixture too.)
    add(banned_card)
    # An always-not-legal card (silver-border style).
    add(not_legal_card)
    # 80 legal cards: a mix so all role buckets can fill.
    for i in range(20):
        add(_card(f"Mountain Wanderer {i}", type_line="Creature — Dragon", cmc=4, oracle_text="Flying."))
    for i in range(15):
        add(_card(
            f"Rampant Sprout {i}",
            type_line="Sorcery", cmc=2,
            oracle_text="Search your library for a basic land card and put it onto the battlefield.",
        ))
    for i in range(15):
        add(_card(
            f"Insightful Draw {i}",
            type_line="Instant", cmc=2,
            oracle_text="Draw two cards.",
        ))
    for i in range(15):
        add(_card(
            f"Sharp Removal {i}",
            type_line="Instant", cmc=2,
            oracle_text="Destroy target creature.",
        ))
    for i in range(15):
        add(_card(
            f"Brave Bodyguard {i}",
            type_line="Instant", cmc=1,
            oracle_text="Target creature gains hexproof and indestructible until end of turn.",
        ))

    # ----- Build at each bracket; banned card must never appear -------------
    brackets = [
        "Bracket 1 — Low Power / Precon-Friendly",
        "Bracket 2 — Casual Upgraded",
        "Bracket 3 — Strong Casual",
        "Bracket 4 — High Power",
        "Bracket 5 — cEDH / Competitive",
    ]
    for bracket in brackets:
        result = build_full_100_card_draft(
            commander_candidate={"commander_name": commander["name"], "color_identity_key": "R"},
            owned_cards=owned_cards,
            scryfall_lookup=scryfall_lookup,
            primary_strategy="",
            secondary_strategy="",
            bracket_preference=bracket,
            sub_philosophy="",
        )
        names = {e.card_name for e in result.entries}
        label = bracket.split("—")[0].strip()
        t.true(f"{label}: banned card not in deck", banned_card["name"] not in names)
        t.true(f"{label}: not-legal card not in deck", not_legal_card["name"] not in names)
        t.true(f"{label}: legality_banned_excluded_count >= 1",
               result.legality_banned_excluded_count >= 1)
        t.true(f"{label}: legality_not_legal_excluded_count >= 1",
               result.legality_not_legal_excluded_count >= 1)
        t.true(f"{label}: commander_is_banned is False", result.commander_is_banned is False)
        t.true(f"{label}: allow_banned_cards is False", result.allow_banned_cards is False)
        # Notes should mention the legality gate firing.
        gate_note_found = any("Legality gate" in n for n in result.notes)
        t.true(f"{label}: notes mention 'Legality gate'", gate_note_found)

    # ----- Custom mode: banned cards allowed --------------------------------
    result = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"], "color_identity_key": "R"},
        owned_cards=owned_cards,
        scryfall_lookup=scryfall_lookup,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
        allow_banned_cards=True,
    )
    names = {e.card_name for e in result.entries}
    t.true("CUSTOM MODE: banned card MAY appear in deck (banned color matches?)",
           # banned_card is green-identity (Channel-like). Commander is red.
           # The COLOR-IDENTITY filter still rejects it. Confirm at least the
           # legality gate didn't reject it: counter is zero in custom mode.
           result.legality_banned_excluded_count == 0)
    t.true("CUSTOM MODE: allow_banned_cards is True", result.allow_banned_cards is True)
    t.true("CUSTOM MODE: not-legal card STILL not in deck",
           not_legal_card["name"] not in names)
    custom_note_found = any("CUSTOM MODE" in n for n in result.notes)
    t.true("CUSTOM MODE: notes mention 'CUSTOM MODE'", custom_note_found)

    # ----- Banned commander warning -----------------------------------------
    banned_commander = _card(
        "Test Banned Lord",
        commander_legality="banned",
        type_line="Legendary Creature — Demon",
        cmc=6,
        color_identity=["R"],
    )
    scryfall_lookup[banned_commander["name"].lower()] = banned_commander
    result = build_full_100_card_draft(
        commander_candidate={"commander_name": banned_commander["name"], "color_identity_key": "R"},
        owned_cards=owned_cards,
        scryfall_lookup=scryfall_lookup,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    t.true("banned commander flagged on result", result.commander_is_banned is True)
    warn_found = any("BANNED" in n for n in result.notes)
    t.true("banned commander surfaces WARNING in notes", warn_found)

    t.report_and_exit()


if __name__ == "__main__":
    main()
