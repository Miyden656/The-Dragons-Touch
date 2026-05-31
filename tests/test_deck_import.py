"""Headless tests for the URL importer.

No live network. Every adapter is exercised with a FakeFetcher that
returns a canned response — same pattern the AI tests use for the
Ollama client. The final test renders text via cards_to_decklist_text
and pipes it through the engine's real parse_deck_file to confirm
end-to-end format compatibility.

Run via tests/run_all.py.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from _test_helpers import TestRun

from deck_import import (
    DeckImportResult,
    detect_source,
    import_from_url,
    SUPPORTED_SOURCES,
)
from deck_import.http import FetchResult
from deck_import.sources import archidekt, moxfield, mtggoldfish
from deck_import.types import (
    ImportedCard,
    cards_to_decklist_text,
    normalize_section,
)


# ---------------------------------------------------------------------------
# Fake fetchers
# ---------------------------------------------------------------------------


def _make_fetcher(responses):
    """Build a fetcher(url, *, timeout=None, headers=None) -> FetchResult.

    `responses` is a dict[url -> FetchResult]. Any unmatched URL returns a
    `not_found` FetchResult so tests fail loudly if the wrong endpoint is called.
    """
    calls: list[str] = []

    def fetcher(url, *, timeout=None, headers=None):
        calls.append(url)
        if url in responses:
            return responses[url]
        return FetchResult(ok=False, status=404, error_kind="not_found",
                           message=f"no fake response for {url}")

    fetcher.calls = calls  # type: ignore[attr-defined]
    return fetcher


def _moxfield_payload():
    return {
        "name": "Atraxa Superfriends",
        "format": "commander",
        "boards": {
            "commanders": {"cards": {
                "x1": {"quantity": 1, "card": {"name": "Atraxa, Praetors' Voice"}},
            }},
            "mainboard": {"cards": {
                "a1": {"quantity": 1, "card": {"name": "Sol Ring"}},
                "a2": {"quantity": 1, "card": {"name": "Arcane Signet"}},
                "a3": {"quantity": 1, "card": {"name": "Command Tower"}},
                "a4": {"quantity": 0, "card": {"name": "Ignored Zero"}},  # filtered
            }},
            "companions": {"cards": {}},
            "sideboard": {"cards": {}},
        },
    }


def _archidekt_payload():
    return {
        "name": "Krenko Goblins",
        "cards": [
            {"quantity": 1, "categories": ["Commander"], "card": {"oracleCard": {"name": "Krenko, Mob Boss"}}},
            {"quantity": 1, "categories": ["Ramp"], "card": {"oracleCard": {"name": "Sol Ring"}}},
            {"quantity": 1, "categories": [], "card": {"oracleCard": {"name": "Goblin Chieftain"}}},
            {"quantity": 1, "categories": ["Maybeboard"], "card": {"oracleCard": {"name": "Skirk Prospector"}}},
            {"quantity": 0, "categories": [], "card": {"oracleCard": {"name": "Ignored Zero"}}},
        ],
    }


def _mtggoldfish_arena_text():
    # MTGGoldfish arena_download format: explicit Commander/Deck headers + (SET) ### tail.
    return (
        "Commander\n"
        "1 Atraxa, Praetors' Voice (CMR) 245\n"
        "\n"
        "Deck\n"
        "1 Sol Ring (CMR) 269\n"
        "1 Arcane Signet (ELD) 331\n"
        "1 Command Tower (ELD) 333\n"
    )


def _mtggoldfish_arena_text_html_entities():
    # The bug the user hit in real testing: MTGGoldfish actually returns
    # apostrophes as the HTML entity `&#39;`. Make sure we decode them.
    return (
        "Commander\n"
        "1 Atraxa, Praetors&#39; Voice (CMR) 245\n"
        "\n"
        "Deck\n"
        "1 Kodama&#39;s Reach (CHK) 167\n"
        "1 Nature&#39;s Lore (3ED) 268\n"
        "1 Sol Ring (CMR) 269\n"
    )


def _mtggoldfish_flat_text():
    # Legacy /deck/download/ format: no headers, just one block. Reproduces the
    # bug where the commander was buried alphabetically in the mainboard.
    return (
        "1 Ajani Steadfast\n"
        "1 Arcane Signet\n"
        "1 Atraxa, Praetors' Voice\n"
        "1 Sol Ring\n"
    )


def _mtggoldfish_trailing_block_text():
    # Legacy format that DID separate the commander: mainboard, blank, single trailing card.
    return (
        "1 Sol Ring\n"
        "1 Arcane Signet\n"
        "1 Command Tower\n"
        "\n"
        "1 Atraxa, Praetors' Voice\n"
    )


def main() -> None:
    t = TestRun("deck_import")

    # -----------------------------------------------------------------------
    # detect_source / URL routing
    # -----------------------------------------------------------------------
    t.true("Moxfield URL routes to moxfield",
           detect_source("https://www.moxfield.com/decks/abc123") is moxfield)
    t.true("bare moxfield.com routes to moxfield",
           detect_source("moxfield.com/decks/abc123") is moxfield)
    t.true("Archidekt URL routes to archidekt",
           detect_source("https://archidekt.com/decks/5566778/some-slug") is archidekt)
    t.true("MTGGoldfish URL routes to mtggoldfish",
           detect_source("https://www.mtggoldfish.com/deck/123") is mtggoldfish)
    t.true("subdomain.moxfield.com still matches moxfield",
           detect_source("https://api.moxfield.com/decks/x") is moxfield)
    t.true("unsupported site returns None",
           detect_source("https://tappedout.net/mtg-decks/some-deck/") is None)
    t.true("empty URL returns None", detect_source("") is None)
    t.true("garbage URL returns None", detect_source("not a url") is None)

    # -----------------------------------------------------------------------
    # adapter.extract_deck_id
    # -----------------------------------------------------------------------
    t.eq("Moxfield id from /decks/<id>",
         moxfield.extract_deck_id(urlparse("https://www.moxfield.com/decks/abcDEF123")),
         "abcDEF123")
    t.eq("Moxfield id missing returns ''",
         moxfield.extract_deck_id(urlparse("https://www.moxfield.com/")), "")
    t.eq("Archidekt id from /decks/<digits>",
         archidekt.extract_deck_id(urlparse("https://archidekt.com/decks/123456/my-slug")),
         "123456")
    t.eq("Archidekt id non-numeric -> ''",
         archidekt.extract_deck_id(urlparse("https://archidekt.com/decks/abc")), "")
    t.eq("MTGGoldfish id from /deck/<id>",
         mtggoldfish.extract_deck_id(urlparse("https://www.mtggoldfish.com/deck/4567890")),
         "4567890")

    # -----------------------------------------------------------------------
    # Empty / invalid URL handling (no network)
    # -----------------------------------------------------------------------
    r = import_from_url("")
    t.eq("empty URL ok=False", r.ok, False)
    t.eq("empty URL error_kind invalid_url", r.error_kind, "invalid_url")

    r = import_from_url("https://tappedout.net/some-deck/")
    t.eq("unsupported site ok=False", r.ok, False)
    t.eq("unsupported site error_kind", r.error_kind, "unsupported_site")
    t.true("unsupported message lists supported sources",
           all(name in r.message for name in SUPPORTED_SOURCES), r.message)

    r = import_from_url("https://www.moxfield.com/")
    t.eq("Moxfield URL missing id -> invalid_url", r.error_kind, "invalid_url")

    # -----------------------------------------------------------------------
    # Moxfield happy path (FakeFetcher)
    # -----------------------------------------------------------------------
    mox_url = "https://api2.moxfield.com/v3/decks/all/MOX123"
    fetcher = _make_fetcher({
        mox_url: FetchResult(ok=True, status=200, text=json.dumps(_moxfield_payload())),
    })
    r = import_from_url("https://www.moxfield.com/decks/MOX123", fetcher=fetcher)
    t.eq("Moxfield ok=True", r.ok, True)
    t.eq("Moxfield source", r.source, "moxfield")
    t.eq("Moxfield deck_id passed through", r.deck_id, "MOX123")
    t.eq("Moxfield deck_name", r.deck_name, "Atraxa Superfriends")
    t.eq("Moxfield commander", r.commander, "Atraxa, Praetors' Voice")
    t.eq("Moxfield mainboard count", r.mainboard_count(), 3)
    t.eq("Moxfield total card count", r.card_count(), 4)
    t.true("Moxfield text starts with Commander header",
           r.decklist_text.startswith("Commander\n"), r.decklist_text[:80])
    t.true("Moxfield text contains Sol Ring", "Sol Ring" in r.decklist_text)
    t.true("Moxfield zero-qty card filtered out",
           "Ignored Zero" not in r.decklist_text, r.decklist_text)
    t.eq("Moxfield source_url preserved", r.source_url, "https://www.moxfield.com/decks/MOX123")
    t.true("Moxfield fetcher was called with v3 API URL",
           mox_url in fetcher.calls, str(fetcher.calls))

    # Moxfield: not_found error from server
    fetcher_404 = _make_fetcher({
        "https://api2.moxfield.com/v3/decks/all/NOPE": FetchResult(
            ok=False, status=404, error_kind="not_found", message="Deck not found."),
    })
    r = import_from_url("https://moxfield.com/decks/NOPE", fetcher=fetcher_404)
    t.eq("Moxfield 404 -> ok False", r.ok, False)
    t.eq("Moxfield 404 -> not_found", r.error_kind, "not_found")

    # Moxfield: bad JSON
    fetcher_bad = _make_fetcher({
        "https://api2.moxfield.com/v3/decks/all/BAD": FetchResult(
            ok=True, status=200, text="<html>not json</html>"),
    })
    r = import_from_url("https://moxfield.com/decks/BAD", fetcher=fetcher_bad)
    t.eq("Moxfield non-JSON -> bad_response", r.error_kind, "bad_response")

    # Moxfield: empty deck
    fetcher_empty = _make_fetcher({
        "https://api2.moxfield.com/v3/decks/all/EMPTY": FetchResult(
            ok=True, status=200, text=json.dumps({"name": "Empty", "boards": {"mainboard": {"cards": {}}}})),
    })
    r = import_from_url("https://moxfield.com/decks/EMPTY", fetcher=fetcher_empty)
    t.eq("Moxfield empty deck -> empty_deck", r.error_kind, "empty_deck")

    # -----------------------------------------------------------------------
    # Archidekt happy path
    # -----------------------------------------------------------------------
    arch_url = "https://archidekt.com/api/decks/777888/"
    fetcher = _make_fetcher({
        arch_url: FetchResult(ok=True, status=200, text=json.dumps(_archidekt_payload())),
    })
    r = import_from_url("https://archidekt.com/decks/777888/krenko-goblins", fetcher=fetcher)
    t.eq("Archidekt ok=True", r.ok, True)
    t.eq("Archidekt source", r.source, "archidekt")
    t.eq("Archidekt deck_id", r.deck_id, "777888")
    t.eq("Archidekt commander", r.commander, "Krenko, Mob Boss")
    t.true("Archidekt rolls 'Ramp' category into mainboard",
           "1 Sol Ring" in r.decklist_text, r.decklist_text)
    t.true("Archidekt keeps Maybeboard as its own section",
           "Maybeboard" in r.decklist_text and "Skirk Prospector" in r.decklist_text,
           r.decklist_text)
    t.true("Archidekt zero-qty filtered", "Ignored Zero" not in r.decklist_text)

    # Archidekt: blocked (private deck)
    fetcher_blk = _make_fetcher({
        "https://archidekt.com/api/decks/4242/": FetchResult(
            ok=False, status=403, error_kind="blocked", message="Private deck."),
    })
    r = import_from_url("https://archidekt.com/decks/4242", fetcher=fetcher_blk)
    t.eq("Archidekt 403 -> blocked", r.error_kind, "blocked")

    # -----------------------------------------------------------------------
    # MTGGoldfish: Arena-format primary endpoint (the new default).
    # -----------------------------------------------------------------------
    arena_url = "https://www.mtggoldfish.com/deck/arena_download/9999"
    fetcher = _make_fetcher({
        arena_url: FetchResult(ok=True, status=200, text=_mtggoldfish_arena_text()),
    })
    r = import_from_url("https://www.mtggoldfish.com/deck/9999#paper", fetcher=fetcher)
    t.eq("MTGGoldfish Arena ok=True", r.ok, True)
    t.eq("MTGGoldfish Arena source", r.source, "mtggoldfish")
    t.eq("MTGGoldfish Arena commander from header block",
         r.commander, "Atraxa, Praetors' Voice")
    t.eq("MTGGoldfish Arena mainboard count", r.mainboard_count(), 3)
    t.true("MTGGoldfish Arena text starts with Commander header",
           r.decklist_text.startswith("Commander\n"), r.decklist_text[:80])
    t.true("Arena (SET) ### tails stripped from names",
           "(CMR)" not in r.decklist_text and "(ELD)" not in r.decklist_text,
           r.decklist_text)
    t.true("MTGGoldfish hit Arena endpoint first",
           arena_url in fetcher.calls, str(fetcher.calls))

    # -----------------------------------------------------------------------
    # MTGGoldfish Arena: HTML entities (`&#39;` apostrophes) get decoded.
    # Reproduces the user-reported `Atraxa, Praetors&#39; Voice` issue.
    # -----------------------------------------------------------------------
    entity_url = "https://www.mtggoldfish.com/deck/arena_download/5555"
    fetcher = _make_fetcher({
        entity_url: FetchResult(ok=True, status=200,
                                text=_mtggoldfish_arena_text_html_entities()),
    })
    r = import_from_url("https://www.mtggoldfish.com/deck/5555", fetcher=fetcher)
    t.eq("MTGGoldfish HTML-entity import ok=True", r.ok, True)
    t.eq("Commander apostrophe decoded (no &#39;)",
         r.commander, "Atraxa, Praetors' Voice")
    t.true("Decklist text has no remaining &#39;",
           "&#39;" not in r.decklist_text, r.decklist_text)
    t.true("Decklist text has the real apostrophe",
           "Kodama's Reach" in r.decklist_text and "Nature's Lore" in r.decklist_text,
           r.decklist_text)

    # -----------------------------------------------------------------------
    # MTGGoldfish: legacy single-trailing-card heuristic (plain endpoint).
    # Arena endpoint failing falls back here.
    # -----------------------------------------------------------------------
    legacy_url = "https://www.mtggoldfish.com/deck/download/8888"
    fetcher = _make_fetcher({
        arena_url.replace("9999", "8888"): FetchResult(
            ok=False, status=404, error_kind="not_found", message="No arena export."),
        legacy_url: FetchResult(ok=True, status=200, text=_mtggoldfish_trailing_block_text()),
    })
    r = import_from_url("https://www.mtggoldfish.com/deck/8888", fetcher=fetcher)
    t.eq("MTGGoldfish fallback ok=True", r.ok, True)
    t.eq("MTGGoldfish fallback commander via trailing-block heuristic",
         r.commander, "Atraxa, Praetors' Voice")
    t.eq("MTGGoldfish fallback mainboard count", r.mainboard_count(), 3)

    # -----------------------------------------------------------------------
    # MTGGoldfish: BOTH endpoints failing surfaces a friendly error.
    # -----------------------------------------------------------------------
    fetcher = _make_fetcher({
        "https://www.mtggoldfish.com/deck/arena_download/7777": FetchResult(
            ok=False, status=404, error_kind="not_found", message="not found"),
        "https://www.mtggoldfish.com/deck/download/7777": FetchResult(
            ok=False, status=404, error_kind="not_found", message="not found"),
    })
    r = import_from_url("https://www.mtggoldfish.com/deck/7777", fetcher=fetcher)
    t.eq("MTGGoldfish both endpoints 404 -> ok False", r.ok, False)
    t.eq("MTGGoldfish both endpoints 404 -> not_found", r.error_kind, "not_found")

    # -----------------------------------------------------------------------
    # MTGGoldfish: the user's actual failure mode — flat block with no
    # headers (commander buried alphabetically). With the trailing-block
    # heuristic disabled because the entire deck is one block, we expect
    # NO commander to be detected. The fix is to use the Arena endpoint;
    # this test pins the documented fallback behavior so we know what to
    # expect if Arena ever stops working.
    # -----------------------------------------------------------------------
    flat_url = "https://www.mtggoldfish.com/deck/download/6666"
    fetcher = _make_fetcher({
        "https://www.mtggoldfish.com/deck/arena_download/6666": FetchResult(
            ok=False, status=404, error_kind="not_found", message="No arena export."),
        flat_url: FetchResult(ok=True, status=200, text=_mtggoldfish_flat_text()),
    })
    r = import_from_url("https://www.mtggoldfish.com/deck/6666", fetcher=fetcher)
    t.eq("MTGGoldfish flat-block fallback still imports cards", r.ok, True)
    t.eq("MTGGoldfish flat-block cards counted", r.mainboard_count(), 4)
    t.eq("MTGGoldfish flat-block: no commander identifiable (documented gap)",
         r.commander, "")

    # -----------------------------------------------------------------------
    # cards_to_decklist_text — formatting invariants
    # -----------------------------------------------------------------------
    text = cards_to_decklist_text([
        ImportedCard("Sol Ring", 1, "Mainboard"),
        ImportedCard("Arcane Signet", 1, "Mainboard"),
        ImportedCard("Krenko, Mob Boss", 1, "Commander"),
    ])
    lines = [l for l in text.splitlines() if l.strip()]
    t.eq("Commander header first", lines[0], "Commander")
    t.eq("Commander card next", lines[1], "1 Krenko, Mob Boss")
    t.in_set("Sol Ring rendered", "1 Sol Ring", lines)
    t.in_set("Arcane Signet rendered", "1 Arcane Signet", lines)
    t.eq("Deck header marks mainboard transition", lines.count("Deck"), 1)

    # Without a commander block, mainboard should be header-less (matches paste-tab).
    text_no_cmdr = cards_to_decklist_text([
        ImportedCard("Sol Ring", 1, "Mainboard"),
        ImportedCard("Arcane Signet", 1, "Mainboard"),
    ])
    lines_no_cmdr = [l for l in text_no_cmdr.splitlines() if l.strip()]
    t.eq("No 'Deck' header when no commander block", lines_no_cmdr.count("Deck"), 0)
    t.eq("No 'Commander' header when no commander block", lines_no_cmdr.count("Commander"), 0)

    t.eq("normalize_section Commander", normalize_section("Commanders"), "Commander")
    t.eq("normalize_section unknown -> Mainboard", normalize_section("Ramp"), "Mainboard")
    t.eq("normalize_section empty -> Mainboard", normalize_section(""), "Mainboard")
    t.eq("normalize_section Sideboard", normalize_section("Sideboard"), "Sideboard")

    # -----------------------------------------------------------------------
    # End-to-end: rendered text parses cleanly with the engine's deck parser
    # -----------------------------------------------------------------------
    from parsing.deck_parser import parse_deck_file

    fetcher = _make_fetcher({
        mox_url: FetchResult(ok=True, status=200, text=json.dumps(_moxfield_payload())),
    })
    r = import_from_url("https://www.moxfield.com/decks/MOX123", fetcher=fetcher)
    t.eq("Moxfield re-import ok=True", r.ok, True)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "imported.txt"
        path.write_text(r.decklist_text, encoding="utf-8")
        parsed = parse_deck_file(path)
        t.true("engine parser produced a ParsedDeck",
               parsed is not None and hasattr(parsed, "cards"))
        # Engine treats the Commander section as reference (not mainboard counted)
        # so the mainboard list should hold the 3 non-commander cards.
        t.in_set("engine parsed Sol Ring", "Sol Ring", parsed.cards)
        t.in_set("engine parsed Arcane Signet", "Arcane Signet", parsed.cards)
        t.in_set("engine parsed Command Tower", "Command Tower", parsed.cards)
        # Engine puts Commander-section cards in BOTH `cards` and `commander_names`.
        # The important thing for us is that the commander is correctly identified.
        t.in_set("engine identified Atraxa as commander",
                 "Atraxa, Praetors' Voice", parsed.commander_names)
        t.eq("engine set commander_name", parsed.commander_name, "Atraxa, Praetors' Voice")

    t.report_and_exit()


if __name__ == "__main__":
    main()
