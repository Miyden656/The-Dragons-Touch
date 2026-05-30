"""v1.6.1 Phase 2 — Banned-commander eligibility gate tests.

Verifies that the Commander Discovery layer drops legendary creatures (and
special-rule command-zone cards) that Scryfall marks as banned in Commander,
while still surfacing legal commanders, and that the allow_banned_commanders
opt-in correctly resurfaces them with a BANNED warning.

Uses synthetic Scryfall + collection fixtures so no project data is required.

Run from project root:  py -3 tests/test_banned_commander_eligibility.py
"""
from _test_helpers import TestRun

from commander_discovery.eligibility import (
    ELIGIBILITY_STATUS_ELIGIBLE,
    ELIGIBILITY_STATUS_MANUAL_REVIEW,
    ELIGIBILITY_STATUS_NOT_CANDIDATE,
    RULE_BANNED_COMMANDER,
    RULE_BASIC_LEGENDARY_CREATURE,
    classify_commander_eligibility,
    is_banned_commander_candidate,
    is_commander_discovery_candidate,
)
from commander_discovery.collection_scanner import scan_collection_for_commanders


def _legendary_creature(
    name: str,
    *,
    commander_legality: str = "legal",
    color_identity: list[str] | None = None,
    oracle_text: str = "",
) -> dict:
    """Minimal Scryfall-shaped legendary creature record."""
    return {
        "name": name,
        "type_line": "Legendary Creature — Human Wizard",
        "cmc": 4,
        "color_identity": color_identity if color_identity is not None else ["U"],
        "oracle_text": oracle_text or f"{name} does something interesting.",
        "legalities": {"commander": commander_legality},
    }


def _legendary_planeswalker_commander(name: str, *, commander_legality: str) -> dict:
    """Synthetic planeswalker-commander record (says 'can be your commander')."""
    return {
        "name": name,
        "type_line": "Legendary Planeswalker — Test",
        "cmc": 5,
        "color_identity": ["B"],
        "oracle_text": f"{name} can be your commander.\n[+1]: Do a thing.",
        "legalities": {"commander": commander_legality},
    }


