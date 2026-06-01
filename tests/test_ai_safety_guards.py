"""Phase 4 tests: the code-enforced safety / claim-checker.

Verifies that fabricated ownership, ban-status, and combo claims get flagged,
while engine-verified claims pass clean. Run via tests/run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun

from ai.commander_ai_safety import (
    BAN_CONTRADICTED,
    BAN_UNVERIFIED,
    COMBO_UNVERIFIED,
    LEGALITY_CONTRADICTED,
    OWNERSHIP_UNVERIFIED,
    verify_response,
)
from ai.schemas.ai_context import CommanderAIContext


def _ctx(combo_available: bool = False) -> CommanderAIContext:
    return CommanderAIContext(
        decklist=[{"name": "Sol Ring", "count": 1, "roles": ["ramp"]}],
        legality={"banned_cards": ["Channel"], "banned_commanders": []},
        replacements={"collection_candidates": [{"card": "Goblin Chieftain"}]},
        combo={"available": combo_available},
    )


def main() -> None:
    t = TestRun("ai_safety_guards")
    ctx = _ctx()

    # --- false ownership claim is flagged ---
    r = verify_response("You already own Dockside Extortionist, so add it.", ctx)
    t.eq("false ownership not ok", r.ok, False)
    t.in_set("ownership flag kind", OWNERSHIP_UNVERIFIED, r.kinds())
    t.true("flagged the right card", any(f.card == "Dockside Extortionist" for f in r.flags))
    t.true("footer appended in strict mode", "Fact-check notes" in r.annotated_text)
    t.true("footer names the card", "Dockside Extortionist" in r.annotated_text)

    # --- verified ownership passes ---
    r = verify_response("You own Goblin Chieftain, which is great here.", ctx)
    t.not_in_set("verified owned not flagged", OWNERSHIP_UNVERIFIED, r.kinds())

    # --- a deck card claimed as 'run' passes ---
    r = verify_response("Since you run Sol Ring, ramp is fine.", ctx)
    t.not_in_set("deck card not flagged as unowned", OWNERSHIP_UNVERIFIED, r.kinds())

    # --- false ban claim is flagged ---
    r = verify_response("Mana Crypt is banned in Commander now.", ctx)
    t.in_set("false ban flagged", BAN_UNVERIFIED, r.kinds())
    t.true("ban flag names Mana Crypt", any(f.card == "Mana Crypt" for f in r.flags))

    # --- verified ban passes ---
    r = verify_response("Note that Channel is banned, so it's excluded.", ctx)
    t.not_in_set("verified ban not flagged", BAN_UNVERIFIED, r.kinds())

    # --- 'not banned' must NOT trigger a ban flag ---
    r = verify_response("Lightning Bolt is not banned, so it's fine.", ctx)
    t.not_in_set("'not banned' does not flag", BAN_UNVERIFIED, r.kinds())

    # --- combo claim flagged when combo awareness wasn't run ---
    r = verify_response("These two pieces make an infinite combo.", ctx)
    t.in_set("combo flagged when not run", COMBO_UNVERIFIED, r.kinds())

    # --- combo claim allowed when combo awareness WAS run ---
    r = verify_response("These two pieces make an infinite combo.", _ctx(combo_available=True))
    t.not_in_set("combo allowed when run", COMBO_UNVERIFIED, r.kinds())

    # --- clean response passes untouched ---
    clean = "This deck wants to go wide with goblin tokens and finish through combat."
    r = verify_response(clean, ctx)
    t.eq("clean response ok", r.ok, True)
    t.eq("clean response no flags", len(r.flags), 0)
    t.eq("clean response unchanged", r.annotated_text, clean)

    # --- strict=False returns flags but does not append footer ---
    r = verify_response("You own Dockside Extortionist.", ctx, strict=False)
    t.eq("non-strict still flags", r.ok, False)
    t.true("non-strict leaves text unannotated", "Fact-check notes" not in r.annotated_text)

    # --- None context does not crash ---
    raised = ""
    try:
        verify_response("You own Some Card and it is banned.", None)
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("None context did not crash", raised, "")

    # --- empty text is ok ---
    t.eq("empty text ok", verify_response("", ctx).ok, True)

    # --- precision fixes (Scryfall-grounded path): reduce false positives only ---
    scry = {
        "sol ring": {"name": "Sol Ring",
                     "legalities": {"legacy": "banned", "commander": "legal", "vintage": "restricted"}},
        "lightning bolt": {"name": "Lightning Bolt",
                           "legalities": {"modern": "legal", "commander": "legal"}},
    }
    # 1) a mis-extracted common word ("Now") is NOT flagged as an unverified ban,
    #    and the correct "Sol Ring is banned in Legacy" stays clean.
    r = verify_response("Now, Sol Ring is banned in Legacy.", ctx, scryfall_lookup=scry)
    t.not_in_set("common word 'Now' not ban-flagged", BAN_UNVERIFIED, r.kinds())
    t.eq("correct banned claim is clean", r.ok, True)
    # 2) "not legal" is true for a banned card -> not a contradiction.
    r = verify_response("Sol Ring is not legal in Legacy.", ctx, scryfall_lookup=scry)
    t.not_in_set("'not legal' for banned card not flagged", LEGALITY_CONTRADICTED, r.kinds())
    # 3) regression: calling a banned card "legal" IS still flagged (dangerous direction).
    r = verify_response("Sol Ring is legal in Legacy.", ctx, scryfall_lookup=scry)
    t.in_set("'legal' claim for banned card still flagged", LEGALITY_CONTRADICTED, r.kinds())
    # 4) regression: a real card wrongly called banned is still flagged.
    r = verify_response("Lightning Bolt is banned in Modern.", ctx, scryfall_lookup=scry)
    t.in_set("real card wrongly called banned still flagged", BAN_CONTRADICTED, r.kinds())

    t.report_and_exit()


if __name__ == "__main__":
    main()
