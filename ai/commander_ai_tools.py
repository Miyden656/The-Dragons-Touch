"""Verified card-fact tools (the grounding layer).

The north star for this AI layer is "knows every card and every format's
legality cold" — and the only honest way to deliver that on a small local model
is to GROUND it: the model never recites card facts from memory, it reads
verified facts these functions return from the local Scryfall data.

Everything here is deterministic and read-only. It does NOT call the engine and
does NOT call Ollama. It is the bridge between the ~30k-card Scryfall database
(source of truth for oracle text + per-format legality) and:

  1. the prompt assembler — inject a "VERIFIED CARD FACTS" block for any card
     the user asks about, so the model is handed the answer instead of guessing;
  2. the safety net — cross-check a model's "X is banned" claim against the
     card's REAL per-format legality.

Faces (MDFC / adventure / split / room) are handled via data.card_lookup so a
two-faced card reports a sensible mana value and full oracle text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from data.card_lookup import (
    format_color_identity,
    get_full_oracle_text,
    get_representative_nonland_mana_value,
)

# The four values Scryfall uses in a card's `legalities` map.
LEGAL = "legal"
NOT_LEGAL = "not_legal"
BANNED = "banned"
RESTRICTED = "restricted"
UNKNOWN = "unknown"

# Formats most relevant to this tool, ordered for display. Commander first
# because that is the deckbuilding format this app coaches; the rest let the
# guide answer "is X legal in <format>?" for any format Scryfall tracks.
FORMAT_DISPLAY_ORDER = [
    "commander",
    "oathbreaker",
    "paupercommander",
    "duel",
    "brawl",
    "standard",
    "pioneer",
    "modern",
    "legacy",
    "vintage",
    "pauper",
    "premodern",
    "predh",
    "oldschool",
    "penny",
    "historic",
    "timeless",
    "alchemy",
    "standardbrawl",
    "gladiator",
    "future",
    "tlr",
]

# Friendlier labels for the formats people actually ask about.
FORMAT_LABELS = {
    "commander": "Commander/EDH",
    "oathbreaker": "Oathbreaker",
    "paupercommander": "Pauper Commander",
    "duel": "Duel Commander",
    "brawl": "Brawl",
    "standard": "Standard",
    "pioneer": "Pioneer",
    "modern": "Modern",
    "legacy": "Legacy",
    "vintage": "Vintage",
    "pauper": "Pauper",
    "premodern": "Premodern",
    "predh": "Pre-EDH",
    "oldschool": "Old School",
    "penny": "Penny Dreadful",
    "historic": "Historic",
    "timeless": "Timeless",
    "alchemy": "Alchemy",
    "standardbrawl": "Standard Brawl",
    "gladiator": "Gladiator",
    "future": "Future Standard",
    "tlr": "TLR",
}

_LEGALITY_DISPLAY = {
    LEGAL: "legal",
    NOT_LEGAL: "not legal",
    BANNED: "BANNED",
    RESTRICTED: "restricted",
    UNKNOWN: "unknown",
}


@dataclass(frozen=True)
class CardFacts:
    """A verified snapshot of one card, straight from the Scryfall data."""

    name: str
    found: bool = False
    type_line: str = ""
    mana_cost: str = ""
    mana_value: float | None = None
    color_identity: str = ""
    oracle_text: str = ""
    keywords: tuple[str, ...] = ()
    game_changer: bool = False
    legalities: dict[str, str] = field(default_factory=dict)

    def legality(self, fmt: str) -> str:
        """Per-format status, normalized; UNKNOWN if the format isn't tracked."""
        return self.legalities.get(_norm_format(fmt), UNKNOWN)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "found": self.found,
            "type_line": self.type_line,
            "mana_cost": self.mana_cost,
            "mana_value": self.mana_value,
            "color_identity": self.color_identity,
            "oracle_text": self.oracle_text,
            "keywords": list(self.keywords),
            "game_changer": self.game_changer,
            "legalities": dict(self.legalities),
        }