def main() -> None:
    t = TestRun("test_banned_commander_eligibility")

    # ----- is_banned_commander_candidate primitive --------------------------
    legal_legend = _legendary_creature("Atraxa, Praetors' Voice")
    banned_legend = _legendary_creature("Old Banned Lord", commander_legality="banned")
    non_legendary_card = {
        "name": "Lightning Bolt",
        "type_line": "Instant",
        "cmc": 1,
        "color_identity": ["R"],
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "legalities": {"commander": "banned"},
    }
    banned_walker_cmdr = _legendary_planeswalker_commander(
        "Banned Walker", commander_legality="banned"
    )

    t.true("legal legendary creature is NOT a banned-commander candidate",
           not is_banned_commander_candidate(legal_legend))
    t.true("banned legendary creature IS a banned-commander candidate",
           is_banned_commander_candidate(banned_legend))
    t.true("non-legendary banned card is NOT a banned-commander candidate "
           "(it can't be a commander at all)",
           not is_banned_commander_candidate(non_legendary_card))
    t.true("banned planeswalker-commander IS a banned-commander candidate",
           is_banned_commander_candidate(banned_walker_cmdr))
    t.true("None input returns False", not is_banned_commander_candidate(None))

    # ----- classify_commander_eligibility default = banned dropped ---------
    cls = classify_commander_eligibility(banned_legend)
    t.eq("default: banned legend status is NOT_CANDIDATE",
         cls.status, ELIGIBILITY_STATUS_NOT_CANDIDATE)
    t.eq("default: banned legend rule is banned_commander",
         cls.rule, RULE_BANNED_COMMANDER)
    t.true("default: banned legend NOT included in discovery",
           cls.include_in_discovery is False)
    t.true("default: banned legend is_mvp_eligible is False",
           cls.is_mvp_eligible is False)

    cls = classify_commander_eligibility(legal_legend)
    t.eq("default: legal legend status is ELIGIBLE",
         cls.status, ELIGIBILITY_STATUS_ELIGIBLE)
    t.eq("default: legal legend rule is basic_legendary_creature",
         cls.rule, RULE_BASIC_LEGENDARY_CREATURE)
    t.true("default: legal legend included in discovery",
           cls.include_in_discovery is True)
    t.true("default: legal legend is_mvp_eligible is True",
           cls.is_mvp_eligible is True)

    cls = classify_commander_eligibility(banned_walker_cmdr)
    t.eq("default: banned planeswalker-cmdr status is NOT_CANDIDATE",
         cls.status, ELIGIBILITY_STATUS_NOT_CANDIDATE)
    t.eq("default: banned planeswalker-cmdr rule is banned_commander",
         cls.rule, RULE_BANNED_COMMANDER)

    # ----- classify_commander_eligibility custom mode = banned surfaced ----
    cls = classify_commander_eligibility(banned_legend, allow_banned_commanders=True)
    t.eq("custom mode: banned legend status is ELIGIBLE",
         cls.status, ELIGIBILITY_STATUS_ELIGIBLE)
    t.eq("custom mode: banned legend rule is banned_commander",
         cls.rule, RULE_BANNED_COMMANDER)
    t.true("custom mode: special_rule_note contains 'BANNED'",
           "BANNED" in cls.special_rule_note)
    t.true("custom mode: at least one manual_review_note contains 'BANNED'",
           any("BANNED" in note for note in cls.manual_review_notes))
    t.true("custom mode: banned legend NOT marked is_mvp_eligible (loud-flag)",
           cls.is_mvp_eligible is False)
    t.true("custom mode: is_special_rule_candidate True (so UI labels it)",
           cls.is_special_rule_candidate is True)

    cls = classify_commander_eligibility(banned_walker_cmdr, allow_banned_commanders=True)
    t.eq("custom mode: banned planeswalker-cmdr status is MANUAL_REVIEW",
         cls.status, ELIGIBILITY_STATUS_MANUAL_REVIEW)
    t.eq("custom mode: banned planeswalker-cmdr rule is banned_commander",
         cls.rule, RULE_BANNED_COMMANDER)

    cls = classify_commander_eligibility(legal_legend, allow_banned_commanders=True)
    t.eq("custom mode: legal legend still ELIGIBLE",
         cls.status, ELIGIBILITY_STATUS_ELIGIBLE)
    t.eq("custom mode: legal legend still basic_legendary_creature rule",
         cls.rule, RULE_BASIC_LEGENDARY_CREATURE)

    # ----- is_commander_discovery_candidate behavior -----------------------
    t.true("default: banned legend NOT a discovery candidate",
           not is_commander_discovery_candidate(banned_legend))
    t.true("custom mode: banned legend IS a discovery candidate",
           is_commander_discovery_candidate(banned_legend, allow_banned_commanders=True))
    t.true("legal legend is a discovery candidate",
           is_commander_discovery_candidate(legal_legend))

    # ----- End-to-end: scanner drops banned commanders + counts them -------
    # Build a synthetic CollectionLoadSummary-like dict the scanner accepts.
    def _entry(card: dict, qty: int = 1) -> dict:
        return {
            "scryfall_name": card["name"],
            "card_name": card["name"],
            "quantity": qty,
            "source_file": "fixture.txt",
        }

    # Cards: 2 legal legends, 2 banned legends, 1 non-legendary card.
    legal_a = _legendary_creature("Atraxa, Praetors' Voice", color_identity=["W", "U", "B", "G"])
    legal_b = _legendary_creature("Korvold, Fae-Cursed King", color_identity=["B", "R", "G"])
    banned_a = _legendary_creature("Test Banned Lord A", commander_legality="banned", color_identity=["R"])
    banned_b = _legendary_creature("Test Banned Lord B", commander_legality="banned", color_identity=["G"])
    non_legendary = {
        "name": "Random Mountain",
        "type_line": "Basic Land — Mountain",
        "cmc": 0,
        "color_identity": ["R"],
        "oracle_text": "{T}: Add {R}.",
        "legalities": {"commander": "legal"},
    }

    collection_summary = {
        "entries": [
            _entry(legal_a, 1),
            _entry(legal_b, 2),
            _entry(banned_a, 1),
            _entry(banned_b, 1),
            _entry(non_legendary, 8),
        ],
        "parse_warnings": [],
    }
    scryfall_lookup = {
        c["name"].lower(): c for c in [legal_a, legal_b, banned_a, banned_b, non_legendary]
    }

    # Default mode: banned legends excluded from candidates.
    result = scan_collection_for_commanders(collection_summary, scryfall_lookup)
    candidate_names = {c.card_name for c in result.candidates}
    t.true("default: Atraxa appears as candidate", "Atraxa, Praetors' Voice" in candidate_names)
    t.true("default: Korvold appears as candidate", "Korvold, Fae-Cursed King" in candidate_names)
    t.true("default: Banned Lord A NOT a candidate", "Test Banned Lord A" not in candidate_names)
    t.true("default: Banned Lord B NOT a candidate", "Test Banned Lord B" not in candidate_names)
    t.eq("default: banned_commanders_skipped == 2", result.banned_commanders_skipped, 2)
    t.eq("default: skipped_nonlegendary_cards == 1 (just the Mountain)",
         result.skipped_nonlegendary_cards, 1)
    t.true("default: allow_banned_commanders is False on result",
           result.allow_banned_commanders is False)
    t.eq("default: mvp_candidate_count == 2", result.mvp_candidate_count, 2)

    # Custom mode: banned legends surface as candidates with the BANNED rule.
    result = scan_collection_for_commanders(
        collection_summary, scryfall_lookup, allow_banned_commanders=True,
    )
    candidate_names = {c.card_name for c in result.candidates}
    t.true("custom mode: Banned Lord A appears as candidate",
           "Test Banned Lord A" in candidate_names)
    t.true("custom mode: Banned Lord B appears as candidate",
           "Test Banned Lord B" in candidate_names)
    t.eq("custom mode: banned_commanders_skipped == 0 "
         "(they're surfaced, not skipped)", result.banned_commanders_skipped, 0)
    t.true("custom mode: allow_banned_commanders is True on result",
           result.allow_banned_commanders is True)
    # The banned candidates must carry the loud BANNED warning so the UI can label them.
    banned_candidates = [c for c in result.candidates if c.card_name.startswith("Test Banned Lord")]
    for cand in banned_candidates:
        t.true(f"custom mode: {cand.card_name} eligibility_rule is banned_commander",
               cand.eligibility_rule == RULE_BANNED_COMMANDER)
        t.true(f"custom mode: {cand.card_name} special_commander_rule contains 'BANNED'",
               "BANNED" in cand.special_commander_rule)

    t.report_and_exit()


if __name__ == "__main__":
    main()
