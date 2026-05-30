"""v1.6.1 Phase 7 — Build Validation report tests.

Verifies:
  1. compute_build_verdict() picks the right verdict for each scenario:
     LEGAL / LEGAL_BUT_WEAK / COLLECTION_LIMITED / ILLEGAL / CUSTOM_MODE.
  2. The report block contains the required sections (Legality, Role
     breakdown, Creature density, Bracket expectations, Diagnostic counts).
  3. The block surfaces collection-readiness notes when there are real
     shortfalls and omits them when the deck is clean.
  4. End-to-end: build_full_100_card_draft renders a markdown report that
     includes the Build Validation section with the expected verdict.

Uses synthetic Full100CardDraftResult-like objects so we can drive every
verdict deterministically without a real Scryfall.

Run from project root:  py -3 tests/test_build_validation_report.py
"""
from _test_helpers import TestRun

from build_from_collection.build_validation_report import (
    VERDICT_COLLECTION_LIMITED,
    VERDICT_CUSTOM_MODE,
    VERDICT_ILLEGAL,
    VERDICT_LEGAL,
    VERDICT_LEGAL_BUT_WEAK,
    build_validation_report_lines,
    build_validation_top_line,
    compute_bracket_expectations_status,
    compute_build_verdict,
    compute_collection_readiness_status,
)
from build_from_collection.full_100_card_draft_builder import (
    Full100CardDraftResult,
    build_full_100_card_draft,
    render_full_100_card_draft_markdown,
)


def _result(**overrides) -> Full100CardDraftResult:
    """Construct a Full100CardDraftResult with reasonable defaults + overrides."""
    base = dict(
        commander_name="Test Lord",
        color_identity=["R"],
        primary_strategy="",
        secondary_strategy="",
        entries=[],
        role_counts={"Commander": 1, "Lands": 37, "Ramp": 10, "Card Draw": 10,
                     "Removal": 7, "Protection": 3, "Strategy": 25, "Flex": 7},
        missing_slots={},
        total_cards=100,
        notes=[],
        collection_cards_analyzed=500,
        scryfall_unmatched_count=0,
        color_identity_excluded_count=10,
        legality_banned_excluded_count=0,
        legality_not_legal_excluded_count=0,
        legality_restricted_excluded_count=0,
        bracket_excluded_count=0,
        allow_banned_cards=False,
        commander_is_banned=False,
        creature_count=24,
        noncreature_nonland_count=38,
        creature_band_category="creature_default",
        creature_band_floor=16,
        creature_band_target=22,
        creature_band_ceiling=28,
        creatures_skipped_for_ceiling=0,
        creatures_added_past_ceiling=0,
    )
    base.update(overrides)
    return Full100CardDraftResult(**base)


