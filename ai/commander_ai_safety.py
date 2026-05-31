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

from ai.schemas.ai_context import CommanderAIContext

# claim kinds
OWNERSHIP_UNVERIFIED = "ownership_unverified"
BAN_UNVERIFIED = "ban_unverified"
COMBO_UNVERIFIED = "combo_unverified"

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

_STOPWORD_NAMES = {
    "the", "this", "that", "your", "you", "it", "if", "based", "use", "do", "don",
    "commander", "magic", "gathering", "edh", "and", "but", "or", "so", "because",
    "when", "while", "with", "without", "note", "also", "however", "here", "there",
    "i", "a", "an", "they", "them", "we", "in", "on", "for", "to", "of",
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
        flags.extend(_check_ban(sentence, banned))
        flags.extend(_check_combo(sentence, combo_available))

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


def _check_ban(sentence: str, banned: set[str]) -> list[FlaggedClaim]:
    m = _BAN_TRIGGER.search(sentence)
    if not m:
        return []
    # "X is banned" -> the card name precedes the trigger.
    out: list[FlaggedClaim] = []
    for name in _candidate_names(sentence[: m.start()]):
        if name.lower() in banned:
            continue
        out.append(
            FlaggedClaim(
                kind=BAN_UNVERIFIED,
                card=name,
                sentence=sentence.strip(),
                note=f"Ban status of \"{name}\" is not confirmed by the engine legality data.",
            )
        )
    return out


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
