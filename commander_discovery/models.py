"""Data models for Commander Discovery.

v1.2.2 refines commander candidate data so later CLI/report/UI surfaces can
show not only that a card was found, but why it was included and whether it is
an MVP-eligible commander or a future/manual-review special-rule candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .eligibility import CommanderEligibilityClassification, classify_commander_eligibility


_COLOR_ORDER = ["W", "U", "B", "R", "G"]
_COLOR_LABELS = {
    "": "Colorless",
    "W": "Mono-White",
    "U": "Mono-Blue",
    "B": "Mono-Black",
    "R": "Mono-Red",
    "G": "Mono-Green",
    "WU": "Azorius",
    "WB": "Orzhov",
    "WR": "Boros",
    "WG": "Selesnya",
    "UB": "Dimir",
    "UR": "Izzet",
    "UG": "Simic",
    "BR": "Rakdos",
    "BG": "Golgari",
    "RG": "Gruul",
    "WUB": "Esper",
    "WUR": "Jeskai",
    "WUG": "Bant",
    "WBR": "Mardu",
    "WBG": "Abzan",
    "WRG": "Naya",
    "UBR": "Grixis",
    "UBG": "Sultai",
    "URG": "Temur",
    "BRG": "Jund",
    "WUBR": "Four-Color W/U/B/R",
    "WUBG": "Four-Color W/U/B/G",
    "WURG": "Four-Color W/U/R/G",
    "WBRG": "Four-Color W/B/R/G",
    "UBRG": "Four-Color U/B/R/G",
    "WUBRG": "Five-Color",
}


def normalize_color_identity(color_identity: list[str] | tuple[str, ...] | set[str] | None) -> list[str]:
    """Return color identity in stable WUBRG order with extras appended."""
    if not color_identity:
        return []
    color_set = {str(color).upper() for color in color_identity if str(color).strip()}
    ordered = [color for color in _COLOR_ORDER if color in color_set]
    extras = sorted(color for color in color_set if color not in _COLOR_ORDER)
    return ordered + extras


def color_identity_key(color_identity: list[str] | tuple[str, ...] | set[str] | None) -> str:
    """Return compact WUBRG key used for grouping/filtering."""
    return "".join(normalize_color_identity(color_identity))


def format_color_identity_text(color_identity: list[str] | tuple[str, ...] | set[str] | None) -> str:
    """Return a stable Commander-facing color identity label."""
    normalized = normalize_color_identity(color_identity)
    return "/".join(normalized) if normalized else "Colorless"


def color_identity_group_label(color_identity: list[str] | tuple[str, ...] | set[str] | None) -> str:
    """Return a report-friendly color group label."""
    key = color_identity_key(color_identity)
    return _COLOR_LABELS.get(key, format_color_identity_text(color_identity))


@dataclass(slots=True)
class CommanderCandidate:
    """Structured commander candidate found from collection + Scryfall metadata."""

    card_name: str
    owned_quantity: int = 1
    color_identity: list[str] = field(default_factory=list)
    color_identity_text: str = "Colorless"
    color_identity_key: str = ""
    color_identity_group: str = "Colorless"
    color_count: int = 0
    mana_value: float | None = None
    type_line: str = ""
    oracle_text_preview: str = ""
    # Full, untruncated combined oracle text (incl. card faces). The preview
    # above stays 240-char for the text report; this feeds the UI detail panel
    # so the selected commander's complete rules text is always visible.
    full_oracle_text: str = ""
    source_files: list[str] = field(default_factory=list)
    commander_eligibility_reason: str = ""
    eligibility_status: str = "eligible"
    eligibility_rule: str = "basic_legendary_creature"
    special_commander_rule: str = ""
    manual_review_notes: list[str] = field(default_factory=list)
    is_mvp_eligible: bool = True
    is_special_rule_candidate: bool = False

    @classmethod
    def from_card(
        cls,
        card: dict[str, Any],
        *,
        owned_quantity: int = 1,
        source_files: list[str] | None = None,
        commander_eligibility_reason: str = "",
        special_commander_rule: str = "",
        manual_review_notes: list[str] | None = None,
        eligibility: CommanderEligibilityClassification | None = None,
    ) -> "CommanderCandidate":
        """Create a candidate from a Scryfall-like card dictionary."""
        classification = eligibility or classify_commander_eligibility(card)
        color_identity = normalize_color_identity(card.get("color_identity") or [])
        oracle_text = _combined_oracle_text_preview_source(card)
        preview = oracle_text[:240].rstrip()
        if len(oracle_text) > len(preview):
            preview = preview.rstrip() + "..."

        merged_manual_notes = list(manual_review_notes or [])
        for note in classification.manual_review_notes:
            if note and note not in merged_manual_notes:
                merged_manual_notes.append(note)

        special_rule = special_commander_rule or classification.special_rule_note
        reason = commander_eligibility_reason or classification.reason

        return cls(
            card_name=str(card.get("name") or "Unknown"),
            owned_quantity=max(int(owned_quantity or 0), 0),
            color_identity=color_identity,
            color_identity_text=format_color_identity_text(color_identity),
            color_identity_key=color_identity_key(color_identity),
            color_identity_group=color_identity_group_label(color_identity),
            color_count=len(color_identity),
            mana_value=_coerce_mana_value(card.get("cmc")),
            type_line=str(card.get("type_line") or ""),
            oracle_text_preview=preview,
            full_oracle_text=oracle_text,
            source_files=sorted(set(source_files or [])),
            commander_eligibility_reason=reason,
            eligibility_status=classification.status,
            eligibility_rule=classification.rule,
            special_commander_rule=special_rule,
            manual_review_notes=merged_manual_notes,
            is_mvp_eligible=classification.is_mvp_eligible,
            is_special_rule_candidate=classification.is_special_rule_candidate,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/report-friendly representation."""
        return {
            "card_name": self.card_name,
            "owned_quantity": self.owned_quantity,
            "color_identity": list(self.color_identity),
            "color_identity_text": self.color_identity_text,
            "color_identity_key": self.color_identity_key,
            "color_identity_group": self.color_identity_group,
            "color_count": self.color_count,
            "mana_value": self.mana_value,
            "type_line": self.type_line,
            "oracle_text_preview": self.oracle_text_preview,
            "full_oracle_text": self.full_oracle_text,
            "source_files": list(self.source_files),
            "commander_eligibility_reason": self.commander_eligibility_reason,
            "eligibility_status": self.eligibility_status,
            "eligibility_rule": self.eligibility_rule,
            "special_commander_rule": self.special_commander_rule,
            "manual_review_notes": list(self.manual_review_notes),
            "is_mvp_eligible": self.is_mvp_eligible,
            "is_special_rule_candidate": self.is_special_rule_candidate,
        }


