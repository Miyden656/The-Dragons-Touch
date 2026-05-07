"""Command-zone detection helpers.

Round 4 cleanup goal:
- Move commander/companion identification out of the monolith.
- Preserve v0.6.2.6 behavior for partner/background/companion notes.
- Return structured data that later report and strategy modules can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from data.card_lookup import format_color_identity, get_full_oracle_text, normalize_text
from parsing.deck_parser import ParsedDeck


@dataclass(slots=True)
class CommandZoneSummary:
    commander_names: list[str]
    companion_names: list[str]
    commander_name: str
    commander_name_set: set[str]
    commander_cards_scryfall: list[dict[str, Any]] = field(default_factory=list)
    commander_cards_not_found: list[str] = field(default_factory=list)
    commander_found: bool = False
    commander_type_line: str = "Unknown"
    commander_color_identity: list[str] = field(default_factory=list)
    commander_color_identity_text: str = "Unknown"
    commander_color_identity_set: set[str] = field(default_factory=set)
    command_zone_rule_detected: str = "Unknown / manual review"
    companion_note: str = "No companion detected. Companion legality check not applicable."


def detect_command_zone_rule(
    commander_cards_scryfall: list[dict[str, Any]],
    companion_names: list[str] | None = None,
) -> str:
    """Detect the command-zone construction rule from command-zone card text.

    This intentionally mirrors the legacy v0.6.2.6 heuristic. It is not a full
    comprehensive Commander rules engine; it provides report guidance and flags
    manual review when the structure is unusual.
    """
    companion_names = companion_names or []
    if companion_names:
        return "Companion present / companion legality not fully checked"

    if not commander_cards_scryfall:
        return "Unknown / manual review"

    texts = [
        normalize_text(get_full_oracle_text(card) + " " + card.get("type_line", ""))
        for card in commander_cards_scryfall
    ]
    joined = " ".join(texts)

    if len(commander_cards_scryfall) == 1:
        return "Single commander"

    if "doctor's companion" in joined or "doctor’s companion" in joined:
        return "Doctor's companion"
    if "friends forever" in joined:
        return "Friends forever"
    if "choose a background" in joined or "background" in joined:
        return "Background"
    if "partner with" in joined:
        return "Partner with"
    if "partner" in joined:
        return "Partner"

    return "Multiple command-zone cards / manual review"


def companion_legality_note(companion_names: list[str] | None) -> str:
    if companion_names:
        return "Companion detected. Companion legality is reported but not fully validated in v0.5.7."
    return "No companion detected. Companion legality check not applicable."


def build_command_zone_summary(
    parsed_deck: ParsedDeck,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> CommandZoneSummary:
    commander_cards_scryfall: list[dict[str, Any]] = []
    commander_cards_not_found: list[str] = []

    for name in parsed_deck.commander_names:
        card = scryfall_lookup.get(name.lower())
        if card:
            commander_cards_scryfall.append(card)
        else:
            commander_cards_not_found.append(name)

    commander_found = bool(parsed_deck.commander_names) and not commander_cards_not_found

    if commander_cards_scryfall:
        commander_type_line = " + ".join(
            f"{card.get('name', 'Unknown')}: {card.get('type_line', 'Unknown')}"
            for card in commander_cards_scryfall
        )
        order = ["W", "U", "B", "R", "G"]
        commander_color_identity = sorted(
            set().union(*(set(card.get("color_identity", [])) for card in commander_cards_scryfall)),
            key=lambda color: order.index(color) if color in order else 99,
        )
        commander_color_identity_text = format_color_identity(commander_color_identity)
    else:
        commander_type_line = "Unknown"
        commander_color_identity = []
        commander_color_identity_text = "Unknown"

    command_zone_rule_detected = detect_command_zone_rule(
        commander_cards_scryfall,
        parsed_deck.companion_names,
    )

    return CommandZoneSummary(
        commander_names=list(parsed_deck.commander_names),
        companion_names=list(parsed_deck.companion_names),
        commander_name=parsed_deck.commander_name,
        commander_name_set=set(parsed_deck.commander_names),
        commander_cards_scryfall=commander_cards_scryfall,
        commander_cards_not_found=commander_cards_not_found,
        commander_found=commander_found,
        commander_type_line=commander_type_line,
        commander_color_identity=commander_color_identity,
        commander_color_identity_text=commander_color_identity_text,
        commander_color_identity_set=set(commander_color_identity),
        command_zone_rule_detected=command_zone_rule_detected,
        companion_note=companion_legality_note(parsed_deck.companion_names),
    )