def _norm_format(fmt: object) -> str:
    return str(fmt or "").strip().lower().replace(" ", "").replace("/", "").replace("-", "")


def lookup_card_facts(name: object, scryfall_lookup: dict | None) -> CardFacts | None:
    """Resolve one card to verified facts. Returns None if it isn't a real card.

    A None return is itself a grounding signal: "this name is not in the card
    database" — the caller can tell the model the card doesn't exist rather than
    letting it invent oracle text.
    """
    raw = str(name or "").strip()
    if not raw or not scryfall_lookup:
        return None
    card = scryfall_lookup.get(raw.lower())
    if not isinstance(card, dict):
        return None

    legalities = {
        str(k).lower(): str(v).lower()
        for k, v in (card.get("legalities") or {}).items()
    }
    keywords = tuple(str(k) for k in (card.get("keywords") or []) if k)
    return CardFacts(
        name=str(card.get("name", raw)),
        found=True,
        type_line=str(card.get("type_line", "")),
        mana_cost=str(card.get("mana_cost", "")),
        mana_value=get_representative_nonland_mana_value(card),
        color_identity=format_color_identity(card.get("color_identity")),
        oracle_text=get_full_oracle_text(card),
        keywords=keywords,
        game_changer=bool(card.get("game_changer", False)),
        legalities=legalities,
    )


def legality_in(name: object, fmt: object, scryfall_lookup: dict | None) -> str:
    """Status of `name` in `fmt`. UNKNOWN if card or format is unknown."""
    facts = lookup_card_facts(name, scryfall_lookup)
    if facts is None:
        return UNKNOWN
    return facts.legality(str(fmt))


def all_format_legality(name: object, scryfall_lookup: dict | None) -> dict[str, str]:
    """The full per-format legality table for a card ({} if not a real card)."""
    facts = lookup_card_facts(name, scryfall_lookup)
    return dict(facts.legalities) if facts else {}


def is_banned_in(name: object, fmt: object, scryfall_lookup: dict | None) -> bool | None:
    """True/False if known, None if the card or format can't be resolved.

    Used by the safety net: only a hard False (verified legal) makes a model's
    "X is banned" claim a fabrication; None means "can't confirm" (don't flag).
    """
    status = legality_in(name, fmt, scryfall_lookup)
    if status == UNKNOWN:
        return None
    return status == BANNED


# --- card-name extraction from free text ----------------------------------

# Title-case phrase shape. Card names are Title Case; this is the same rough
# shape the safety module uses, widened to allow commas/colons/apostrophes that
# show up in real card names ("Krenko, Mob Boss", "Jace, the Mind Sculptor").
_PHRASE = re.compile(r"[A-Z][\w'’]*(?:[ ,:'’-]+[A-Z0-9][\w'’]*)*")

# Words that begin sentences and look like names but rarely are; if a single
# one of these is the whole candidate, skip it. Multi-word candidates are kept.
_LEADING_STOPWORDS = {
    "the", "this", "that", "your", "you", "it", "if", "is", "are", "can", "could",
    "should", "would", "i", "we", "they", "in", "on", "for", "to", "of", "and",
    "but", "or", "so", "when", "while", "with", "without", "magic", "commander",
    "edh", "what", "which", "how", "why", "does", "do", "will", "here", "there",
    "also", "however", "note", "yes", "no", "format", "legal", "banned",
}