@dataclass(slots=True)
class CommanderDiscoveryScanResult:
    """Summary returned by the collection commander-discovery scanner."""

    candidates: list[CommanderCandidate] = field(default_factory=list)
    total_collection_entries: int = 0
    unique_collection_cards: int = 0
    resolved_collection_cards: int = 0
    unresolved_collection_cards: int = 0
    skipped_nonlegendary_cards: int = 0
    # v1.6.1 Phase 2: number of cards that LOOK like commander candidates
    # (legendary creature or special command-zone text) but were excluded
    # because Scryfall marks them banned in Commander. Tracked separately from
    # skipped_nonlegendary_cards so the UI / report can surface "your collection
    # contains N banned commanders" instead of hiding it in the non-legendary
    # bucket.
    banned_commanders_skipped: int = 0
    # When True, the scan was run in custom / Rule Zero mode. Banned commanders
    # were surfaced as candidates with a BANNED warning instead of being dropped.
    allow_banned_commanders: bool = False
    manual_review_candidate_count: int = 0
    mvp_candidate_count: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def commander_candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def legendary_creature_candidates(self) -> list[CommanderCandidate]:
        """Compatibility alias for the explicit v1.2.1 scanner target."""
        return [candidate for candidate in self.candidates if candidate.is_mvp_eligible]

    @property
    def manual_review_candidates(self) -> list[CommanderCandidate]:
        """Candidates surfaced only because of deferred special commander rules."""
        return [candidate for candidate in self.candidates if candidate.eligibility_status == "manual_review"]

    def to_dict(self) -> dict[str, Any]:
        """Return a report/debug-friendly representation."""
        return {
            "commander_candidate_count": self.commander_candidate_count,
            "mvp_candidate_count": self.mvp_candidate_count,
            "manual_review_candidate_count": self.manual_review_candidate_count,
            "total_collection_entries": self.total_collection_entries,
            "unique_collection_cards": self.unique_collection_cards,
            "resolved_collection_cards": self.resolved_collection_cards,
            "unresolved_collection_cards": self.unresolved_collection_cards,
            "skipped_nonlegendary_cards": self.skipped_nonlegendary_cards,
            "banned_commanders_skipped": self.banned_commanders_skipped,
            "allow_banned_commanders": self.allow_banned_commanders,
            "warnings": list(self.warnings),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


def _coerce_mana_value(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _combined_oracle_text_preview_source(card: dict[str, Any]) -> str:
    parts: list[str] = []
    if card.get("oracle_text"):
        parts.append(str(card.get("oracle_text") or ""))
    for face in card.get("card_faces", []) or []:
        if not isinstance(face, dict):
            continue
        face_parts = [str(face.get(key) or "") for key in ("name", "oracle_text") if face.get(key)]
        if face_parts:
            parts.append(" — ".join(face_parts))
    return " ".join(" ".join(parts).replace("\n", " ").split())
