"""Commander eligibility classification helpers for Commander Discovery.

v1.2.2 refines The Commander's Call data layer by separating:
- confirmed MVP commander candidates
- future/manual-review command-zone candidates
- non-candidates

This module is intentionally conservative. It does not validate legal partner
pairs, background pairs, Doctor's companion pairs, banned lists, color identity
rules for deck construction, or any full deck-building behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


ELIGIBILITY_STATUS_ELIGIBLE = "eligible"
ELIGIBILITY_STATUS_MANUAL_REVIEW = "manual_review"
ELIGIBILITY_STATUS_NOT_CANDIDATE = "not_candidate"

RULE_BASIC_LEGENDARY_CREATURE = "basic_legendary_creature"
RULE_SPECIAL_COMMANDER_TEXT = "special_commander_text"
RULE_DEFERRED_PAIRING_RULE = "deferred_pairing_rule"
RULE_NOT_A_COMMANDER_CANDIDATE = "not_a_commander_candidate"


@dataclass(slots=True)
class CommanderEligibilityClassification:
    """Conservative commander-discovery classification for one Scryfall card."""

    status: str = ELIGIBILITY_STATUS_NOT_CANDIDATE
    rule: str = RULE_NOT_A_COMMANDER_CANDIDATE
    reason: str = "Not a v1.2.2 commander discovery candidate."
    special_rule_note: str = ""
    manual_review_notes: list[str] = field(default_factory=list)
    is_mvp_eligible: bool = False
    is_special_rule_candidate: bool = False

    @property
    def include_in_discovery(self) -> bool:
        """Return True when the card should be surfaced to the v1.2 discovery layer."""
        return self.status in {ELIGIBILITY_STATUS_ELIGIBLE, ELIGIBILITY_STATUS_MANUAL_REVIEW}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rule": self.rule,
            "reason": self.reason,
            "special_rule_note": self.special_rule_note,
            "manual_review_notes": list(self.manual_review_notes),
            "is_mvp_eligible": self.is_mvp_eligible,
            "is_special_rule_candidate": self.is_special_rule_candidate,
            "include_in_discovery": self.include_in_discovery,
        }


def classify_commander_eligibility(card: dict[str, Any] | None) -> CommanderEligibilityClassification:
    """Classify commander-discovery eligibility without changing deck review behavior."""
    if not isinstance(card, dict):
        return CommanderEligibilityClassification(reason="No Scryfall card metadata was available.")

    special_note = get_special_commander_rule_note(card)
    manual_notes = [special_note] if special_note else []

    if is_basic_legendary_creature_candidate(card):
        return CommanderEligibilityClassification(
            status=ELIGIBILITY_STATUS_ELIGIBLE,
            rule=RULE_BASIC_LEGENDARY_CREATURE,
            reason="Scryfall type_line contains 'Legendary Creature'.",
            special_rule_note=special_note,
            manual_review_notes=manual_notes,
            is_mvp_eligible=True,
            is_special_rule_candidate=bool(special_note),
        )

    if special_note:
        rule = RULE_SPECIAL_COMMANDER_TEXT
        lowered = special_note.lower()
        if any(marker in lowered for marker in ("partner", "background", "companion", "friends forever")):
            rule = RULE_DEFERRED_PAIRING_RULE
        return CommanderEligibilityClassification(
            status=ELIGIBILITY_STATUS_MANUAL_REVIEW,
            rule=rule,
            reason="Manual review: special command-zone text may affect commander eligibility.",
            special_rule_note=special_note,
            manual_review_notes=manual_notes,
            is_mvp_eligible=False,
            is_special_rule_candidate=True,
        )

    return CommanderEligibilityClassification(
        status=ELIGIBILITY_STATUS_NOT_CANDIDATE,
        rule=RULE_NOT_A_COMMANDER_CANDIDATE,
        reason="Not a v1.2.2 commander discovery candidate.",
    )


def is_basic_legendary_creature_candidate(card: dict[str, Any] | None) -> bool:
    """Return True for the active v1.2 MVP commander candidate rule."""
    if not isinstance(card, dict):
        return False
    return any("Legendary Creature" in type_line for type_line in iter_type_lines(card))


def is_commander_discovery_candidate(card: dict[str, Any] | None) -> bool:
    """Return True when the card should be included in discovery results."""
    return classify_commander_eligibility(card).include_in_discovery


def get_commander_candidate_reason(card: dict[str, Any] | None) -> str:
    """Return the classification reason for a card."""
    return classify_commander_eligibility(card).reason


def get_special_commander_rule_note(card: dict[str, Any] | None) -> str:
    """Return cautious notes for special command-zone rules deferred past v1.2.2."""
    if not isinstance(card, dict):
        return ""

    text = normalize_rules_text(combined_oracle_text(card))
    type_text = normalize_rules_text(" ".join(iter_type_lines(card)))
    notes: list[str] = []

    if "can be your commander" in text:
        notes.append("Card text says it can be your commander; manual review until special commander rules are fully implemented.")
    if "partner with" in text:
        notes.append("Partner with detected; pair validation deferred.")
    elif "partner" in text:
        notes.append("Partner detected; pair validation deferred.")
    if "friends forever" in text:
        notes.append("Friends forever detected; pair validation deferred.")
    if "doctor's companion" in text or "doctors companion" in text:
        notes.append("Doctor's companion detected; pair validation deferred.")
    if "choose a background" in text:
        notes.append("Choose a Background detected; background pairing deferred.")
    if "background" in type_text:
        notes.append("Background type detected; background pairing deferred.")
    if "planeswalker" in type_text and "can be your commander" in text:
        notes.append("Planeswalker commander text detected; manual review deferred.")

    return " ".join(dict.fromkeys(notes))


def iter_type_lines(card: dict[str, Any]) -> Iterable[str]:
    """Yield root and face type lines from a Scryfall-like card object."""
    if card.get("type_line"):
        yield str(card.get("type_line") or "")
    for face in card.get("card_faces", []) or []:
        if isinstance(face, dict) and face.get("type_line"):
            yield str(face.get("type_line") or "")


def combined_oracle_text(card: dict[str, Any]) -> str:
    """Combine root and face text/type snippets for rules-text detection."""
    parts: list[str] = []
    if card.get("oracle_text"):
        parts.append(str(card.get("oracle_text") or ""))
    if card.get("type_line"):
        parts.append(str(card.get("type_line") or ""))
    for face in card.get("card_faces", []) or []:
        if isinstance(face, dict):
            for key in ("oracle_text", "type_line"):
                if face.get(key):
                    parts.append(str(face.get(key) or ""))
    return "\n".join(parts)


def normalize_rules_text(value: object) -> str:
    """Normalize card rules/type text for conservative phrase checks."""
    return " ".join(str(value or "").lower().replace("\n", " ").split())
