"""Archidekt adapter.

Public URL:  https://archidekt.com/decks/<deckId>[/<slug>]
Public API:  https://archidekt.com/api/decks/<deckId>/

Response shape (relevant subset):

    {
      "name": "...",
      "categories": [
        {"name": "Commander", "includedInDeck": true},
        {"name": "TDT recommended Cut", "includedInDeck": false},
        ...
      ],
      "cards": [
        {
          "quantity": N,
          "categories": ["Commander", ...],
          "card": {
            "oracleCard": {"name": "..."},
            "name": "..."
          }
        },
        ...
      ]
    }

Archidekt models categories as user-defined buckets, each with an
`includedInDeck` flag that decides whether its cards count toward the
deck. We follow that flag: a card in any excluded bucket (the built-in
Maybeboard / Sideboard, or a custom cut pile) is set aside under
Maybeboard / Sideboard so the deck arrives at the size Archidekt shows;
Commander and Companion keep their own sections; every other bucket
("Ramp", "Removal", ...) is Mainboard, which matches how the engine
parses an exported text file.
"""

from deck_import.http import fetch as _default_fetch
from deck_import.types import (
    DeckImportResult,
    ImportedCard,
    cards_to_decklist_text,
    make_error,
)


NAME = "archidekt"
DOMAINS = ("archidekt.com", "www.archidekt.com")

_API_TEMPLATE = "https://archidekt.com/api/decks/{deck_id}/"


def extract_deck_id(parsed_url) -> str:
    parts = [p for p in parsed_url.path.split("/") if p]
    # /decks/<id> or /decks/<id>/<slug>
    if len(parts) >= 2 and parts[0].lower() == "decks":
        candidate = parts[1].strip()
        if candidate.isdigit():
            return candidate
    return ""


def _excluded_category_names(payload) -> set[str]:
    """Category names Archidekt does NOT count toward the deck size.

    Honors each category's `includedInDeck` flag, so a user's custom "cut" /
    considering pile (e.g. "TDT recommended Cut") is set aside exactly the way
    Archidekt itself sets it aside — this is what keeps an imported 100-card deck
    from arriving as 110. The built-in Maybeboard and Sideboard are always
    excluded, even when a deck's JSON omits the category definitions.
    """
    excluded = {"maybeboard", "sideboard"}
    cats = payload.get("categories") if isinstance(payload, dict) else None
    if isinstance(cats, list):
        for c in cats:
            if isinstance(c, dict) and c.get("includedInDeck") is False:
                name = (c.get("name") or "").strip().lower()
                if name:
                    excluded.add(name)
    return excluded


def _section_for(entry, excluded: set[str]) -> str:
    """Pick the canonical section for a card, matching what Archidekt counts.

    Archidekt's rule: a card in ANY excluded category (a cut pile, the
    Maybeboard) is out of the deck — even if it's also tagged with an included
    category like "Creature". Such a card becomes Maybeboard here (Sideboard
    when that's the excluded bucket it sits in): kept in the text so nothing
    is silently lost, but out of the maindeck count. Commander and Companion
    keep their own sections; everything else is Mainboard.
    """
    cats = entry.get("categories") if isinstance(entry, dict) else None
    names = (
        [c.strip() for c in cats if isinstance(c, str) and c.strip()]
        if isinstance(cats, list)
        else []
    )
    hits = [c.lower() for c in names if c.lower() in excluded]
    if hits:
        return "Sideboard" if "sideboard" in hits else "Maybeboard"
    for c in names:
        if c.lower() == "commander":
            return "Commander"
    for c in names:
        if c.lower() == "companion":
            return "Companion"
    return "Mainboard"


def _entry_name(entry) -> str:
    card = entry.get("card") if isinstance(entry, dict) else None
    if not isinstance(card, dict):
        return ""
    oracle = card.get("oracleCard") if isinstance(card.get("oracleCard"), dict) else None
    if oracle:
        name = (oracle.get("name") or "").strip()
        if name:
            return name
    return (card.get("name") or "").strip()


def import_deck(deck_id: str, *, timeout=None, fetcher=None) -> DeckImportResult:
    if not deck_id:
        return make_error(
            error_kind="invalid_url",
            message="That Archidekt URL didn't include a numeric deck id.",
            source=NAME,
        )

    fetch = fetcher or _default_fetch
    url = _API_TEMPLATE.format(deck_id=deck_id)
    fr = fetch(url, timeout=timeout, headers={"Accept": "application/json"})
    if not fr.ok:
        return make_error(
            error_kind=fr.error_kind or "http_error",
            message=fr.message or "Could not fetch the Archidekt deck.",
            source=NAME,
            deck_id=deck_id,
        )

    payload = fr.json()
    if not isinstance(payload, dict):
        return make_error(
            error_kind="bad_response",
            message="Archidekt returned a response we couldn't read as JSON.",
            source=NAME,
            deck_id=deck_id,
        )

    deck_name = (payload.get("name") or "").strip() or f"Archidekt deck {deck_id}"
    raw_cards = payload.get("cards") if isinstance(payload.get("cards"), list) else []
    excluded = _excluded_category_names(payload)

    cards: list[ImportedCard] = []
    commanders: list[str] = []
    for entry in raw_cards:
        if not isinstance(entry, dict):
            continue
        try:
            qty = int(entry.get("quantity", 1))
        except (TypeError, ValueError):
            qty = 1
        if qty <= 0:
            continue
        name = _entry_name(entry)
        if not name:
            continue
        section = _section_for(entry, excluded)
        cards.append(ImportedCard(name=name, quantity=qty, section=section))
        if section == "Commander":
            commanders.append(name)

    if not cards:
        return make_error(
            error_kind="empty_deck",
            message="Archidekt returned the deck but it contained no card entries.",
            source=NAME,
            deck_id=deck_id,
        )

    text = cards_to_decklist_text(cards)
    return DeckImportResult(
        ok=True,
        source=NAME,
        deck_id=deck_id,
        deck_name=deck_name,
        commander=commanders[0] if commanders else "",
        commanders=commanders,
        cards=cards,
        decklist_text=text,
        message=f"Imported {sum(c.quantity for c in cards)} cards from Archidekt.",
    )
