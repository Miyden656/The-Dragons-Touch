"""Typed result objects for the URL importer.

Same friendly-failure posture as ai/ollama_client.py: importer functions
never raise on offline/timeout/bad-response/parse-error. Every failure
becomes ok=False with a short user-facing message and a machine
error_kind so the UI can branch on it.
"""

from dataclasses import dataclass, field
from typing import Iterable


ERROR_KINDS = (
    "unsupported_site",   # URL was valid but no adapter handles that domain
    "invalid_url",        # URL was empty / unparseable / missing deck id
    "offline",             # Network unreachable
    "timeout",             # Request timed out
    "not_found",           # Site returned 404 for the deck
    "blocked",             # Site returned 401/403 — likely private deck or rate limit
    "http_error",          # Other HTTP failure
    "bad_response",        # Response wasn't the expected shape (JSON/text)
    "empty_deck",          # Fetched fine but no cards parsed
)


@dataclass(frozen=True)
class ImportedCard:
    """A single line of the normalized decklist."""
    name: str
    quantity: int
    section: str = "Mainboard"   # "Mainboard" | "Commander" | "Companion" | "Sideboard" | etc.


@dataclass
class DeckImportResult:
    """Outcome of an import attempt. Never raised — always returned."""
    ok: bool = False
    source: str = ""             # "moxfield" | "archidekt" | "mtggoldfish" | "" if unknown
    deck_id: str = ""
    deck_name: str = ""
    commander: str = ""           # First commander name if detected; "" otherwise
    commanders: list[str] = field(default_factory=list)  # All commander names (partner support)
    cards: list[ImportedCard] = field(default_factory=list)
    decklist_text: str = ""      # Normalized plain-text decklist (the deliverable)
    message: str = ""            # User-facing message (success or friendly error)
    error_kind: str = ""         # One of ERROR_KINDS when ok=False; "" on success
    source_url: str = ""         # Original URL passed in

    def card_count(self) -> int:
        return sum(c.quantity for c in self.cards)

    def mainboard_count(self) -> int:
        return sum(c.quantity for c in self.cards if c.section == "Mainboard")

    def to_summary(self) -> dict:
        """Lightweight summary safe for logs / status lines."""
        return {
            "ok": self.ok,
            "source": self.source,
            "deck_id": self.deck_id,
            "deck_name": self.deck_name,
            "commander": self.commander,
            "card_count": self.card_count(),
            "mainboard_count": self.mainboard_count(),
            "error_kind": self.error_kind,
            "message": self.message,
        }


def make_error(
    *,
    error_kind: str,
    message: str,
    source: str = "",
    source_url: str = "",
    deck_id: str = "",
) -> DeckImportResult:
    """Factory for the failure path so adapters stay terse."""
    return DeckImportResult(
        ok=False,
        source=source,
        deck_id=deck_id,
        error_kind=error_kind,
        message=message,
        source_url=source_url,
    )


def normalize_section(raw: str) -> str:
    """Map a site-specific bucket name to one of our canonical sections.

    Returns one of: Commander | Companion | Mainboard | Sideboard | Maybeboard | Tokens.
    Defaults to Mainboard for anything unknown — the engine parser will
    re-classify based on actual section headers in the rendered text.
    """
    if not raw:
        return "Mainboard"
    s = raw.strip().lower()
    if "commander" in s:
        return "Commander"
    if "companion" in s:
        return "Companion"
    if "sideboard" in s or "side" == s:
        return "Sideboard"
    if "maybe" in s:
        return "Maybeboard"
    if "token" in s:
        return "Tokens"
    return "Mainboard"


def cards_to_decklist_text(cards: Iterable[ImportedCard]) -> str:
    """Render imported cards as the same plain-text format the Paste tab consumes.

    Order: Commander section first (with `Commander` header), then Mainboard
    (no header — that's the default), then any non-mainboard sections with
    their headers. Each card is rendered as `<qty> <name>`. Quantities of 0
    are dropped; names are stripped.
    """
    by_section: dict[str, list[ImportedCard]] = {}
    for c in cards:
        if not c.name or c.quantity <= 0:
            continue
        section = c.section or "Mainboard"
        by_section.setdefault(section, []).append(
            ImportedCard(name=c.name.strip(), quantity=c.quantity, section=section)
        )

    # Stable per-section sort by name (case-insensitive) for predictable output.
    for section, items in by_section.items():
        items.sort(key=lambda c: c.name.lower())

    lines: list[str] = []

    def emit_section(header: str | None, section_key: str):
        items = by_section.get(section_key, [])
        if not items:
            return
        if header:
            if lines:
                lines.append("")
            lines.append(header)
        for c in items:
            lines.append(f"{c.quantity} {c.name}")

    # If a Commander block precedes the mainboard, emit a `Deck` header so the
    # engine parser exits the Commander section. With no Commander block,
    # mainboard goes header-less (matches the legacy paste-tab format).
    has_commander_block = bool(by_section.get("Commander"))
    emit_section("Commander", "Commander")
    emit_section("Deck" if has_commander_block else None, "Mainboard")
    emit_section("Companion", "Companion")
    emit_section("Sideboard", "Sideboard")
    emit_section("Maybeboard", "Maybeboard")
    emit_section("Tokens", "Tokens")

    # Catch-all for any unexpected section labels we didn't pre-declare.
    known = {"Commander", "Mainboard", "Companion", "Sideboard", "Maybeboard", "Tokens"}
    for section_key, items in by_section.items():
        if section_key in known:
            continue
        emit_section(section_key, section_key)

    return "\n".join(lines).strip() + ("\n" if lines else "")
