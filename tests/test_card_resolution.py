"""v1.6.1 Phase 4 — shared Scryfall card-name resolution tests.

Verifies the new data/card_resolution.py module resolves cards by:
  - exact lowercase
  - normalized (whitespace / case variants)
  - per-face name (split cards, MDFCs, rooms)
  - printed_name (alt-language reprints)
  - flavor_name (Universes Within style)

Also confirms the deck builder uses the smart resolver — a synthetic owned
card with a split-card face name resolves to the full split-card record
and lands in the deck.

Uses synthetic fixtures so no project data is required.

Run from project root:  py -3 tests/test_card_resolution.py
"""
from _test_helpers import TestRun

from data.card_resolution import (
    build_card_resolution_indexes,
    resolve_card_simple,
    resolve_card_in_indexes,
    normalize_lookup_key,
    collector_key,
)
from build_from_collection.full_100_card_draft_builder import build_full_100_card_draft


def main() -> None:
    t = TestRun("test_card_resolution")

    # ----- normalize_lookup_key -------------------------------------------
    t.eq("normalize None -> ''", normalize_lookup_key(None), "")
    t.eq("normalize empty -> ''", normalize_lookup_key(""), "")
    t.eq("normalize spaces collapsed",
         normalize_lookup_key("  Sol  Ring  "), "sol ring")
    t.eq("normalize newlines -> space",
         normalize_lookup_key("Fire\n//\nIce"), "fire // ice")
    t.eq("normalize unicode preserved",
         normalize_lookup_key("Lim-Dûl's Vault"), "lim-dûl's vault")

    # ----- collector_key --------------------------------------------------
    t.eq("collector_key basic", collector_key("IKO", "225"), ("iko", "225"))
    t.eq("collector_key star removed", collector_key("STA", "29★"), ("sta", "29"))
    t.eq("collector_key None set -> None", collector_key(None, "100"), None)
    t.eq("collector_key None num -> None", collector_key("DOM", None), None)

    # ----- build_card_resolution_indexes ----------------------------------
    fire_ice = {
        "name": "Fire // Ice",
        "type_line": "Instant // Instant",
        "card_faces": [
            {"name": "Fire", "type_line": "Instant", "oracle_text": "Fire deals 2 damage."},
            {"name": "Ice", "type_line": "Instant", "oracle_text": "Tap target permanent."},
        ],
        "set": "apc",
        "collector_number": "128",
        "legalities": {"commander": "legal"},
        "color_identity": ["U", "R"],
    }
    lim_dul = {
        "name": "Lim-Dûl's Vault",
        "type_line": "Instant",
        "set": "all",
        "collector_number": "14",
        "legalities": {"commander": "legal"},
        "color_identity": ["U", "B"],
    }
    flavored_reprint = {
        "name": "Lightning Wave",
        "flavor_name": "Lightning Surge",
        "type_line": "Instant",
        "set": "sld",
        "collector_number": "99",
        "legalities": {"commander": "legal"},
        "color_identity": ["R"],
    }
    foreign_print = {
        "name": "Counterspell",
        "printed_name": "Contramágica",
        "type_line": "Instant",
        "set": "lea",
        "collector_number": "55",
        "legalities": {"commander": "legal"},
        "color_identity": ["U"],
    }

    scryfall_cards = [fire_ice, lim_dul, flavored_reprint, foreign_print]
    scryfall_lookup = {c["name"].lower(): c for c in scryfall_cards}
    indexes = build_card_resolution_indexes(scryfall_lookup, scryfall_cards)

    # Index contents
    t.in_set("'fire // ice' indexed by exact",
             "fire // ice", indexes["exact_name"])
    t.in_set("face name 'fire' indexed in alternates",
             "fire", indexes["alternate_name"])
    t.in_set("face name 'ice' indexed in alternates",
             "ice", indexes["alternate_name"])
    t.in_set("flavor_name 'lightning surge' indexed",
             "lightning surge", indexes["alternate_name"])
    t.in_set("printed_name 'contramágica' indexed",
             "contramágica", indexes["alternate_name"])
    t.in_set("set+collector ('apc','128') indexed",
             ("apc", "128"), indexes["set_collector"])

    # ----- resolve_card_in_indexes (full collection resolver) -------------
    name, found, method, rec = resolve_card_in_indexes(
        "Fire // Ice", None, None, scryfall_lookup, indexes)
    t.true("full exact match (Fire // Ice)", found and method == "exact_name" and rec is fire_ice)

    name, found, method, rec = resolve_card_in_indexes(
        "  fire // ice  ", None, None, scryfall_lookup, indexes)
    t.true("full match via normalized name (whitespace + case)",
           found and rec is fire_ice)

    name, found, method, rec = resolve_card_in_indexes(
        "Fire", None, None, scryfall_lookup, indexes)
    t.true("full match via face name", found
           and method == "printed_or_alternate_name" and rec is fire_ice)

    name, found, method, rec = resolve_card_in_indexes(
        "Lightning Surge", None, None, scryfall_lookup, indexes)
    t.true("full match via flavor_name", found and rec is flavored_reprint)

    name, found, method, rec = resolve_card_in_indexes(
        "Contramágica", None, None, scryfall_lookup, indexes)
    t.true("full match via printed_name", found and rec is foreign_print)

    name, found, method, rec = resolve_card_in_indexes(
        "Some Card", "apc", "128", scryfall_lookup, indexes)
    t.true("full match via set+collector", found
           and method == "set_collector" and rec is fire_ice)

    name, found, method, rec = resolve_card_in_indexes(
        "Not A Real Card", None, None, scryfall_lookup, indexes)
    t.true("not-found returns method='not_found'",
           not found and method == "not_found" and rec is None)

    # ----- resolve_card_simple (build-time resolver) ----------------------
    t.true("simple resolves exact",
           resolve_card_simple("Fire // Ice", scryfall_lookup, indexes) is fire_ice)
    t.true("simple resolves face name",
           resolve_card_simple("Fire", scryfall_lookup, indexes) is fire_ice)
    t.true("simple resolves face name (case+space mismatch)",
           resolve_card_simple("  ICE  ", scryfall_lookup, indexes) is fire_ice)
    t.true("simple resolves flavor name",
           resolve_card_simple("Lightning Surge", scryfall_lookup, indexes) is flavored_reprint)
    t.true("simple resolves printed name",
           resolve_card_simple("Contramágica", scryfall_lookup, indexes) is foreign_print)
    t.true("simple returns None on miss",
           resolve_card_simple("Not A Real Card", scryfall_lookup, indexes) is None)
    t.true("simple returns None on empty",
           resolve_card_simple("", scryfall_lookup, indexes) is None)
    t.true("simple builds indexes on demand when None passed",
           resolve_card_simple("Fire", scryfall_lookup, None) is fire_ice)

    # ----- End-to-end: builder uses smart resolver ------------------------
    # Build a synthetic collection where one card is referenced by a face
    # name ("Fire") in the owned_cards list. The builder must resolve it to
    # the full "Fire // Ice" record and include it in the deck.
    commander = {
        "name": "Test Izzet Lord",
        "type_line": "Legendary Creature — Dragon Wizard",
        "cmc": 6,
        "color_identity": ["U", "R"],
        "oracle_text": "Whenever you cast an instant or sorcery spell, draw a card.",
        "legalities": {"commander": "legal"},
    }
    builder_lookup = dict(scryfall_lookup)
    builder_lookup[commander["name"].lower()] = commander
    owned_cards = [
        # Referenced by FACE NAME — only resolves with the smart resolver.
        {"name": "Fire", "owned_quantity": 1, "source_files": ["test.txt"],
         "oracle_text": "Fire deals 2 damage.", "type_line": "Instant"},
        # Referenced by FLAVOR NAME — only resolves with the smart resolver.
        {"name": "Lightning Surge", "owned_quantity": 1, "source_files": ["test.txt"],
         "oracle_text": "", "type_line": ""},
    ]
    # Add enough plain cards so the deck can hit 100 (or close).
    for i in range(30):
        c = {
            "name": f"Bolt Strike {i}",
            "type_line": "Instant",
            "cmc": 1,
            "color_identity": ["R"],
            "oracle_text": "Deal 3 damage to any target.",
            "legalities": {"commander": "legal"},
        }
        builder_lookup[c["name"].lower()] = c
        owned_cards.append({
            "name": c["name"], "owned_quantity": 1, "source_files": ["test.txt"],
            "oracle_text": c["oracle_text"], "type_line": c["type_line"],
        })
    for i in range(30):
        c = {
            "name": f"Dragon Apprentice {i}",
            "type_line": "Creature — Dragon Wizard",
            "cmc": 3,
            "color_identity": ["U", "R"],
            "oracle_text": "Flying.",
            "legalities": {"commander": "legal"},
        }
        builder_lookup[c["name"].lower()] = c
        owned_cards.append({
            "name": c["name"], "owned_quantity": 1, "source_files": ["test.txt"],
            "oracle_text": c["oracle_text"], "type_line": c["type_line"],
        })

    result = build_full_100_card_draft(
        commander_candidate={"commander_name": commander["name"], "color_identity_key": "UR"},
        owned_cards=owned_cards,
        scryfall_lookup=builder_lookup,
        primary_strategy="",
        secondary_strategy="",
        bracket_preference="Bracket 3 — Strong Casual",
        sub_philosophy="",
    )
    deck_names = {e.card_name for e in result.entries}
    t.in_set("face-name 'Fire' resolved to 'Fire // Ice' in final deck",
             "Fire // Ice", deck_names)
    t.in_set("flavor-name 'Lightning Surge' resolved to 'Lightning Wave' in deck",
             "Lightning Wave", deck_names)
    # Neither alias should appear as its alias — the builder must use the
    # canonical name from the resolved record.
    t.not_in_set("alias 'Fire' did NOT appear under its face name", "Fire", deck_names)
    t.not_in_set("alias 'Lightning Surge' did NOT appear under its flavor name",
                 "Lightning Surge", deck_names)
    t.eq("scryfall_unmatched_count == 0 (everything resolved)",
         result.scryfall_unmatched_count, 0)

    t.report_and_exit()


if __name__ == "__main__":
    main()
