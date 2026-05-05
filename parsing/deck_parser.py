"""Decklist parser.

Round 3 cleanup goal:
- Move decklist parsing out of the monolith.
- Preserve v0.6.2.6 handling for sections, custom headers, companion/reference
  cards, ignored token/helper entries, and repeated card expansion.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from data.card_lookup import format_color_identity, normalize_text
from app_io.output_writer import make_safe_filename
from parsing.section_rules import (
    NON_MAINBOARD_SECTION_HEADERS,
    REFERENCE_ONLY_SECTION_HEADERS,
    SECTION_HEADERS,
    is_token_helper_section,
    section_is_non_mainboard,
    should_ignore_card_from_tokens_section,
)


@dataclass(slots=True)
class ParsedDeck:
    deck_file: Path
    cards: list[str] = field(default_factory=list)
    reference_cards: list[str] = field(default_factory=list)
    cards_by_section: dict[str, list[str]] = field(default_factory=dict)
    reference_cards_by_section: dict[str, list[str]] = field(default_factory=dict)
    card_manual_sections: dict[str, set[str]] = field(default_factory=dict)
    ignored_lines: list[str] = field(default_factory=list)
    input_hygiene_warnings: list[str] = field(default_factory=list)
    ignored_sections: Counter[str] = field(default_factory=Counter)
    commander_names: list[str] = field(default_factory=list)
    companion_names: list[str] = field(default_factory=list)
    commander_name: str = "Unknown_Commander"
    safe_commander_name: str = "Unknown_Commander"

    @property
    def unique_cards(self) -> Counter[str]:
        return Counter(self.cards)

    @property
    def deck_card_count(self) -> int:
        return len(self.cards)

    @property
    def reference_card_count(self) -> int:
        return len(self.reference_cards)


def _append_repeated(target: list[str], card_name: str, quantity: int) -> None:
    for _ in range(quantity):
        target.append(card_name)


def parse_quantity_card_line(line: str) -> tuple[int, str] | None:
    """Parse common decklist quantity lines like `1 Sol Ring`.

    This intentionally keeps the legacy parser's conservative behavior: only an
    integer followed by a space is accepted here. Collection parsing will support
    looser formats in a later round.
    """
    if not line or not line[0].isdigit():
        return None
    parts = line.split(" ", 1)
    if len(parts) != 2:
        return None
    quantity_text, card_name = parts[0], parts[1].strip()
    try:
        quantity = int(quantity_text)
    except ValueError:
        return None
    if quantity < 0 or not card_name:
        return None
    return quantity, card_name


def parse_deck_file(deck_file: Path | str, scryfall_lookup: dict[str, dict[str, Any]] | None = None) -> ParsedDeck:
    path = Path(deck_file)
    if not path.exists():
        raise FileNotFoundError(f"Could not find selected deck file: {path}")

    cards: list[str] = []
    reference_cards: list[str] = []
    cards_by_section: defaultdict[str, list[str]] = defaultdict(list)
    reference_cards_by_section: defaultdict[str, list[str]] = defaultdict(list)
    card_manual_sections: defaultdict[str, set[str]] = defaultdict(set)
    ignored_lines: list[str] = []
    input_hygiene_warnings: list[str] = []
    ignored_sections: Counter[str] = Counter()
    current_section = "Unknown / Needs Review"
    current_section_is_reference = False

    for original_line in path.read_text(encoding="utf-8").splitlines():
        line = original_line.strip()

        if not line:
            continue

        if line.startswith("#") or line.startswith("//"):
            continue

        lower_line = line.lower()

        if lower_line in NON_MAINBOARD_SECTION_HEADERS or lower_line in REFERENCE_ONLY_SECTION_HEADERS:
            current_section = f"Reference: {line}"
            current_section_is_reference = True
            ignored_sections[current_section] += 0
            continue

        if lower_line in SECTION_HEADERS:
            current_section = SECTION_HEADERS[lower_line]
            current_section_is_reference = section_is_non_mainboard(current_section)
            continue

        parsed = parse_quantity_card_line(line)
        if parsed is not None:
            quantity, card_name = parsed
            target_is_reference = current_section_is_reference or section_is_non_mainboard(current_section)

            # A section named "Tokens" is ambiguous. If it contains token/helper names,
            # ignore them as reference-only. Real card entries in this section continue
            # through the normal mainboard/reference decision.
            is_tokens_category = is_token_helper_section(current_section)
            if is_tokens_category and should_ignore_card_from_tokens_section(card_name, scryfall_lookup):
                reference_section = f"Reference: {current_section}"
                _append_repeated(reference_cards, card_name, quantity)
                for _ in range(quantity):
                    reference_cards_by_section[reference_section].append(card_name)
                ignored_sections[reference_section] += quantity
                continue

            if target_is_reference:
                _append_repeated(reference_cards, card_name, quantity)
                for _ in range(quantity):
                    reference_cards_by_section[current_section].append(card_name)
                ignored_sections[current_section] += quantity
                continue

            _append_repeated(cards, card_name, quantity)
            for _ in range(quantity):
                cards_by_section[current_section].append(card_name)
                card_manual_sections[card_name].add(current_section)
            continue

        if line[0].isdigit():
            ignored_lines.append(original_line)
            continue

        # Treat unknown non-card lines as custom/player-defined headers. Known
        # reference-only headers stay out of the real deck.
        normalized_header = normalize_text(line)
        if normalized_header in NON_MAINBOARD_SECTION_HEADERS or normalized_header in REFERENCE_ONLY_SECTION_HEADERS:
            current_section = f"Reference: {line}"
            current_section_is_reference = True
        else:
            current_section = f"Custom: {line}"
            current_section_is_reference = section_is_non_mainboard(current_section)

    commander_cards = cards_by_section.get("Commander", [])
    companion_cards = (
        cards_by_section.get("Companion", [])
        + reference_cards_by_section.get("Reference: Companion", [])
        + reference_cards_by_section.get("Reference: companion", [])
    )
    commander_names = list(dict.fromkeys(commander_cards))
    companion_names = list(dict.fromkeys(companion_cards))
    commander_name = " + ".join(commander_names) if commander_names else "Unknown_Commander"

    return ParsedDeck(
        deck_file=path,
        cards=cards,
        reference_cards=reference_cards,
        cards_by_section={key: list(value) for key, value in cards_by_section.items()},
        reference_cards_by_section={key: list(value) for key, value in reference_cards_by_section.items()},
        card_manual_sections={key: set(value) for key, value in card_manual_sections.items()},
        ignored_lines=ignored_lines,
        input_hygiene_warnings=input_hygiene_warnings,
        ignored_sections=ignored_sections,
        commander_names=commander_names,
        companion_names=companion_names,
        commander_name=commander_name,
        safe_commander_name=make_safe_filename(commander_name),
    )


@dataclass(slots=True)
class CommanderParseSummary:
    commander_cards_scryfall: list[dict[str, Any]]
    commander_cards_not_found: list[str]
    commander_found: bool
    commander_type_line: str
    commander_color_identity: list[str]
    commander_color_identity_text: str
    commander_color_identity_set: set[str]


def summarize_commander_from_parse(parsed_deck: ParsedDeck, scryfall_lookup: dict[str, dict[str, Any]]) -> CommanderParseSummary:
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

    return CommanderParseSummary(
        commander_cards_scryfall=commander_cards_scryfall,
        commander_cards_not_found=commander_cards_not_found,
        commander_found=commander_found,
        commander_type_line=commander_type_line,
        commander_color_identity=commander_color_identity,
        commander_color_identity_text=commander_color_identity_text,
        commander_color_identity_set=set(commander_color_identity),
    )