def find_known_card_names(
    text: object,
    scryfall_lookup: dict | None,
    *,
    limit: int = 8,
) -> list[str]:
    """Extract names from free text that are REAL cards in the Scryfall data.

    Bounded and cheap: we pull Title-Case candidate phrases out of the text and
    check each (and its leading sub-phrases, longest first) against the lookup.
    We never scan all ~30k names. Only confirmed cards are returned, in their
    canonical Scryfall casing, de-duplicated, capped at `limit`.
    """
    raw = str(text or "")
    if not raw or not scryfall_lookup:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for m in _PHRASE.finditer(raw):
        if len(out) >= limit:
            break
        words = m.group(0).split()
        n = len(words)
        # Greedy longest-match tokenizer over the phrase: at each start position
        # try the longest run first, then shorter. This skips a leading non-card
        # word ("Is Sol Ring" -> "Sol Ring") yet still prefers the longest real
        # name ("Mana Crypt" over "Mana").
        start = 0
        while start < n and len(out) < limit:
            matched = False
            for end in range(n, start, -1):
                candidate = " ".join(words[start:end]).strip(" ,:")
                low = candidate.lower()
                if not candidate:
                    continue
                if (end - start) == 1 and low in _LEADING_STOPWORDS:
                    continue
                card = scryfall_lookup.get(low)
                if isinstance(card, dict) and card.get("name"):
                    canonical = str(card["name"])
                    if canonical.lower() not in seen:
                        seen.add(canonical.lower())
                        out.append(canonical)
                    start = end
                    matched = True
                    break
            if not matched:
                start += 1
    return out


def resolve_facts_for_text(
    text: object,
    scryfall_lookup: dict | None,
    *,
    limit: int = 8,
    exclude: set[str] | None = None,
) -> list[CardFacts]:
    """Find real card names in text and return their verified facts.

    `exclude` (lower-cased names) skips cards already covered elsewhere in the
    prompt (e.g. the decklist) so we don't repeat facts the model already has.
    """
    exclude = {e.lower() for e in (exclude or set())}
    facts: list[CardFacts] = []
    for name in find_known_card_names(text, scryfall_lookup, limit=limit):
        if name.lower() in exclude:
            continue
        f = lookup_card_facts(name, scryfall_lookup)
        if f is not None:
            facts.append(f)
    return facts


# --- rendering -------------------------------------------------------------

def format_legality_line(facts: CardFacts, *, formats: list[str] | None = None) -> str:
    """One-line per-format legality summary for a card."""
    fmts = formats or FORMAT_DISPLAY_ORDER
    parts = []
    for fmt in fmts:
        status = facts.legalities.get(fmt)
        if not status:
            continue
        parts.append(f"{FORMAT_LABELS.get(fmt, fmt)}: {_LEGALITY_DISPLAY.get(status, status)}")
    return " · ".join(parts)


def render_card_facts(facts: CardFacts, *, max_oracle: int = 400) -> str:
    """A compact verified-facts block for a single card."""
    if not facts.found:
        return f'- "{facts.name}" — not found in the card database (treat as not a real card).'

    lines = [f"### {facts.name}"]
    meta = []
    if facts.type_line:
        meta.append(facts.type_line)
    if facts.mana_cost:
        meta.append(f"cost {facts.mana_cost}")
    if facts.mana_value is not None:
        meta.append(f"MV {facts.mana_value:g}")
    if facts.color_identity:
        meta.append(f"color identity {facts.color_identity}")
    if facts.game_changer:
        meta.append("Game Changer")
    if meta:
        lines.append(" · ".join(meta))

    oracle = facts.oracle_text.strip()
    if oracle:
        if len(oracle) > max_oracle:
            oracle = oracle[: max_oracle - 1].rstrip() + "…"
        lines.append(f"Oracle: {oracle}")

    legality = format_legality_line(facts)
    if legality:
        lines.append(f"Legality — {legality}")
    return "\n".join(lines)


def render_card_facts_block(facts_list: list[CardFacts]) -> str:
    """The full 'VERIFIED CARD FACTS' section for the user prompt.

    Empty list -> '' (the caller simply omits the section).
    """
    facts_list = [f for f in facts_list if f is not None]
    if not facts_list:
        return ""
    header = (
        "## Verified card facts (from the local Scryfall database — source of truth)\n"
        "Use these exact facts for the cards below. Do not contradict the legality "
        "or oracle text shown here; if a card a user names is not listed here, say you "
        "could not find it rather than guessing."
    )
    blocks = [render_card_facts(f) for f in facts_list]
    return header + "\n\n" + "\n\n".join(blocks)
