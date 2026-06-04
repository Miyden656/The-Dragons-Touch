"""Code-enforced hallucination guardrails.

The system prompt ASKS the model to behave. This module CHECKS that it did.
After a response comes back, verify_response() scans it for the three claim
types a Commander assistant most dangerously fabricates — collection ownership,
banned status, and combos — and cross-checks each against the engine-verified
context. Unverifiable claims are flagged and (in strict mode) a transparent
fact-check footer is appended. Prose is never silently rewritten.

This is what lets a small local model be trustworthy enough to ship: the floor
on correctness is enforced in code, not left to the model's goodwill.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ai.commander_ai_tools import (
    BANNED,
    LEGAL,
    NOT_LEGAL,
    RESTRICTED,
    UNKNOWN,
    find_known_card_names,
    legality_in,
    lookup_card_facts,
)
from ai.schemas.ai_context import CommanderAIContext

# claim kinds
OWNERSHIP_UNVERIFIED = "ownership_unverified"
BAN_UNVERIFIED = "ban_unverified"
BAN_CONTRADICTED = "ban_contradicted"
LEGALITY_CONTRADICTED = "legality_contradicted"
COMBO_UNVERIFIED = "combo_unverified"
CARD_NOT_FOUND = "card_not_found"

# Format names a model might cite in a ban claim -> Scryfall legality key.
_FORMAT_WORDS = {
    "commander": "commander", "edh": "commander",
    "oathbreaker": "oathbreaker",
    "duel commander": "duel", "duel": "duel",
    "brawl": "brawl",
    "standard": "standard",
    "pioneer": "pioneer",
    "modern": "modern",
    "legacy": "legacy",
    "vintage": "vintage",
    "pauper": "pauper",
    "premodern": "premodern",
    "historic": "historic",
    "timeless": "timeless",
    "alchemy": "alchemy",
    "penny": "penny",
}

# Structured legality statement: "<...> is [currently/now] <status> in <format>".
# We only act on the NON-banned statuses here ("banned" stays with _check_ban so
# the two checks never double-flag the same sentence). The card name is taken as
# the candidate name immediately preceding "is".
_LEGALITY_STATUS_WORDS = {
    "legal": LEGAL,
    "playable": LEGAL,
    "allowed": LEGAL,
    "restricted": RESTRICTED,
    "not legal": NOT_LEGAL,
    "illegal": NOT_LEGAL,
    "not allowed": NOT_LEGAL,
}
_LEGALITY_CLAIM = re.compile(
    r"\bis\s+(?:currently\s+|now\s+)?"
    r"(legal|playable|allowed|restricted|not\s+legal|illegal|not\s+allowed)\s+in\s+"
    r"(" + "|".join(sorted((re.escape(w) for w in _FORMAT_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_STATUS_DISPLAY = {LEGAL: "legal", NOT_LEGAL: "not legal", RESTRICTED: "restricted", BANNED: "banned"}

# Ownership claims come in two shapes:
#   - card AFTER the trigger:  "you own X", "you run X", "you've got X"
#   - card BEFORE the trigger: "X is in your collection"
# We extract the card name relative to the trigger so sentence-initial words
# ("Since you run Sol Ring...") are never mistaken for the claimed card.
_OWN_AFTER = re.compile(
    r"\byou (?:already )?(?:do )?(?:own|have|run|play)\b|\byou've got\b",
    re.IGNORECASE,
)
_OWN_BEFORE = re.compile(r"\bin your collection\b", re.IGNORECASE)
# Affirmative ban claim only — "is not banned" / "isn't banned" must NOT trigger.
_BAN_TRIGGER = re.compile(r"(?<!not )banned", re.IGNORECASE)
_COMBO_TRIGGER = re.compile(
    r"\b(infinite combo|combo line|combos? with|goes infinite|two-card combo|game-winning combo)\b",
    re.IGNORECASE,
)

# Title-case phrase (a rough card-name shape). Not perfect with comma names, but
# conservative: we only act when a claim trigger is also present.
_NAME = re.compile(r"[A-Z][a-zA-Z'’]+(?:[ -][A-Z][a-zA-Z'’]+)*")

# Invented-card detection (free-form modes). The model presents card suggestions
# in markdown emphasis or quotes (e.g. "swap it for *Sundering Blade*"). We only
# look inside emphasis/quotes AND only in a recommendation sentence, then flag a
# card-shaped phrase that resolves to NO real card — high precision, never touches
# plain prose or section headers.
_EMPHASIS = re.compile(
    r"\*\*(?P<b>[^*\n]+?)\*\*"     # **bold**
    r"|\*(?P<i>[^*\n]+?)\*"        # *italic*
    r"|“(?P<dq>[^”\n]+?)”"        # “smart quotes”
    r"|\"(?P<q>[^\"\n]+?)\""      # "straight quotes"
)
_SUGGEST_CUE = re.compile(
    r"\b(add|adds|adding|swap|swapping|replace|replacing|replaced|consider|"
    r"include|including|run|play|try|upgrade|slot in|instead of|such as|like|e\.?g\.?)\b",
    re.IGNORECASE,
)
# First-word discourse/header words that produce Title-Case phrases but are never cards.
_NON_CARD_LEAD = {
    "final", "key", "answer", "example", "note", "summary", "takeaway", "overall",
    "conclusion", "important", "remember", "trade", "trade-offs", "tradeoffs",
    "step", "tip", "tips", "pros", "cons", "verdict", "caveat", "reminder",
}
_CONNECTOR_TOKENS = {"of", "the", "and", "to", "in", "a", "an", "for", "on", "//", "the,"}
# Strategy/concept words the model bolds as labels ("Token Combat / Go-Wide", "Life
# Total Politics", "Mana Development") — these are NOT cards. Used ONLY to suppress a
# flag AFTER a phrase fails to resolve to a real card, so real cards that happen to
# contain such a word (e.g. "Mana Drain") are unaffected (they resolve first).
_CONCEPT_WORDS = {
    "combat", "politics", "value", "acceleration", "interaction", "engine", "setup",
    "development", "mana", "resource", "pressure", "ramp", "removal", "protection",
    "tempo", "advantage", "control", "aggro", "midrange", "synergy", "payoff", "wide",
    "tall", "tablewide", "table-wide", "go-wide", "go-tall", "recursion", "lifegain",
    "tokens", "token", "sacrifice", "stax", "wincon", "strategy", "strategies", "plan",
    "package", "subtheme", "theme", "archetype", "manabase", "fixing", "draw",
}
# Curly punctuation -> ascii, so a real card with a smart apostrophe/quote ("Ashnod's
# Transmogrant") resolves instead of being mis-flagged as invented.
_UNICODE_PUNCT = {"’": "'", "‘": "'", "ʼ": "'", "´": "'", "`": "'",
                  "“": '"', "”": '"', "„": '"', "–": "-", "—": "-"}


def _normalize_card_text(s: str) -> str:
    for a, b in _UNICODE_PUNCT.items():
        s = s.replace(a, b)
    return s


def _is_concept_phrase(phrase: str) -> bool:
    """A bolded strategy/concept LABEL (not a card): slash-joined, or contains a
    strategy word. Only consulted for phrases that already failed to resolve."""
    if " / " in phrase:
        return True
    return any(t.strip(",./-").lower() in _CONCEPT_WORDS for t in phrase.split())

_STOPWORD_NAMES = {
    "the", "this", "that", "your", "you", "it", "if", "based", "use", "do", "don",
    "commander", "magic", "gathering", "edh", "and", "but", "or", "so", "because",
    "when", "while", "with", "without", "note", "also", "however", "here", "there",
    "i", "a", "an", "they", "them", "we", "in", "on", "for", "to", "of",
    # Sentence-leading discourse words that get capitalized and mis-read as cards.
    "now", "given", "sure", "lastly", "overall", "additionally", "importantly",
    "first", "firstly", "second", "secondly", "third", "finally", "next", "then",
    "yes", "no", "let", "key", "honestly", "basically", "essentially", "remember",
    "consider", "instead", "since", "though", "although", "regarding", "addressing",
}


@dataclass(frozen=True)
class FlaggedClaim:
    kind: str
    card: str
    sentence: str
    note: str


@dataclass
class SafetyReport:
    ok: bool
    flags: list[FlaggedClaim] = field(default_factory=list)
    annotated_text: str = ""

    def kinds(self) -> set[str]:
        return {f.kind for f in self.flags}


def verify_response(
    text: str,
    context: CommanderAIContext | None,
    *,
    scryfall_lookup: dict | None = None,
    strict: bool = True,
) -> SafetyReport:
    """Check a model response against engine-verified context.

    strict=True appends a transparent fact-check footer when flags exist.
    Never raises; on bad input returns ok=True with the original text.
    """
    text = text or ""
    owned, deck, banned, combo_available = _verified_sets(context)

    flags: list[FlaggedClaim] = []
    for sentence in _sentences(text):
        flags.extend(_check_ownership(sentence, owned, deck))
        flags.extend(_check_ban(sentence, banned, scryfall_lookup))
        flags.extend(_check_legality_claim(sentence, scryfall_lookup))
        flags.extend(_check_combo(sentence, combo_available))
        flags.extend(_check_unverified_cards(sentence, scryfall_lookup))

    flags = _dedupe(flags)
    annotated = text
    if flags and strict:
        annotated = text.rstrip() + "\n\n" + _footer(flags)

    return SafetyReport(ok=not flags, flags=flags, annotated_text=annotated)


# --- claim checks ---------------------------------------------------------

def _check_ownership(sentence: str, owned: set[str], deck: set[str]) -> list[FlaggedClaim]:
    names: list[str] = []
    m_after = _OWN_AFTER.search(sentence)
    if m_after:
        names.extend(_candidate_names(sentence[m_after.end():]))
    m_before = _OWN_BEFORE.search(sentence)
    if m_before:
        names.extend(_candidate_names(sentence[: m_before.start()]))
    if not names:
        return []

    out: list[FlaggedClaim] = []
    for name in names:
        low = name.lower()
        if low in owned or low in deck:
            continue
        out.append(
            FlaggedClaim(
                kind=OWNERSHIP_UNVERIFIED,
                card=name,
                sentence=sentence.strip(),
                note=f"Ownership of \"{name}\" is not confirmed by the loaded collection data.",
            )
        )
    return out


def _check_ban(
    sentence: str, banned: set[str], scryfall_lookup: dict | None = None
) -> list[FlaggedClaim]:
    m = _BAN_TRIGGER.search(sentence)
    if not m:
        return []
    fmt = _detect_format(sentence)
    # "X is banned" -> the card name precedes the trigger.
    out: list[FlaggedClaim] = []
    for name in _candidate_names(sentence[: m.start()]):
        low = name.lower()
        # 1) Engine already lists it as banned for this deck -> verified, skip.
        if low in banned:
            continue
        # 2) Cross-check the real Scryfall per-format legality when we can.
        if scryfall_lookup:
            status = legality_in(name, fmt, scryfall_lookup)
            if status == BANNED:
                continue  # verified banned in this format — accurate claim
            if status != UNKNOWN:
                # Card is real and Scryfall says it is NOT banned here.
                out.append(
                    FlaggedClaim(
                        kind=BAN_CONTRADICTED,
                        card=name,
                        sentence=sentence.strip(),
                        note=(
                            f"Scryfall says \"{name}\" is {status.replace('_', ' ')} in "
                            f"{fmt}, not banned."
                        ),
                    )
                )
                continue
            # status == UNKNOWN with the Scryfall oracle present: the token isn't a
            # real card, so it is almost certainly a mis-extracted common word
            # (e.g. "Now, ... Sol Ring is banned"), NOT a real ban claim. Skip it
            # rather than emit a noisy "Ban status of 'Now' is not confirmed" flag.
            # Real wrong claims about real cards are still caught above (BAN_CONTRADICTED).
            continue
        # No Scryfall lookup available -> keep the legacy soft "unverified" flag.
        out.append(
            FlaggedClaim(
                kind=BAN_UNVERIFIED,
                card=name,
                sentence=sentence.strip(),
                note=f"Ban status of \"{name}\" is not confirmed by the legality data.",
            )
        )
    return out


def _check_legality_claim(sentence: str, scryfall_lookup: dict | None) -> list[FlaggedClaim]:
    """Verify a structured 'X is <legal|restricted|not legal> in <format>' claim
    against real Scryfall legality. Needs the lookup; 'banned' is left to
    _check_ban so the two never double-flag the same sentence."""
    if not scryfall_lookup:
        return []
    out: list[FlaggedClaim] = []
    for m in _LEGALITY_CLAIM.finditer(sentence):
        claimed = _LEGALITY_STATUS_WORDS.get(re.sub(r"\s+", " ", m.group(1).lower().strip()))
        fmt = _FORMAT_WORDS.get(m.group(2).lower())
        if not claimed or not fmt:
            continue
        names = _candidate_names(sentence[: m.start()])
        if not names:
            continue
        name = names[-1]  # the card named right before "is ..."
        actual = legality_in(name, fmt, scryfall_lookup)
        if actual == UNKNOWN or actual == claimed:
            continue  # unknown card -> don't guess; match -> accurate
        # A banned card is genuinely "not legal" to play, so a "not legal" claim
        # about a banned card is TRUE — don't flag it. (The dangerous direction,
        # e.g. calling a banned card "legal", is still flagged below.)
        if claimed == NOT_LEGAL and actual == BANNED:
            continue
        out.append(
            FlaggedClaim(
                kind=LEGALITY_CONTRADICTED,
                card=name,
                sentence=sentence.strip(),
                note=(
                    f"Scryfall says \"{name}\" is {_STATUS_DISPLAY.get(actual, actual)} in "
                    f"{fmt}, not {_STATUS_DISPLAY.get(claimed, claimed)}."
                ),
            )
        )
    return out


def _detect_format(sentence: str) -> str:
    """Which format a ban claim is about; defaults to commander (this app's focus)."""
    low = sentence.lower()
    # Check multi-word format names first so "duel commander" wins over "commander".
    for word in sorted(_FORMAT_WORDS, key=len, reverse=True):
        if word in low:
            return _FORMAT_WORDS[word]
    return "commander"


def _check_combo(sentence: str, combo_available: bool) -> list[FlaggedClaim]:
    if combo_available or not _COMBO_TRIGGER.search(sentence):
        return []
    return [
        FlaggedClaim(
            kind=COMBO_UNVERIFIED,
            card="",
            sentence=sentence.strip(),
            note="Combo awareness was not run for this deck, so this combo claim is unverified.",
        )
    ]


def _looks_like_card_name(phrase: str) -> bool:
    """A conservative 'this emphasized phrase is shaped like a card name' gate:
    multi-word, Title-Case, no digits/colons, not a section-header lead word."""
    p = phrase.strip()
    if not p or len(p) > 40 or ":" in p or any(ch.isdigit() for ch in p):
        return False
    tokens = p.split()
    if len(tokens) < 2:  # require multi-word — single emphasized words are usually prose (*great*)
        return False
    if tokens[0].strip(",.").lower() in _NON_CARD_LEAD:
        return False
    # At least two "real" tokens must be capitalized (connectors like of/the don't count).
    capitalized = sum(
        1 for t in tokens
        if t.lower() not in _CONNECTOR_TOKENS and t[:1].isupper()
    )
    return capitalized >= 2


def _check_unverified_cards(sentence: str, scryfall_lookup: dict | None) -> list[FlaggedClaim]:
    """Flag a card SUGGESTION that names no real card. Only fires inside markdown
    emphasis / quotes within a recommendation sentence, so plain prose and headers
    are never touched. Catches the free-form-mode failure where the model invents a
    plausible-sounding card (e.g. *Sundering Blade*) the rest of the net misses."""
    if not scryfall_lookup or not _SUGGEST_CUE.search(sentence):
        return []
    out: list[FlaggedClaim] = []
    seen: set[str] = set()
    for m in _EMPHASIS.finditer(sentence):
        phrase = next((g for g in m.groups() if g), "").strip(" *\"'“”.,;:")
        low = phrase.lower()
        if not phrase or low in seen or not _looks_like_card_name(phrase):
            continue
        seen.add(low)
        norm = _normalize_card_text(phrase)  # curly apostrophes/quotes -> ascii so real cards resolve
        try:
            real = (
                lookup_card_facts(norm, scryfall_lookup) is not None
                or bool(find_known_card_names(norm, scryfall_lookup))
            )
        except Exception:  # noqa: BLE001 - a lookup error must never produce a false flag
            real = True
        if real:
            continue
        # Didn't resolve — but a bolded strategy/concept label isn't an invented CARD.
        if _is_concept_phrase(phrase):
            continue
        out.append(
            FlaggedClaim(
                kind=CARD_NOT_FOUND,
                card=phrase,
                sentence=sentence.strip(),
                note=(
                    f"\"{phrase}\" doesn't match any real card in the local database — it may "
                    f"not exist. Verify it before adding it to the deck."
                ),
            )
        )
    return out


# --- helpers --------------------------------------------------------------

def _verified_sets(context: CommanderAIContext | None) -> tuple[set[str], set[str], set[str], bool]:
    if context is None:
        return set(), set(), set(), False

    deck = {str(c.get("name", "")).lower() for c in (context.decklist or []) if isinstance(c, dict)}
    deck.discard("")

    owned: set[str] = set()
    for c in (context.replacements or {}).get("collection_candidates", []) or []:
        if isinstance(c, dict) and c.get("card"):
            owned.add(str(c["card"]).lower())

    banned: set[str] = set()
    for key in ("banned_cards", "banned_commanders"):
        for n in (context.legality or {}).get(key, []) or []:
            banned.add(str(n).lower())

    combo_available = bool((context.combo or {}).get("available", False))
    return owned, deck, banned, combo_available


def _sentences(text: str) -> list[str]:
    # split on sentence punctuation and newlines; keep non-empty chunks
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [c for c in (chunk.strip() for chunk in chunks) if c]


def _candidate_names(sentence: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for m in _NAME.finditer(sentence):
        name = m.group(0).strip()
        low = name.lower()
        if low in _STOPWORD_NAMES or len(name) < 3:
            continue
        if low in seen:
            continue
        seen.add(low)
        out.append(name)
    return out


def _dedupe(flags: list[FlaggedClaim]) -> list[FlaggedClaim]:
    out: list[FlaggedClaim] = []
    seen: set[tuple[str, str]] = set()
    for f in flags:
        key = (f.kind, f.card.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def _footer(flags: list[FlaggedClaim]) -> str:
    lines = ["---", "⚠️ Fact-check notes (auto-checked against engine data):"]
    for f in flags:
        lines.append(f"- {f.note}")
    lines.append(
        "If any of these matter, ask me to verify against the local card database before relying on it."
    )
    return "\n".join(lines)
