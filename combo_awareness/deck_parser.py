#!/usr/bin/env python3
"""v0.8.6.2-dev — decklist parsing for combo awareness.

Scope guard: parser module split only; no parser behavior changes.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import DeckData
from .normalization import clean_card_name, normalize_card_name, normalize_header_text

# Keep quantity parsing explicit. The old loose pattern could turn "1xXorn" into "orn"
# by consuming the real card-name X as the optional quantity marker.
CARD_COUNT_PATTERNS = [
    re.compile(r"^\s*(?P<count>\d+)\s+x\s+(?P<name>.+?)\s*$", re.IGNORECASE),   # 1 x Sol Ring
    re.compile(r"^\s*(?P<count>\d+)x\s+(?P<name>.+?)\s*$", re.IGNORECASE),      # 1x Sol Ring
    re.compile(r"^\s*(?P<count>\d+)x(?P<name>[A-Z0-9].+?)\s*$"),                # 1xSol Ring / 1xXorn
    re.compile(r"^\s*(?P<count>\d+)\s+(?P<name>.+?)\s*$", re.IGNORECASE),      # 1 Sol Ring
]
MTGA_COUNT_RE = re.compile(r"^\s*(?P<count>\d+)\s+(?P<name>.+?)\s+\([A-Z0-9]+\)\s+\d+.*$", re.IGNORECASE)

COMMANDER_HEADERS = {
    "commander",
    "commanders",
    "commander zone",
    "command zone",
}

MAIN_DECK_HEADERS = {
    "deck",
    "mainboard",
    "main deck",
    "creatures",
    "creature",
    "instants",
    "instant",
    "sorceries",
    "sorcery",
    "artifacts",
    "artifact",
    "enchantments",
    "enchantment",
    "planeswalkers",
    "planeswalker",
    "lands",
    "land",
    "battle",
    "battles",
    "spells",
    "noncreature spells",
}

MAYBEBOARD_HEADERS = {
    "maybeboard",
    "maybe board",
    "maybe",
    "maybes",
    "maybe cards",
    "considering",
    "considerations",
    "considering cards",
    "cards to consider",
    "considered",
    "possible includes",
    "possible additions",
    "cards to add",
    "future adds",
    "future additions",
    "upgrades",
    "upgrade options",
    "potential upgrades",
    "wishlist",
    "wish list",
    "want list",
    "sideboard",
    "side board",
    "side deck",
}

TOKEN_HEADERS = {
    "tokens & extras",
    "tokens and extras",
    "token extras",
    "extras / tokens",
    "extras",
    "extra",
    "emblems",
    "emblem",
    "dungeons",
    "dungeon",
    "attractions",
    "attraction",
    "stickers",
    "sticker",
    "planechase",
    "planes",
    "schemes",
    "helper cards",
    "reminder cards",
}

# Deck-management sections are not part of the active deck by default.
# These are different from "Potential Cuts" / "Maybe Cuts", which the user
# treats as still-in-deck review buckets and therefore remain included.
DECK_MANAGEMENT_EXCLUDE_HEADERS = {
    "cut",
    "cuts",
    "cut cards",
    "cards cut",
    "cut section",
    "cut list",
    "cutlist",
    "removed",
    "removed cards",
    "removed from deck",
    "cards removed",
    "cards to remove",
    "cards i cut",
    "cards cut from deck",
    "made cut",
    "made cuts",
    "already cut",
    "already removed",
    "cuts made",
    "post first playtest cut",
    "post first playtest cuts",
    "post-first-playtest cut",
    "post-first-playtest cuts",
    "post playtest cut",
    "post playtest cuts",
    "first playtest cut",
    "first playtest cuts",
    "playtest cut",
    "playtest cuts",
    "after playtest cuts",
    "round 1 cuts",
    "round 2 cuts",
    "final cuts",
    "do not include",
    "not included",
    "rejected cards",
    "dead cards",
    "cards removed after testing",
    "testing pool",
    "test pool",
    "card pool",
    "pool",
    "package pool",
    "extra cards",
    "bench",
    "reserve",
    "reserved",
    "need",
    "needs",
    "need to buy",
    "buy",
    "buy list",
    "buylist",
    "shopping list",
    "purchase list",
    "order",
    "ordered",
    "incoming",
    "owned",
    "not owned",
    "missing",
    "missing cards",
    "notes",
    "note",
    "deck notes",
    "strategy notes",
    "play notes",
    "gameplan",
    "game plan",
    "how to win",
    "primer",
    "description",
    "explanation",
    "comments",
    "to do",
    "todo",
    "change log",
    "changelog",
    "updates",
    "version history",
    "testing notes",
    "playtest notes",
    "first playtest notes",
    "post game notes",
    "report",
    "ai prompt",
    "ai followup",
    "ai follow-up",
}


# Common package/category labels seen in Archidekt/Moxfield-style exports and
# custom Dragon's Touch test lists. These are section labels, not card names.
# They should not become commanders and should not inflate combo matching.
CUSTOM_CATEGORY_HEADERS = {
    "+1/+1",
    "+1/+1 counter",
    "+1/+1 counters",
    "alternate commander",
    "alternate commanders",
    "amass",
    "anthem",
    "anthems",
    "aristocrat",
    "aristocrats",
    "blink",
    "board wipe",
    "board wipes",
    "bomb",
    "bombs",
    "bottling",
    "burn",
    "card advantage",
    "card advantage/recursion",
    "card draw",
    "cheat out",
    "clones",
    "combat focus",
    "complete infinite combo",
    "complete infinite combos",
    "control",
    "copy",
    "copies",
    "cost reduction",
    "cost reduciton",  # preserved typo from a test deck heading
    "counterspell",
    "counterspells",
    "counters",
    "damage trigger copy",
    "damage/win con",
    "damage/win cons",
    "deck enabler",
    "deck enablers",
    "draw",
    "drain",
    "evasion",
    "finisher",
    "finishers",
    "flopsie",
    "interaction",
    "lock",
    "locks",
    "ramp",
    "recursion",
    "removal",
    "sacrifice",
    "self-mill",
    "stax",
    "theme",
    "toolbox",
    "token",
    "tokens",
    "token maker",
    "token makers",
    "token production",
    "token support",
    "token payoff",
    "token payoffs",
    "voltron",
    "win con",
    "win cons",
    "win condition",
    "win conditions",
    # Still-in-deck cut review buckets. These are intentionally included as
    # main-deck sections because the cards have not actually been removed yet.
    "potential cut",
    "potential cuts",
    "maybe cut",
    "maybe cuts",
    "possible cut",
    "possible cuts",
    "cut candidate",
    "cut candidates",
    "cards i might cut",
    "on the bubble",
    "flex slot",
    "flex slots",
    "flex card",
    "flex cards",
    "review for cuts",
}

NON_CARD_HEADERS = (
    COMMANDER_HEADERS
    | MAIN_DECK_HEADERS
    | MAYBEBOARD_HEADERS
    | TOKEN_HEADERS
    | DECK_MANAGEMENT_EXCLUDE_HEADERS
    | CUSTOM_CATEGORY_HEADERS
)

def is_known_non_card_header(text: str) -> bool:
    """Return True when a line is a known section/category label, not a card."""
    return normalize_header_text(text) in NON_CARD_HEADERS

def extract_card_name_from_line(line: str) -> tuple[int, str] | None:
    """Extract quantity and card name from a common decklist line."""
    line = line.strip()
    if not line:
        return None

    mtga_match = MTGA_COUNT_RE.match(line)
    if mtga_match:
        return int(mtga_match.group("count")), clean_card_name(mtga_match.group("name"))

    for count_pattern in CARD_COUNT_PATTERNS:
        count_match = count_pattern.match(line)
        if count_match:
            return int(count_match.group("count")), clean_card_name(count_match.group("name"))

    # Some exported commander sections may include a bare card name.
    # Do not allow known package/category headings to become fake cards.
    if not is_known_non_card_header(line):
        # Avoid treating obvious comments or separator lines as cards.
        if not line.startswith(("//", "#", "--", "==")):
            return 1, clean_card_name(line)

    return None

def parse_decklist(
    deck_path: Path,
    explicit_commanders: list[str] | None = None,
    *,
    include_maybeboard: bool = False,
    include_tokens: bool = False,
) -> DeckData:
    """Parse one plain-text decklist with loose support for common export formats.

    By default this parses only the real deck: commander plus main-deck sections.
    Maybeboard/sideboard/considering cards and token/extras sections are excluded
    because those are not cards actually present in the deck. Debug flags can opt
    them back in for verification only.

    v0.8.3.4 parser cleanup:
    - Commander sections stop after the first blank line following commander cards.
    - Common custom category headings are skipped instead of parsed as commanders/cards.
    - Cut/removed/post-playtest/card-pool/Made Cuts sections are excluded by default.
    - Plain Tokens/Token package headings remain included as real deck sections.
    - Tokens & Extras remains excluded as non-deck token objects.
    - Potential Cuts / Maybe Cuts style review sections remain included because
      those cards are still considered part of the current deck.
    """
    if not deck_path.exists():
        raise FileNotFoundError(f"Decklist not found: {deck_path}")

    data = DeckData(path=deck_path)
    current_section = "main"
    commander_section_seen_card = False

    for raw_line in deck_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            # In many exports, commander lines are followed by a blank before the
            # first custom package/category. Treat that blank as the end of the
            # commander section so package headings do not become commanders.
            if current_section == "commander" and commander_section_seen_card:
                current_section = "main"
            continue

        header = normalize_header_text(line)
        if header in COMMANDER_HEADERS:
            current_section = "commander"
            commander_section_seen_card = False
            continue
        if header in MAIN_DECK_HEADERS:
            current_section = "main"
            continue
        if header in MAYBEBOARD_HEADERS:
            current_section = "main" if include_maybeboard else "excluded"
            continue
        if header in TOKEN_HEADERS:
            current_section = "main" if include_tokens else "excluded"
            continue
        if header in DECK_MANAGEMENT_EXCLUDE_HEADERS:
            current_section = "excluded"
            continue
        if header in CUSTOM_CATEGORY_HEADERS:
            # Custom package/category labels are section headings. Keep parsing
            # following quantity lines as main deck cards, but never treat the
            # heading itself as a commander/card.
            if current_section == "commander":
                current_section = "main"
            continue

        if current_section == "excluded":
            continue

        parsed = extract_card_name_from_line(line)
        if not parsed:
            continue
        quantity, card_name = parsed
        if not card_name:
            continue

        if current_section == "commander":
            data.commander_names.append(card_name)
            commander_section_seen_card = True
        else:
            for _ in range(max(1, quantity)):
                data.main_card_names.append(card_name)

    if explicit_commanders:
        data.commander_names = [clean_card_name(name) for name in explicit_commanders if clean_card_name(name)]
        explicit_norms = {normalize_card_name(name) for name in data.commander_names}
        data.main_card_names = [
            name for name in data.main_card_names
            if normalize_card_name(name) not in explicit_norms
        ]

    return data

