"""Phase 6a tests: the verified card-fact tools (grounding layer).

Runs against the REAL local Scryfall data (skips cleanly if it isn't built).
Asserts the tools report accurate per-format legality + oracle facts, never
invent a card, and that the safety net now cross-checks ban claims against the
real legality data. Run via tests/run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun, load_scryfall_or_skip

from ai.commander_ai_safety import (
    BAN_CONTRADICTED,
    BAN_UNVERIFIED,
    LEGALITY_CONTRADICTED,
    verify_response,
)
from ai.commander_ai_tools import (
    BANNED,
    LEGAL,
    NOT_LEGAL,
    RESTRICTED,
    UNKNOWN,
    all_format_legality,
    find_known_card_names,
    is_banned_in,
    legality_in,
    lookup_card_facts,
    render_card_facts_block,
    resolve_facts_for_text,
)
from ai.schemas.ai_context import CommanderAIContext


def main() -> None:
    t = TestRun("ai_tools")
    lookup = load_scryfall_or_skip()

    # --- lookup_card_facts: verified facts for a real card ---
    sol = lookup_card_facts("sol ring", lookup)  # lower-case in -> canonical out
    t.true("Sol Ring found", sol is not None and sol.found)
    t.eq("canonical name", sol.name, "Sol Ring")
    t.true("type line is artifact", "Artifact" in sol.type_line)
    t.true("mana value resolved", sol.mana_value is not None)
    t.true("oracle text present", "add" in sol.oracle_text.lower())

    # --- per-format legality is accurate (this is the north-star claim) ---
    t.eq("Sol Ring commander legal", sol.legality("commander"), LEGAL)
    t.eq("Sol Ring legacy banned", sol.legality("legacy"), BANNED)
    t.eq("Sol Ring vintage restricted", sol.legality("vintage"), RESTRICTED)
    t.eq("Sol Ring modern not legal", sol.legality("modern"), NOT_LEGAL)
    t.eq("format key normalized (EDH-ish input)", sol.legality(" Commander "), LEGAL)

    # --- a banned-in-commander card ---
    t.eq("Mana Crypt commander banned", legality_in("Mana Crypt", "commander", lookup), BANNED)
    t.eq("Black Lotus commander banned", legality_in("Black Lotus", "commander", lookup), BANNED)

    # --- is_banned_in tri-state ---
    t.eq("Mana Crypt banned True", is_banned_in("Mana Crypt", "commander", lookup), True)
    t.eq("Sol Ring not banned (commander)", is_banned_in("Sol Ring", "commander", lookup), False)
    t.eq("nonexistent card -> None", is_banned_in("Zzz Not A Real Card", "commander", lookup), None)

    # --- no invention: unknown name returns None / UNKNOWN ---
    t.eq("fake card not found", lookup_card_facts("Zzz Not A Real Card", lookup), None)
    t.eq("fake card legality unknown", legality_in("Zzz Not A Real Card", "commander", lookup), UNKNOWN)
    t.eq("empty lookup -> None", lookup_card_facts("Sol Ring", None), None)

    # --- all_format_legality table ---
    table = all_format_legality("Sol Ring", lookup)
    t.in_set("legality table has commander", "commander", table)
    t.true("legality table is broad (>15 formats)", len(table) > 15)
    t.eq("fake card -> empty table", all_format_legality("Zzz Not A Real Card", lookup), {})

    # --- find_known_card_names: pull real cards out of free text ---
    names = find_known_card_names(
        "Is Sol Ring legal in Legacy? And what about Black Lotus and Mana Crypt?", lookup
    )
    t.in_set("found Sol Ring in text", "Sol Ring", names)
    t.in_set("found Black Lotus in text", "Black Lotus", names)
    t.in_set("found Mana Crypt in text", "Mana Crypt", names)
    t.not_in_set("did not treat 'Legacy' as a card", "Legacy", names)
    t.not_in_set("did not treat 'Is' as a card", "Is", names)

    # --- resolve_facts_for_text + exclude ---
    facts = resolve_facts_for_text("Should I run Sol Ring or Mana Crypt?", lookup)
    t.true("resolved >=2 cards", len(facts) >= 2)
    facts_ex = resolve_facts_for_text(
        "Should I run Sol Ring or Mana Crypt?", lookup, exclude={"sol ring"}
    )
    t.true("exclude drops Sol Ring", all(f.name != "Sol Ring" for f in facts_ex))

    # --- render block ---
    block = render_card_facts_block(facts)
    t.true("block has header", "Verified card facts" in block)
    t.true("block names Sol Ring", "Sol Ring" in block)
    t.true("block shows commander legality", "Commander/EDH" in block)
    t.eq("empty facts -> empty block", render_card_facts_block([]), "")

    # --- safety net now cross-checks bans against real legality ---
    ctx = CommanderAIContext()  # no engine-listed bans -> force the Scryfall path

    # model claims a legal card is banned -> contradicted (a real fabrication)
    r = verify_response(
        "Sol Ring is banned in Commander, so cut it.", ctx, scryfall_lookup=lookup
    )
    t.in_set("legal-card ban claim contradicted", BAN_CONTRADICTED, r.kinds())
    t.true("contradiction names Sol Ring", any(f.card == "Sol Ring" for f in r.flags))

    # model claims an actually-banned card is banned -> NOT flagged
    r = verify_response(
        "Mana Crypt is banned in Commander now.", ctx, scryfall_lookup=lookup
    )
    t.not_in_set("true commander ban not contradicted", BAN_CONTRADICTED, r.kinds())
    t.not_in_set("true commander ban not unverified", BAN_UNVERIFIED, r.kinds())

    # format-aware: Sol Ring IS banned in Legacy -> accurate, not flagged
    r = verify_response("Sol Ring is banned in Legacy.", ctx, scryfall_lookup=lookup)
    t.not_in_set("true legacy ban not contradicted", BAN_CONTRADICTED, r.kinds())

    # without a lookup, behavior is unchanged (soft 'unverified' flag)
    r = verify_response("Sol Ring is banned in Commander.", ctx)
    t.in_set("no-lookup falls back to unverified", BAN_UNVERIFIED, r.kinds())

    # --- structured legality statements (the qwen2.5 'restricted in Legacy' bug) ---
    r = verify_response("Sol Ring is restricted in Legacy.", ctx, scryfall_lookup=lookup)
    t.in_set("wrong status (restricted vs banned) flagged", LEGALITY_CONTRADICTED, r.kinds())
    t.true("legality note states real status", any("banned in legacy" in f.note.lower() for f in r.flags))

    r = verify_response("Sol Ring is restricted in Vintage.", ctx, scryfall_lookup=lookup)
    t.not_in_set("correct restricted status not flagged", LEGALITY_CONTRADICTED, r.kinds())

    r = verify_response("Sol Ring is legal in Commander.", ctx, scryfall_lookup=lookup)
    t.not_in_set("correct legal status not flagged", LEGALITY_CONTRADICTED, r.kinds())

    r = verify_response("Black Lotus is legal in Modern.", ctx, scryfall_lookup=lookup)
    t.in_set("wrong legal claim flagged", LEGALITY_CONTRADICTED, r.kinds())

    t.report_and_exit()


if __name__ == "__main__":
    main()
