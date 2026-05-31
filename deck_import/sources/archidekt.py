"""Archidekt adapter.

Public URL:  https://archidekt.com/decks/<deckId>[/<slug>]
Public API:  https://archidekt.com/api/decks/<deckId>/

Response shape (relevant subset):

    {
      "name": "...",
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

Archidekt models categories as user-defined buckets. We normalize the
ones that look like our canonical sections (Commander / Companion /
Sideboard / Maybeboard) and treat everything else as Mainboard, which
matches how the engine parses an exported text file.
"""

from deck_import.http import fetch as _default_fetch
from deck_import.types import (
    DeckImportResult,
    ImportedCard,
    cards_to_decklist_text,
    make_error,
    normalize_section,
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


def _categorize(entry) -> str:
    """Pick a canonical section name from an entry's `categories` list."""
    cats = entry.get("categories") if isinstance(entry, dict) else None
    if not isinstance(cats, list):
        return "Mainboard"
    # First commander/companion/sideboard/maybeboard match wins.
    priority = ("Commander", "Companion", "Sideboard", "Maybeboard", "Tokens")
    for want in priority:
        for c in cats:
            if isinstance(c, str) and c.strip().lower() == want.lower():
                return want
    # Anything else — including custom categories like "Ramp", "Removal" —
    # is mainboard from the engine's perspective.
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
        section = normalize_section(_categorize(entry))
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
