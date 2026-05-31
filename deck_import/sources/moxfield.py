"""Moxfield adapter.

Public URL: https://www.moxfield.com/decks/<deckId>
Public API: https://api2.moxfield.com/v3/decks/all/<deckId>

The v3 response shape (relevant subset):

    {
      "name": "...",
      "format": "commander",
      "boards": {
        "mainboard":   {"cards": {"<entryId>": {"quantity": N, "card": {"name": "..."}}}},
        "commanders":  {"cards": {...}},
        "companions":  {"cards": {...}},
        "sideboard":   {"cards": {...}},
        "maybeboard":  {"cards": {...}},
        "tokens":      {"cards": {...}}
      }
    }

We also tolerate the older v2 shape where `mainboard` / `commanders` / etc.
are flat keys at the root, in case Moxfield serves a fallback.
"""

from deck_import.http import fetch as _default_fetch
from deck_import.types import (
    DeckImportResult,
    ImportedCard,
    cards_to_decklist_text,
    make_error,
)


NAME = "moxfield"
DOMAINS = ("moxfield.com", "www.moxfield.com")

_API_TEMPLATE = "https://api2.moxfield.com/v3/decks/all/{deck_id}"

_SECTION_KEYS = (
    ("commanders", "Commander"),
    ("mainboard", "Mainboard"),
    ("companions", "Companion"),
    ("sideboard", "Sideboard"),
    ("maybeboard", "Maybeboard"),
    ("tokens", "Tokens"),
)


def extract_deck_id(parsed_url) -> str:
    parts = [p for p in parsed_url.path.split("/") if p]
    # /decks/<id> or /decks/<id>/<slug>
    if len(parts) >= 2 and parts[0].lower() == "decks":
        candidate = parts[1].strip()
        # Moxfield deck IDs are short alphanumeric tokens
        if candidate and all(ch.isalnum() or ch in "-_" for ch in candidate):
            return candidate
    return ""


def _iter_section_dict(section_obj) -> list[tuple[str, int]]:
    """Yield (card_name, quantity) from a Moxfield section dict.

    Tolerates the v3 nested `cards` map AND the v2-style direct map.
    Also accepts list payloads (some endpoints have served arrays).
    """
    out: list[tuple[str, int]] = []
    if section_obj is None:
        return out

    cards_obj = section_obj.get("cards") if isinstance(section_obj, dict) else None
    if cards_obj is None and isinstance(section_obj, dict):
        cards_obj = section_obj

    if isinstance(cards_obj, dict):
        entries = list(cards_obj.values())
    elif isinstance(cards_obj, list):
        entries = cards_obj
    else:
        return out

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        qty_raw = entry.get("quantity", entry.get("count", 1))
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            qty = 1
        if qty <= 0:
            continue
        card = entry.get("card") if isinstance(entry.get("card"), dict) else entry
        name = ""
        if isinstance(card, dict):
            name = (card.get("name") or "").strip()
        if not name:
            continue
        # Moxfield uses " // " for split/MDFC names — engine parser handles those.
        out.append((name, qty))
    return out


def _boards_root(payload) -> dict:
    if not isinstance(payload, dict):
        return {}
    boards = payload.get("boards")
    if isinstance(boards, dict):
        return boards
    # v2 fallback: section keys directly on the root.
    return payload


def import_deck(deck_id: str, *, timeout=None, fetcher=None) -> DeckImportResult:
    if not deck_id:
        return make_error(
            error_kind="invalid_url",
            message="That Moxfield URL didn't include a deck id.",
            source=NAME,
        )

    fetch = fetcher or _default_fetch
    url = _API_TEMPLATE.format(deck_id=deck_id)
    # Moxfield expects a referer-ish identity; the friendly UA is enough for personal use.
    fr = fetch(url, timeout=timeout, headers={"Accept": "application/json"})
    if not fr.ok:
        return make_error(
            error_kind=fr.error_kind or "http_error",
            message=fr.message or "Could not fetch the Moxfield deck.",
            source=NAME,
            deck_id=deck_id,
        )

    payload = fr.json()
    if not isinstance(payload, dict):
        return make_error(
            error_kind="bad_response",
            message="Moxfield returned a response we couldn't read as JSON.",
            source=NAME,
            deck_id=deck_id,
        )

    deck_name = (payload.get("name") or "").strip() or f"Moxfield deck {deck_id}"

    boards = _boards_root(payload)
    cards: list[ImportedCard] = []
    commanders: list[str] = []
    for key, section in _SECTION_KEYS:
        for name, qty in _iter_section_dict(boards.get(key)):
            cards.append(ImportedCard(name=name, quantity=qty, section=section))
            if section == "Commander":
                commanders.append(name)

    if not cards:
        return make_error(
            error_kind="empty_deck",
            message="Moxfield returned the deck but it contained no card entries.",
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
        message=f"Imported {sum(c.quantity for c in cards)} cards from Moxfield.",
    )
