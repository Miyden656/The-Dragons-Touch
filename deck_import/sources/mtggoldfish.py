"""MTGGoldfish adapter.

Public URL: https://www.mtggoldfish.com/deck/<deckId>

Endpoint strategy:
  1. Primary:  /deck/arena_download/<id>  — Arena-format export, which
     always emits explicit `Commander` / `Deck` / `Companion` / `Sideboard`
     headers for Commander decks and includes `(SET) ###` after each name
     (which we strip).
  2. Fallback: /deck/download/<id>  — flat plain text, no section headers
     for Commander decks in many cases. We use this only if the Arena
     fetch fails or returned an empty body; commander identification will
     be best-effort (single trailing block heuristic).

Arena example:
    Commander
    1 Atraxa, Praetors' Voice (CMR) 245

    Deck
    1 Sol Ring (CMR) 269
    1 Arcane Signet (ELD) 331
    ...
"""

import html
import re

from deck_import.http import fetch as _default_fetch
from deck_import.types import (
    DeckImportResult,
    ImportedCard,
    cards_to_decklist_text,
    make_error,
    normalize_section,
)


NAME = "mtggoldfish"
DOMAINS = ("mtggoldfish.com", "www.mtggoldfish.com")

_ARENA_TEMPLATE = "https://www.mtggoldfish.com/deck/arena_download/{deck_id}"
_DOWNLOAD_TEMPLATE = "https://www.mtggoldfish.com/deck/download/{deck_id}"

# Headers that move us BACK to the canonical mainboard section. Arena uses
# `Deck`; some exports use `Mainboard` / `Main Deck`.
_MAINBOARD_HEADERS = frozenset({"deck", "mainboard", "main deck", "main"})
_OTHER_HEADERS = frozenset({"commander", "commanders", "companion", "sideboard",
                            "maybeboard", "tokens"})

# Strip Arena-format trailing `(SET) ###` from card names. Set code is
# 2-6 alphanumerics; the collector number is alphanumeric (e.g. 245, 200a).
_ARENA_TAIL_RE = re.compile(r"\s*\(([A-Za-z0-9]{2,6})\)\s+\S+\s*$")


def extract_deck_id(parsed_url) -> str:
    parts = [p for p in parsed_url.path.split("/") if p]
    # /deck/<id> — sometimes followed by a slug; sometimes the id has a #paper anchor (stripped by urlparse).
    if len(parts) >= 2 and parts[0].lower() == "deck":
        candidate = parts[1].strip()
        if candidate and all(ch.isalnum() or ch in "-_" for ch in candidate):
            return candidate
    return ""


def _strip_arena_tail(name: str) -> str:
    """Remove the trailing `(SET) ###` block from an Arena-format card name."""
    cleaned = _ARENA_TAIL_RE.sub("", name).rstrip()
    return cleaned or name


def _clean_card_name(name: str) -> str:
    """Decode HTML entities and trim whitespace.

    MTGGoldfish's arena_download endpoint emits `&#39;` for apostrophes
    (and occasionally other entities for special characters), which the
    engine card parser sees as literal `&#39;` strings. Decode them so
    `Atraxa, Praetors&#39; Voice` -> `Atraxa, Praetors' Voice` etc.
    """
    return html.unescape(name).strip()


