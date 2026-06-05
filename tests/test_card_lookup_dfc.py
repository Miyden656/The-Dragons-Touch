"""Regression: build_scryfall_lookup adds front/back face aliases for double-faced
/ modal-DFC / Adventure / split / Battle cards, so a decklist that lists only the
front face (e.g. "Darkbore Pathway") resolves to the full "Front // Back" card.

Without this, those real cards were marked "not found in Scryfall", tagged
role-uncertain, and recommended as cuts. Synthetic + fast. Run via run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun

from data.card_lookup import build_scryfall_lookup


def main() -> None:
    t = TestRun("card_lookup_dfc")

    pathway = {
        "name": "Darkbore Pathway // Slitherbore Pathway",
        "type_line": "Land // Land",
        "card_faces": [
            {"name": "Darkbore Pathway", "type_line": "Land"},
            {"name": "Slitherbore Pathway", "type_line": "Land"},
        ],
    }
    fire_ice = {
        "name": "Fire // Ice",
        "type_line": "Instant // Instant",
        "card_faces": [
            {"name": "Fire", "type_line": "Instant"},
            {"name": "Ice", "type_line": "Instant"},
        ],
    }
    sol_ring = {"name": "Sol Ring", "type_line": "Artifact"}

    lookup = build_scryfall_lookup([pathway, fire_ice, sol_ring])

    # Full name still resolves (unchanged behavior).
    t.true("full DFC name resolves",
           lookup.get("darkbore pathway // slitherbore pathway") is pathway)
    # Front-face-only name now resolves to the full card.
    t.true("front-face name resolves", lookup.get("darkbore pathway") is pathway)
    # Back-face name also resolves (harmless, occasionally useful).
    t.true("back-face name resolves", lookup.get("slitherbore pathway") is pathway)
    # Split-card faces both resolve.
    t.true("split front resolves", lookup.get("fire") is fire_ice)
    t.true("split back resolves", lookup.get("ice") is fire_ice)
    # Plain single-faced cards are unaffected.
    t.true("single-faced card resolves", lookup.get("sol ring") is sol_ring)
    # Case-insensitive.
    t.true("case-insensitive front face", lookup.get("Darkbore Pathway".lower()) is pathway)

    # Collision guard: a genuine standalone card sharing a face name must WIN over
    # the alias (full names are inserted first; aliases use setdefault).
    standalone_fire = {"name": "Fire", "type_line": "Creature"}
    lookup2 = build_scryfall_lookup([fire_ice, standalone_fire])
    t.true("standalone card beats face alias", lookup2.get("fire") is standalone_fire)
    t.true("DFC full name still present", lookup2.get("fire // ice") is fire_ice)

    # Defensive: malformed faces don't crash.
    weird = {"name": "Weird", "card_faces": [None, {"no_name": True}, "junk"]}
    lookup3 = build_scryfall_lookup([weird])
    t.true("malformed faces tolerated", lookup3.get("weird") is weird)

    t.report_and_exit()


if __name__ == "__main__":
    main()
