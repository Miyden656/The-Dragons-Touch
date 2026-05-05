"""Commander legality validation helpers.

Round 4 cleanup goal:
- Move deck-size, color-identity, banned-card, and singleton checks out of the
  monolith.
- Preserve the v0.6.2.6 data shape as closely as possible so later cut/report
  modules can consume the same information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from deck_helper.data.card_lookup import (
    format_color_identity,
    get_duplicate_exception_limit,
    is_basic_land,
)
from deck_helper.legality.commander_detection import CommandZoneSummary
from deck_helper.parsing.deck_parser import ParsedDeck


@dataclass(slots=True)
class CommanderLegalitySummary:
    deck_card_count: int
    expected_deck_size: int = 100
    deck_size_legal: bool = False
    cards_not_found: list[str] = field(default_factory=list)
    color_identity_violations: list[dict[str, Any]] = field(default_factory=list)
    manual_review_color_identity: list[str] = field(default_factory=list)
    banned_cards: list[dict[str, Any]] = field(default_factory=list)
    banned_commanders: list[dict[str, Any]] = field(default_factory=list)
    manual_review_banned_cards: list[str] = field(default_factory=list)
    allowed_duplicate_cards: list[dict[str, Any]] = field(default_factory=list)
    illegal_duplicate_cards: list[dict[str, Any]] = field(default_factory=list)
    manual_review_duplicate_cards: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_color_identity_issues(self) -> bool:
        return bool(self.color_identity_violations or self.manual_review_color_identity)

    @property
    def has_banned_card_issues(self) -> bool:
        return bool(self.banned_cards or self.banned_commanders or self.manual_review_banned_cards)

    @property
    def has_duplicate_issues(self) -> bool:
        return bool(self.illegal_duplicate_cards or self.manual_review_duplicate_cards)

    @property
    def has_any_issues(self) -> bool:
        return (
            not self.deck_size_legal
            or self.has_color_identity_issues
            or self.has_banned_card_issues
            or self.has_duplicate_issues
        )


def find_cards_not_found(
    parsed_deck: ParsedDeck,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> list[str]:
    return [name for name in parsed_deck.unique_cards if name.lower() not in scryfall_lookup]


def check_color_identity(
    parsed_deck: ParsedDeck,
    command_zone: CommandZoneSummary,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    color_identity_violations: list[dict[str, Any]] = []
    manual_review_color_identity: list[str] = []

    for card_name, quantity in parsed_deck.unique_cards.items():
        card = scryfall_lookup.get(card_name.lower())
        if not card:
            manual_review_color_identity.append(card_name)
            continue
        if card_name in command_zone.commander_name_set:
            continue
        card_ci = set(card.get("color_identity", []))
        if not card_ci.issubset(command_zone.commander_color_identity_set):
            color_identity_violations.append({
                "card_name": card_name,
                "quantity": quantity,
                "card_color_identity": format_color_identity(card_ci),
                "commander_color_identity": command_zone.commander_color_identity_text,
            })

    return color_identity_violations, manual_review_color_identity


def check_banned_cards(
    parsed_deck: ParsedDeck,
    command_zone: CommandZoneSummary,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    banned_cards: list[dict[str, Any]] = []
    banned_commanders: list[dict[str, Any]] = []
    manual_review_banned_cards: list[str] = []

    for card_name, quantity in parsed_deck.unique_cards.items():
        card = scryfall_lookup.get(card_name.lower())
        if not card:
            manual_review_banned_cards.append(card_name)
            continue
        if card.get("legalities", {}).get("commander", "unknown") == "banned":
            entry = {"card_name": card_name, "quantity": quantity}
            if card_name in command_zone.commander_name_set:
                banned_commanders.append(entry)
            else:
                banned_cards.append(entry)

    return banned_cards, banned_commanders, manual_review_banned_cards


def check_duplicates(
    parsed_deck: ParsedDeck,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_duplicate_cards: list[dict[str, Any]] = []
    illegal_duplicate_cards: list[dict[str, Any]] = []
    manual_review_duplicate_cards: list[dict[str, Any]] = []

    for card_name, quantity in parsed_deck.unique_cards.items():
        if quantity <= 1:
            continue

        card = scryfall_lookup.get(card_name.lower())
        if not card:
            manual_review_duplicate_cards.append({
                "card_name": card_name,
                "quantity": quantity,
                "reason": "Card was not found in Scryfall, so duplicate legality needs manual review.",
            })
            continue

        limit = get_duplicate_exception_limit(card)
        if is_basic_land(card):
            allowed_duplicate_cards.append({
                "card_name": card_name,
                "quantity": quantity,
                "reason": "Basic land duplicates are allowed in Commander.",
            })
        elif limit == "unlimited":
            allowed_duplicate_cards.append({
                "card_name": card_name,
                "quantity": quantity,
                "reason": "Oracle text allows any number of cards with this name.",
            })
        elif isinstance(limit, int):
            if quantity <= limit:
                allowed_duplicate_cards.append({
                    "card_name": card_name,
                    "quantity": quantity,
                    "reason": f"Oracle text allows up to {limit} copies.",
                })
            else:
                illegal_duplicate_cards.append({
                    "card_name": card_name,
                    "quantity": quantity,
                    "reason": f"Oracle text allows up to {limit} copies, but this deck has {quantity}.",
                })
        else:
            illegal_duplicate_cards.append({
                "card_name": card_name,
                "quantity": quantity,
                "reason": "Commander singleton rule allows only one copy unless an exception applies.",
            })

    return allowed_duplicate_cards, illegal_duplicate_cards, manual_review_duplicate_cards


def build_commander_legality_summary(
    parsed_deck: ParsedDeck,
    command_zone: CommandZoneSummary,
    scryfall_lookup: dict[str, dict[str, Any]],
) -> CommanderLegalitySummary:
    cards_not_found = find_cards_not_found(parsed_deck, scryfall_lookup)
    color_identity_violations, manual_review_color_identity = check_color_identity(
        parsed_deck,
        command_zone,
        scryfall_lookup,
    )
    banned_cards, banned_commanders, manual_review_banned_cards = check_banned_cards(
        parsed_deck,
        command_zone,
        scryfall_lookup,
    )
    allowed_duplicate_cards, illegal_duplicate_cards, manual_review_duplicate_cards = check_duplicates(
        parsed_deck,
        scryfall_lookup,
    )

    return CommanderLegalitySummary(
        deck_card_count=parsed_deck.deck_card_count,
        deck_size_legal=parsed_deck.deck_card_count == 100,
        cards_not_found=cards_not_found,
        color_identity_violations=color_identity_violations,
        manual_review_color_identity=manual_review_color_identity,
        banned_cards=banned_cards,
        banned_commanders=banned_commanders,
        manual_review_banned_cards=manual_review_banned_cards,
        allowed_duplicate_cards=allowed_duplicate_cards,
        illegal_duplicate_cards=illegal_duplicate_cards,
        manual_review_duplicate_cards=manual_review_duplicate_cards,
    )


def format_legality_checkpoint_lines(
    command_zone: CommandZoneSummary,
    legality: CommanderLegalitySummary,
) -> list[str]:
    """Small terminal checkpoint formatter used before full reports are migrated."""
    lines = [
        "Round 4 legality checkpoint:",
        f"- Commander card(s): {command_zone.commander_name}",
        f"- Command zone rule detected: {command_zone.command_zone_rule_detected}",
        f"- Companion status: {command_zone.companion_note}",
        f"- Command zone cards found in Scryfall: {'Yes' if command_zone.commander_found else 'No'}",
        f"- Type line(s): {command_zone.commander_type_line}",
        f"- Combined color identity: {command_zone.commander_color_identity_text}",
        f"- Deck size: {'Legal' if legality.deck_size_legal else f'Not legal ({legality.deck_card_count} cards found; expected {legality.expected_deck_size})'}",
        f"- Cards not found in Scryfall: {len(legality.cards_not_found)}",
        f"- Color identity violations: {len(legality.color_identity_violations)}",
        f"- Banned cards/commanders: {len(legality.banned_cards) + len(legality.banned_commanders)}",
        f"- Illegal duplicate groups: {len(legality.illegal_duplicate_cards)}",
        f"- Manual duplicate reviews: {len(legality.manual_review_duplicate_cards)}",
    ]

    if command_zone.commander_cards_not_found:
        lines.append("- Commander cards not found: " + ", ".join(command_zone.commander_cards_not_found))
    if legality.color_identity_violations:
        lines.append("- Cards outside commander color identity:")
        for violation in legality.color_identity_violations[:10]:
            lines.append(
                f"  - {violation['card_name']} ({violation['card_color_identity']}) outside {violation['commander_color_identity']}"
            )
        if len(legality.color_identity_violations) > 10:
            lines.append(f"  - ...and {len(legality.color_identity_violations) - 10} more")
    if legality.illegal_duplicate_cards:
        lines.append("- Illegal duplicates:")
        for duplicate in legality.illegal_duplicate_cards[:10]:
            lines.append(f"  - {duplicate['card_name']}: {duplicate['quantity']} copies. {duplicate['reason']}")
        if len(legality.illegal_duplicate_cards) > 10:
            lines.append(f"  - ...and {len(legality.illegal_duplicate_cards) - 10} more")

    return lines