def main() -> None:
    t = TestRun("test_build_validation_report")

    # ----- compute_build_verdict: LEGAL ----------------------------------
    clean = _result()
    t.eq("clean build -> LEGAL", compute_build_verdict(clean), VERDICT_LEGAL)
    t.true("LEGAL top line has 'LEGAL'",
           "LEGAL" in build_validation_top_line(clean))

    # ----- compute_build_verdict: LEGAL_BUT_WEAK -------------------------
    weak = _result(missing_slots={"Protection": 2})
    t.eq("missing_slots -> LEGAL_BUT_WEAK",
         compute_build_verdict(weak), VERDICT_LEGAL_BUT_WEAK)
    t.true("LEGAL_BUT_WEAK top line mentions 'structurally weak'",
           "structurally weak" in build_validation_top_line(weak))

    # ----- compute_build_verdict: COLLECTION_LIMITED ---------------------
    relaxed = _result(creatures_added_past_ceiling=4, creature_count=32)
    t.eq("ceiling relaxed -> COLLECTION_LIMITED",
         compute_build_verdict(relaxed), VERDICT_COLLECTION_LIMITED)
    below_floor = _result(creature_count=10)  # default floor 16
    t.eq("below creature floor -> COLLECTION_LIMITED",
         compute_build_verdict(below_floor), VERDICT_COLLECTION_LIMITED)

    # ----- compute_build_verdict: ILLEGAL (banned commander) -------------
    banned_cmdr = _result(commander_is_banned=True)
    t.eq("banned commander -> ILLEGAL",
         compute_build_verdict(banned_cmdr), VERDICT_ILLEGAL)
    t.true("ILLEGAL top line mentions 'ILLEGAL'",
           "ILLEGAL" in build_validation_top_line(banned_cmdr))

    # ----- compute_build_verdict: ILLEGAL (wrong size) -------------------
    short_deck = _result(total_cards=95)
    t.eq("99 cards -> ILLEGAL", compute_build_verdict(short_deck), VERDICT_ILLEGAL)

    # ----- compute_build_verdict: CUSTOM_MODE ----------------------------
    custom = _result(allow_banned_cards=True)
    t.eq("allow_banned_cards=True -> CUSTOM_MODE",
         compute_build_verdict(custom), VERDICT_CUSTOM_MODE)
    custom_with_banned_cmdr = _result(allow_banned_cards=True, commander_is_banned=True)
    t.eq("allow_banned_cards=True + banned commander -> CUSTOM_MODE",
         compute_build_verdict(custom_with_banned_cmdr), VERDICT_CUSTOM_MODE)
    t.true("CUSTOM_MODE top line mentions 'CUSTOM MODE'",
           "CUSTOM MODE" in build_validation_top_line(custom))

    # ----- compute_collection_readiness_status ---------------------------
    t.eq("clean build has empty readiness list",
         compute_collection_readiness_status(clean), [])
    readiness = compute_collection_readiness_status(relaxed)
    t.true("ceiling-relaxed: readiness mentions ceiling",
           any("ceiling" in line.lower() for line in readiness))
    readiness = compute_collection_readiness_status(below_floor)
    t.true("below-floor: readiness mentions floor",
           any("floor" in line.lower() for line in readiness))
    weak_readiness = compute_collection_readiness_status(weak)
    t.true("missing-slots: readiness mentions bucket name",
           any("Protection" in line for line in weak_readiness))
    unmatched = _result(scryfall_unmatched_count=5)
    t.true("scryfall-unmatched: readiness mentions Scryfall",
           any("Scryfall" in line for line in compute_collection_readiness_status(unmatched)))

    # ----- compute_bracket_expectations_status ---------------------------
    bracket_status = compute_bracket_expectations_status(clean)
    t.true("clean: bracket status mentions filter ran",
           "filter" in bracket_status.lower())
    bracket_with_excludes = _result(bracket_excluded_count=12)
    bracket_status = compute_bracket_expectations_status(bracket_with_excludes)
    t.true("with excludes: status mentions count",
           "12" in bracket_status)

    # ----- build_validation_report_lines structural check ---------------
    block = build_validation_report_lines(clean)
    block_text = "\n".join(block)
    t.true("section header present", "## Build Validation" in block_text)
    t.true("legality sub-section present", "### Legality" in block_text)
    t.true("role breakdown sub-section present",
           "### Role breakdown vs target" in block_text)
    t.true("creature density sub-section present",
           "### Creature density vs band" in block_text)
    t.true("bracket sub-section present", "### Bracket expectations" in block_text)
    t.true("diagnostic counts sub-section present",
           "### Diagnostic counts" in block_text)
    t.true("legal commander line present (Commander: PASS marker)",
           "Commander: ✓" in block_text)
    t.true("banned-card filter line present",
           "Banned-card filter:" in block_text)
    t.true("deck size 100 line present", "100 cards" in block_text)

    # ----- build_validation_report_lines on ILLEGAL build ---------------
    banned_block_text = "\n".join(build_validation_report_lines(banned_cmdr))
    t.true("banned commander block shows BANNED marker for commander",
           "Commander: ❌ BANNED" in banned_block_text)
    t.true("banned commander block shows ILLEGAL badge",
           "❌ ILLEGAL" in banned_block_text)

    # ----- build_validation_report_lines on CUSTOM_MODE build -----------
    custom_block_text = "\n".join(build_validation_report_lines(custom))
    t.true("custom mode block shows DISABLED banned filter",
           "DISABLED" in custom_block_text)
    t.true("custom mode block shows CUSTOM MODE badge",
           "CUSTOM MODE" in custom_block_text)

    # ----- LEGAL_BUT_WEAK shows short bucket in role breakdown ---------
    weak_block_text = "\n".join(build_validation_report_lines(weak))
    t.true("weak block shows 'short by' marker in role breakdown",
           "short by 2" in weak_block_text)

    # ----- End-to-end: real builder render includes the block -----------
    commander = {
        "name": "Test Red Dragon Lord",
        "type_line": "Legendary Creature — Dragon",
        "cmc": 6,
        "color_identity": ["R"],
        "oracle_text": "Flying. Whenever Test Red Dragon Lord attacks, deal 2 damage to any target.",
        "legalities": {"commander": "legal"},
    }
    scryfall_lookup = {commander["name"].lower(): commander}
    owned_cards = []
    # Enough cards to fill 100 cleanly: ~25 creatures, 25 ramp, 25 draw, 25 removal.
    for i in range(25):
        c = {"name": f"Hot Dragon {i}", "type_line": "Creature — Dragon", "cmc": 4,
             "color_identity": ["R"], "oracle_text": "Flying.",
             "legalities": {"commander": "legal"}}
        scryfall_lookup[c["name"].lower()] = c
        owned_cards.append({"name": c["name"], "owned_quantity": 1, "source_files": ["t.txt"],
                            "oracle_text": c["oracle_text"], "type_line": c["type_line"]})
    for i in range(15):
        c = {"name": f"Quick Ramp {i}", "type_line": "Sorcery", "cmc": 2,
             "color_identity": ["R"],
             "oracle_text": "Search your library for a basic land card and put it onto the battlefield.",
             "legalities": {"commander": "legal"}}
        scryfall_lookup[c["name"].lower()] = c
        owned_cards.append({"name": c["name"], "owned_quantity": 1, "source_files": ["t.txt"],
                            "oracle_text": c["oracle_text"], "type_line": c["type_line"]})
    for i in range(15):
        c = {"name": f"Quick Draw {i}", "type_line": "Instant", "cmc": 2,
             "color_identity": ["R"], "oracle_text": "Draw two cards.",
             "legalities": {"commander": "legal"}}
        scryfall_lookup[c["name"].lower()] = c
        owned_cards.append({"name": c["name"], "owned_quantity": 1, "source_files": ["t.txt"],
                            "oracle_text": c["oracle_text"], "type_line": c["type_line"]})
    for i in range(15):
        c = {"name": f"Quick Burn {i}", "type_line": "Instant", "cmc": 2,
             "color_identity": ["R"], "oracle_text": "Destroy target creature.",
             "legalities": {"commander": "legal"}}
        scryfall_lookup[c["name"].lower()] = c
        owned_cards.append({"name": c["name"], "owned_quantity": 1, "source_files": ["t.txt"],
                            "oracle_text": c["oracle_text"], "type_line": c["type_line"]})
    for i in range(5):
        c = {"name": f"Quick Save {i}", "type_line": "Instant", "cmc": 1,
             "color_identity": ["R"],
             "oracle_text": "Target creature gains hexproof and indestructible until end of turn.",
             "legalities": {"commander": "legal"}}
        scryfall_lookup[c["name"].lower()] = c
        owned_cards.append({"name": c["name"], "owned_quantity": 1, "source_files": ["t.txt"],
                            "oracle_text": c["oracle_text"], "type_line": c["type_line"]})

    real_result = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"], "color_identity_key": "R"},
        owned_cards=owned_cards,
        scryfall_lookup=scryfall_lookup,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    md = render_full_100_card_draft_markdown(real_result)
    t.true("end-to-end: markdown includes Build Validation section",
           "## Build Validation" in md)
    t.true("end-to-end: markdown includes Role breakdown sub-section",
           "### Role breakdown vs target" in md)
    t.true("end-to-end: markdown includes Creature density sub-section",
           "### Creature density vs band" in md)
    t.true("end-to-end: markdown includes Bracket expectations sub-section",
           "### Bracket expectations" in md)
    t.true("end-to-end: markdown includes Diagnostic counts sub-section",
           "### Diagnostic counts" in md)
    # The verdict badge should appear early in the validation block.
    t.true("end-to-end: markdown includes a verdict badge (one of LEGAL/ILLEGAL/CUSTOM)",
           any(badge in md for badge in ("LEGAL", "ILLEGAL", "CUSTOM MODE")))

    t.report_and_exit()


if __name__ == "__main__":
    main()
