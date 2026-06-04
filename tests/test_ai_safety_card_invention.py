"""Safety net: flag SUGGESTED cards that don't exist in Scryfall.

Free-form coaching answers can invent plausible-sounding cards (observed:
"Mystic Remnant", "Sundering Blade") that the ownership/ban/combo checks miss.
This guard fires only inside markdown emphasis / quotes within a recommendation
sentence, so plain prose, role words, and section headers are never flagged.
Uses real Scryfall data; SKIPS cleanly if the card data isn't present.
"""
from __future__ import annotations

from _test_helpers import TestRun, load_scryfall_or_skip

from ai.commander_ai_safety import CARD_NOT_FOUND, verify_response


def _card_flags(text: str, lookup) -> list[str]:
    r = verify_response(text, None, scryfall_lookup=lookup, strict=False)
    return [f.card for f in r.flags if f.kind == CARD_NOT_FOUND]


def main() -> None:
    t = TestRun("ai_safety_card_invention")
    lookup = load_scryfall_or_skip()

    # --- recall: invented cards in a recommendation get flagged ---
    t.true("invented card in a swap suggestion is flagged",
           "Sundering Blade" in _card_flags("Consider swapping it for *Sundering Blade* for removal.", lookup))
    both = _card_flags("Could be replaced with something better (e.g., *Sundering Blade*, *Mystic Remnant*).", lookup)
    t.true("both invented cards in an e.g. list are flagged",
           "Sundering Blade" in both and "Mystic Remnant" in both)
    t.true("invented card in quotes is flagged",
           "Mystic Remnant" in _card_flags('I would add "Mystic Remnant" for protection.', lookup))

    # --- precision: real cards / prose / roles / headers are NOT flagged ---
    t.true("real card suggestion not flagged",
           not _card_flags("Add *Goblin Matron* to fetch your goblins.", lookup))
    t.true("real card without emphasis not flagged",
           not _card_flags("Consider adding Sol Ring for ramp.", lookup))
    t.true("emphasized role words not flagged",
           not _card_flags("Add more *targeted removal* and *protection*.", lookup))
    t.true("bold section header not flagged",
           not _card_flags("**Final Takeaway** — keep the cards you love.", lookup))
    t.true("plain prose not flagged",
           not _card_flags("This deck floods the board and drains the table's life.", lookup))
    t.true("real split card in a suggestion not flagged",
           not _card_flags("Try running *Fast // Furious* as a finisher.", lookup))

    # --- precision tightening (false positives found in the 114-deck shakedown) ---
    t.true("curly-apostrophe real card not flagged",
           not _card_flags("Consider adding *Ashnod’s Transmogrant* for ramp.", lookup))
    t.true("real card containing a concept word not flagged",
           not _card_flags("You could add *Mana Drain* as interaction.", lookup))
    t.true("slash-joined concept label not flagged",
           not _card_flags("Lean into strategies like *Token Combat / Go-Wide-Go-Tall*.", lookup))
    t.true("strategy concept phrase not flagged",
           not _card_flags("Consider a plan such as *Life Total Politics*.", lookup))
    t.true("genuine invented card still flagged after tightening",
           "Sundering Vortex" in _card_flags("Swap it for *Sundering Vortex* as a finisher.", lookup))

    # --- no lookup -> cannot verify -> never emits a card_not_found flag ---
    no_lookup = verify_response("Swap it for *Sundering Blade*.", None, scryfall_lookup=None, strict=False)
    t.true("no Scryfall lookup -> no card_not_found flags",
           not any(f.kind == CARD_NOT_FOUND for f in no_lookup.flags))

    t.report_and_exit()


if __name__ == "__main__":
    main()
