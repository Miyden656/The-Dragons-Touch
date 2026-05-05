"""Local Scryfall database loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deck_helper.config import SCRYFALL_FILE
from deck_helper.data.card_lookup import build_scryfall_lookup


class ScryfallDataError(RuntimeError):
    """Raised when the local Scryfall data file cannot be loaded safely."""


def load_scryfall_cards(scryfall_file: Path | str = SCRYFALL_FILE) -> list[dict[str, Any]]:
    path = Path(scryfall_file)
    if not path.exists():
        raise ScryfallDataError(
            f"Could not find {path}. Run the Scryfall download/update script first."
        )

    try:
        cards = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScryfallDataError(f"Could not parse {path}: {exc}") from exc

    if not isinstance(cards, list):
        raise ScryfallDataError(f"Expected {path} to contain a JSON list of Scryfall card objects.")

    return cards


def load_scryfall_lookup(scryfall_file: Path | str = SCRYFALL_FILE) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    cards = load_scryfall_cards(scryfall_file)
    return cards, build_scryfall_lookup(cards)
