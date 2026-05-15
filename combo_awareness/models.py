#!/usr/bin/env python3
"""v0.8.6.2.1-dev — dataclasses for combo awareness.

Scope guard: model split only; no behavior changes, no API calls, no app integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .normalization import clean_card_name, normalize_card_name

@dataclass
class DeckData:
    path: Path
    commander_names: list[str] = field(default_factory=list)
    main_card_names: list[str] = field(default_factory=list)

    @property
    def all_card_names(self) -> list[str]:
        return self.commander_names + self.main_card_names

    @property
    def normalized_all_cards(self) -> set[str]:
        return {normalize_card_name(name) for name in self.all_card_names if name.strip()}

    @property
    def normalized_commanders(self) -> set[str]:
        return {normalize_card_name(name) for name in self.commander_names if name.strip()}

@dataclass
class CollectionCard:
    name: str
    normalized_name: str
    source_file: str

@dataclass
class CollectionIndex:
    cards_by_normalized_name: dict[str, list[CollectionCard]] = field(default_factory=dict)

    def add(self, name: str, source_file: Path) -> None:
        clean_name = clean_card_name(name)
        if not clean_name:
            return
        normalized = normalize_card_name(clean_name)
        self.cards_by_normalized_name.setdefault(normalized, []).append(
            CollectionCard(
                name=clean_name,
                normalized_name=normalized,
                source_file=str(source_file),
            )
        )

    def find_sources(self, card_name: str) -> list[str]:
        normalized = normalize_card_name(card_name)
        entries = self.cards_by_normalized_name.get(normalized, [])
        seen: set[str] = set()
        sources: list[str] = []
        for entry in entries:
            if entry.source_file not in seen:
                seen.add(entry.source_file)
                sources.append(entry.source_file)
        return sources

@dataclass
class MatchResult:
    combo: dict[str, Any]
    missing_card_names: list[str]
    collection_sources_by_missing_card: dict[str, list[str]] = field(default_factory=dict)

@dataclass
class MatchSummary:
    complete_combos: list[MatchResult] = field(default_factory=list)
    one_card_away_combos: list[MatchResult] = field(default_factory=list)
    skipped_spoiler: int = 0
    skipped_color_identity: int = 0
    skipped_must_be_commander: int = 0
    skipped_unusable_shape: int = 0
    scanned_combos: int = 0