def _parse_text_export(text: str, *, format_hint: str = "auto") -> list[ImportedCard]:
    """Parse a plain-text deck export.

    `format_hint`:
      - "arena": trust section headers strictly, strip `(SET) ###` tails.
        Don't apply the single-trailing-card heuristic for Commander.
      - "plain": no headers expected for Commander; apply the single-trailing
        -card heuristic to identify the commander.
      - "auto": detect by presence of section headers in the body.

    Returns a list of ImportedCards (empty on failure).
    """
    if format_hint == "auto":
        lowered_lines = {ln.strip().lower() for ln in text.splitlines() if ln.strip()}
        format_hint = "arena" if (lowered_lines & (_MAINBOARD_HEADERS | _OTHER_HEADERS)) else "plain"

    is_arena = format_hint == "arena"

    cards: list[ImportedCard] = []
    section = "Mainboard"
    saw_blank_separator = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            saw_blank_separator = True
            continue
        if line.startswith("#") or line.startswith("//"):
            continue

        lower = line.lower()
        if lower in _MAINBOARD_HEADERS:
            section = "Mainboard"
            saw_blank_separator = False
            continue
        if lower in _OTHER_HEADERS:
            section = normalize_section(line)
            saw_blank_separator = False
            continue

        # Quantity + rest. MTGGoldfish text export is `1 Card Name [...]`.
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        qty_token, rest = parts[0], parts[1].strip()
        # Tolerate '1x Card Name'.
        if qty_token.lower().endswith("x"):
            qty_token = qty_token[:-1]
        try:
            qty = int(qty_token)
        except ValueError:
            continue
        if qty <= 0 or not rest:
            continue

        name = _strip_arena_tail(rest) if is_arena else rest
        name = _clean_card_name(name)
        if not name:
            continue

        effective_section = section
        if not is_arena and saw_blank_separator and section == "Mainboard":
            # In plain (non-Arena) format we assume the trailing block is
            # commander/sideboard; promote single-card trailing blocks below.
            effective_section = "Sideboard"

        cards.append(ImportedCard(name=name, quantity=qty, section=effective_section))

    if not is_arena:
        # Heuristic only used for plain exports: a 1-card trailing "Sideboard"
        # block is almost always the Commander in MTGGoldfish Commander decks.
        sideboard = [c for c in cards if c.section == "Sideboard"]
        if sideboard and sum(c.quantity for c in sideboard) == 1 and len(sideboard) == 1:
            cards = [
                ImportedCard(name=c.name, quantity=c.quantity, section="Commander")
                if c.section == "Sideboard" else c
                for c in cards
            ]

    return cards


def import_deck(deck_id: str, *, timeout=None, fetcher=None) -> DeckImportResult:
    if not deck_id:
        return make_error(
            error_kind="invalid_url",
            message="That MTGGoldfish URL didn't include a deck id.",
            source=NAME,
        )

    fetch = fetcher or _default_fetch

    # ---- Primary: Arena format (explicit Commander / Deck headers). ------
    arena_fr = fetch(
        _ARENA_TEMPLATE.format(deck_id=deck_id),
        timeout=timeout,
        headers={"Accept": "text/plain, */*"},
    )
    cards: list[ImportedCard] = []
    if arena_fr.ok and (arena_fr.text or "").strip():
        cards = _parse_text_export(arena_fr.text, format_hint="arena")

    # ---- Fallback: flat plain text (legacy behavior). --------------------
    if not cards:
        plain_fr = fetch(
            _DOWNLOAD_TEMPLATE.format(deck_id=deck_id),
            timeout=timeout,
            headers={"Accept": "text/plain, */*"},
        )
        if not plain_fr.ok:
            # Both endpoints failed — surface the more informative failure.
            primary_failure = arena_fr if not arena_fr.ok else plain_fr
            return make_error(
                error_kind=primary_failure.error_kind or "http_error",
                message=primary_failure.message or "Could not fetch the MTGGoldfish deck.",
                source=NAME,
                deck_id=deck_id,
            )
        cards = _parse_text_export(plain_fr.text or "", format_hint="auto")

    if not cards:
        return make_error(
            error_kind="empty_deck",
            message="MTGGoldfish returned the export but no card lines parsed.",
            source=NAME,
            deck_id=deck_id,
        )

    commanders = [c.name for c in cards if c.section == "Commander"]
    deck_name = f"MTGGoldfish deck {deck_id}"

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
        message=f"Imported {sum(c.quantity for c in cards)} cards from MTGGoldfish.",
    )
